from pikafishHelper import PikafishHelper
from tools import getMove,fenMove2Qp


def anaylizeFenFile(filename):
    with open(filename, 'r') as f:
        content = f.read()
        lines = content.split('\n')
    
        pikafishHelper = PikafishHelper()
        for i in range(len(lines)-1):
            fen = lines[i]
            nextFen = lines[i+1]
            p,move = getMove(fen,nextFen)
            print(fenMove2Qp(p,move))
            wOrB = 'w' if i%2 == 0 else 'b'
            response = pikafishHelper.go(fen, wOrB)
            # 找到最好的走法
            parsedResp = pikafishHelper.parseGoResponse(response)
            print('best move:', parsedResp[0]['moves'][0])
            print('score:', parsedResp[0]['score'])
            # 找到我的走法，在所有的走法中的排名
            # 默认是最后一名，即所有答案以外的答案
            myRank = len(parsedResp) + 1
            print('my move:', move)
            # print('all moves:', [resp['moves'][0] for resp in parsedResp])
            print(parsedResp)
            for idx,resp in enumerate(parsedResp):
                if resp['moves'][0] == move:
                    myRank = idx+1
                    break
            print('my rank:', myRank)

if __name__ == '__main__':
    anaylizeFenFile('20240427230906.txt')
