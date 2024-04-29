import time
from pikafish import Pikafish

class PikafishHelper:
    def __init__(self, depth=10):
        self.depth = depth
        self.pikafish = Pikafish()
        time.sleep(1)
        self.pikafish.sendCMD("uci")
        self.pikafish.sendCMD('setoption name MultiPV value 10')

    # wOrB: 'w' or 'b' 该谁走，w是红方，b是黑方
    def go(self, fen, wOrB):
        self.pikafish.sendCMD(f'position fen {fen} {wOrB} - - 10 10')
        
        response = self.pikafish.sendCMDSync(f'go depth {self.depth}',needResponse=True)
        return response
    
    def parseGoResponse(self, response):
        lines = response.split('\n')
        
        # 找到以 'info depth {self.depth}' 开头的行
        ret = []
        for line in lines:
            if line.startswith(f'info depth {self.depth}'):
                score = line.split(' ')[9]
                moves = line.split(' pv ')[1].split(' ')
                ret.append({'score': score, 'moves': moves})

        # 按照分数排序
        ret.sort(key=lambda x: x['score'], reverse=True)
        return ret

    


if __name__ == '__main__':
    pikafishHelper = PikafishHelper()
    response = pikafishHelper.go('rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR', 'w')
    print(response)
    print(pikafishHelper.parseGoResponse(response))


        
                
        