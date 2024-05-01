# 分析Fen文件

# 读取Fen文件，找到我的行棋步骤（moves）
# 用PikafishHelper.go2() 找到最佳走法（多个）
# 根据最佳走法，对我的走法进行评价
# 设定阈值，如果差的程度超过阈值，就是我的走法不好
# 针对不好的走法，记录下来，并记录下来最佳走法（多个）

# 初步格式定义
# csv文件
# 列1，fen string类型，类似于：rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR
# 列2，my_move string类型，类似于：'h2e2'
# 列3，my_score int类型，类似于：-100
# 列4，best_move1 string类型，类似于：'h2e2'
# 列5，best_score1 int类型，类似于：-100
# 列6，best_move2 string类型，类似于：'h2e2'
# 列7，best_score2 int类型，类似于：-100
# 列8，best_move3 string类型，类似于：'h2e2'
# 列9，best_score3 int类型，类似于：-100
# 额外的，可能可以加上是哪方走的，是红方还是黑方，方便之后过滤。
# 另外，可以将各种move都加一组中文注释，方便阅读。

import csv
from pikafishHelper import PikafishHelper
from tools import getMove, lastFenAndMove2Qp

def analyzeFenFile(filename, output_csv):
    with open(filename, 'r') as f:
        content = f.read()
        lines = content.split('\n')
        moves = []
        pikafishHelper = PikafishHelper()
        results = []
        for i in range(len(lines)-1):
            fen = lines[i]
            nextFen = lines[i+1]
            p,move = getMove(fen,nextFen)

            response = pikafishHelper.go2(moves)
            moves.append(move)
            # 找到最好的走法
            parsedResp = pikafishHelper.parseGoResponse(response)
            best_moves = parsedResp[0:3]  # 取前3个最佳走法

            # 找到我的走法，在所有的走法中的排名
            # 默认是最后一名，即所有答案以外的答案
            myRank = -1
            for idx,resp in enumerate(parsedResp):
                if resp['moves'][0] == move:
                    myRank = idx+1
                    break

            # 记录结果
            result = {
                'fen': fen,
                'my_move': lastFenAndMove2Qp(fen,move),
                'my_score': parsedResp[myRank-1]['score'] if myRank != -1 else None,
            }
            for i, best_move in enumerate(best_moves, start=1):
                result[f'best_move{i}'] = lastFenAndMove2Qp(fen,best_move['moves'][0])
                result[f'best_score{i}'] = best_move['score']
            results.append(result)

        # 保存到CSV文件
        keys = ['fen', 'my_move', 'my_score', 'best_move1', 'best_score1', 'best_move2', 'best_score2', 'best_move3', 'best_score3']
        with open(output_csv, 'w', newline='') as output_file:
            dict_writer = csv.DictWriter(output_file, keys)
            dict_writer.writeheader()
            dict_writer.writerows(results)


if __name__ == '__main__':
    analyzeFenFile('20240427230906.txt', 'output.csv')

