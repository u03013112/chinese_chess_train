import time
import platform
from pikafish import Pikafish

class PikafishHelper:
    def __init__(self, depth=10):
        self.depth = depth
        
        current_os = platform.system()
        if current_os == 'Darwin':
            # 安装参照文档：
            # https://github.com/official-pikafish/Pikafish/wiki/Compiling-from-source#macos
            self.pikafish = Pikafish('/Users/u03013112/Documents/git/Pikafish/src/pikafish')
        elif current_os == 'Linux':    
            self.pikafish = Pikafish()
        else:
            print('Unsupported OS')
            exit(1)
        time.sleep(1)
        self.pikafish.sendCMD("uci")
        self.pikafish.sendCMD("setoption name Threads value 8")
        self.pikafish.sendCMD('setoption name MultiPV value 20')

    # wOrB: 'w' or 'b' 该谁走，w是红方，b是黑方
    def go(self, fen, wOrB):
        self.pikafish.sendCMD(f'position fen {fen} {wOrB} - - 10 10')
        
        response = self.pikafish.sendCMDSync(f'go depth {self.depth}',needResponse=True)
        return response
    
    def go2(self,moves):
        if len(moves) == 0:
            cmd = 'position startpos'
        else:
            cmd = 'position startpos moves '+ ' '.join(moves)
        self.pikafish.sendCMD(cmd)
        response = self.pikafish.sendCMDSync(f'go depth {self.depth}',needResponse=True)
        return response
        
    def parseGoResponse(self, response,logPath = None):
        # print('response:',response)
        lines = response.split('\n')
        
        # 找到以 'info depth {self.depth}' 开头的行
        ret = []
        log = []
        for line in lines:
            if line.startswith(f'info depth {self.depth}'):
                isMate = line.split(' ')[8] == 'mate'
                if isMate:
                    # 死棋的情况，后面的数字代表步数，步数越少，分数越高
                    mateStepCount = int(line.split(' ')[9])
                    # 粗略的估算
                    if mateStepCount > 0:
                        score = 10000 - mateStepCount*100
                    else:
                        score = -10000 - mateStepCount*100
                else: 
                    score = line.split(' ')[9]

                moves = line.split(' pv ')[1].split(' ')
                ret.append({'score': score, 'moves': moves})
                if logPath:
                    log.append({'line':line,'score':score,'moves':moves})

        # 按照分数排序
        ret.sort(key=lambda x: int(x['score']), reverse=True)

        if logPath:
            with open(logPath,'w') as f:
                for l in log:
                    f.write(l['line']+'\n')
                    f.write(f'score: {l["score"]}\n')
                    f.write(f'moves: {l["moves"]}\n')
                    f.write('-------------------\n')
        return ret

    


if __name__ == '__main__':
    pikafishHelper = PikafishHelper()
    # response = pikafishHelper.go('rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR', 'w')
    response = pikafishHelper.go2(['h2e2','h9i7','e2e6','i9h9','b2b4','c6c5'])
    # response = pikafishHelper.go2(['h2e2','h9i7','e2e6','i9h9','b2b4','c6c5','b4e4'])
    print(response)
    print(pikafishHelper.parseGoResponse(response))


        
                
        