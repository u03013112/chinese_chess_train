from pikafishHelper import PikafishHelper
from tools import getMove,lastFenAndMove2Qp


def anaylizeFenFile(filename):
    with open(filename, 'r') as f:
        content = f.read()
        lines = content.split('\n')
        moves = []
        pikafishHelper = PikafishHelper()
        for i in range(len(lines)-1):
            fen = lines[i]
            nextFen = lines[i+1]
            p,move = getMove(fen,nextFen)
            # print(lastFenAndMove2Qp(fen,move))
            # wOrB = 'w' if i%2 == 0 else 'b'
            # response = pikafishHelper.go(fen, wOrB)
            response = pikafishHelper.go2(moves)
            moves.append(move)
            # 找到最好的走法
            parsedResp = pikafishHelper.parseGoResponse(response)
            print('推荐走法:', lastFenAndMove2Qp(fen,parsedResp[0]['moves'][0]))
            print('得分:', parsedResp[0]['score'])
            # 找到我的走法，在所有的走法中的排名
            # 默认是最后一名，即所有答案以外的答案
            myRank = -1
            print('我的走法:', lastFenAndMove2Qp(fen,move))
            # print('all moves:', [resp['moves'][0] for resp in parsedResp])
            # print(parsedResp)
            for idx,resp in enumerate(parsedResp):
                if resp['moves'][0] == move:
                    myRank = idx+1
                    break
            print('我的选择排名:', myRank)
            if myRank != -1:
                print('得分:', parsedResp[myRank-1]['score'])
            else:
                print('我的选择不在最佳走法中')
            print('-------------------')


if __name__ == '__main__':
    anaylizeFenFile('20240427230906.txt')
