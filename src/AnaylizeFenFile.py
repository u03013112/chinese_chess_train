# 分析Fen文件

# 读取Fen文件，找到我的行棋步骤（moves）
# 用PikafishHelper.go2() 找到最佳走法（多个）
# 根据最佳走法，对我的走法进行评价
# 设定阈值，如果差的程度超过阈值，就是我的走法不好
# 针对不好的走法，记录下来，并记录下来最佳走法（多个）

# CSV 列（向后兼容，仍保留 top3 列）
# 新增列:
#   kill_moves_json —— score>=KILL_THRESHOLD 的所有 PV 的 JSON 序列化。
#                      结构: [{"moves":[m1,m2,...],"score":9500}, ...]
# 同时生成同名 .pv.json 文件，记录每条 PV 沿途展开出的中间 FEN 的 killMove 映射。
# 结构: {
#   "<中间fen>": [{"move":"<uci>","score":9500,"remaining":[...]}, ...],
#   ...
# }
# remaining 是该中间局面之后 PV 剩余步序列（含当前这一步）。

import os
import csv
import json
from pikafishHelper import PikafishHelper
from tools import getMove, lastFenAndMove2Qp, applyMove

KILL_THRESHOLD = 9000


def expandPvIntoKillMap(rootFen, pv, killMap):
    # 沿 PV 每一步推导中间 fen，把每个中间 fen 到其下一步的映射写进 killMap
    fen = rootFen
    moves = pv['moves']
    score = int(pv['score'])
    for i, mv in enumerate(moves):
        remaining = moves[i:]
        entry = {'move': mv, 'score': score, 'remaining': remaining}
        killMap.setdefault(fen, []).append(entry)
        fen = applyMove(fen, mv)


def dedupeKillMap(killMap):
    # 同一 fen 被多条 PV 覆盖时，同 move 只保留最高 score 的那条（remaining 也跟随）
    out = {}
    for fen, entries in killMap.items():
        bestByMove = {}
        for e in entries:
            mv = e['move']
            cur = bestByMove.get(mv)
            if cur is None or e['score'] > cur['score']:
                bestByMove[mv] = e
        out[fen] = sorted(bestByMove.values(), key=lambda x: x['score'], reverse=True)
    return out


def analyzeFenFile(filename, output_csv, output_pv_json=None):
    if output_pv_json is None:
        output_pv_json = output_csv.replace('.csv', '.pv.json')
    with open(filename, 'r') as f:
        content = f.read().strip()
        lines = content.split('\n')
        moves = []
        pikafishHelper = PikafishHelper()
        results = []
        killMap = {}
        for i in range(len(lines) - 1):
            fen = lines[i]
            nextFen = lines[i + 1]
            p, move = getMove(fen, nextFen)
            response = pikafishHelper.go2(moves)
            moves.append(move)
            parsedResp = pikafishHelper.parseGoResponse(response)
            best_moves = parsedResp[0:3]

            # 找到用户走法在所有候选中的排名
            myRank = -1
            for idx, resp in enumerate(parsedResp):
                if resp['moves'][0] == move:
                    myRank = idx + 1
                    break

            # 收集所有 score>=KILL_THRESHOLD 的 PV
            killPvs = [pv for pv in parsedResp if int(pv['score']) >= KILL_THRESHOLD]
            killPvsJson = json.dumps(
                [{'moves': pv['moves'], 'score': int(pv['score'])} for pv in killPvs],
                ensure_ascii=False,
            )

            # 把每条 kill PV 沿途展开，写进 killMap（跨整个棋谱共享）
            for pv in killPvs:
                expandPvIntoKillMap(fen, pv, killMap)

            result = {
                'idx': i + 1,
                'fen': fen,
                'move_fen': move,
                'move_qp': lastFenAndMove2Qp(fen, move),
                'score': parsedResp[myRank - 1]['score'] if myRank != -1 else None,
                'kill_moves_json': killPvsJson,
            }
            for j, best_move in enumerate(best_moves, start=1):
                result[f'best_move{j}_fen'] = ','.join(best_move['moves'])
                result[f'best_move{j}_qp'] = ','.join([lastFenAndMove2Qp(fen, m) for m in best_move['moves']])
                result[f'best_score{j}'] = best_move['score']
            results.append(result)

        keys = [
            'idx', 'fen', 'move_fen', 'move_qp', 'score',
            'best_move1_fen', 'best_move1_qp', 'best_score1',
            'best_move2_fen', 'best_move2_qp', 'best_score2',
            'best_move3_fen', 'best_move3_qp', 'best_score3',
            'kill_moves_json',
        ]
        with open(output_csv, 'w', newline='') as output_file:
            dict_writer = csv.DictWriter(output_file, keys)
            dict_writer.writeheader()
            dict_writer.writerows(results)

        killMap = dedupeKillMap(killMap)
        with open(output_pv_json, 'w', encoding='utf-8') as fjson:
            json.dump(killMap, fjson, ensure_ascii=False, indent=2)


def main():
    path = '../qipu/'
    for file in os.listdir(path):
        if file.endswith('.txt'):
            csv_file = file.replace('.txt', '.csv')
            if os.path.exists(os.path.join(path, csv_file)):
                continue
            print(f'Analyzing {file}...')
            analyzeFenFile(os.path.join(path, file), os.path.join(path, csv_file))


if __name__ == '__main__':
    main()
