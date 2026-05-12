
import json
import os
import sys
from pathlib import Path

import pandas as pd


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
QIPU_DIR = REPO_ROOT / 'qipu'

KILL_THRESHOLD = 9000

# 老 CSV 的向后兼容列
LEGACY_PV_COLS = [
    ('best_move1_fen', 'best_score1'),
    ('best_move2_fen', 'best_score2'),
    ('best_move3_fen', 'best_score3'),
]


def listCsv():
    if not QIPU_DIR.exists():
        return []
    return sorted(p for p in QIPU_DIR.iterdir() if p.suffix == '.csv' and p.is_file())


def sideOf(idx):
    return '红' if idx % 2 == 1 else '黑'


def killPvsOf(row):
    # 优先读新列 kill_moves_json
    blob = row.get('kill_moves_json') if 'kill_moves_json' in row.index else None
    if isinstance(blob, str) and blob.strip():
        try:
            parsed = json.loads(blob)
        except Exception:
            parsed = None
        if parsed:
            found = []
            for pv in parsed:
                score = int(pv['score'])
                if score < KILL_THRESHOLD:
                    continue
                moves = pv.get('moves') or []
                if not moves:
                    continue
                found.append({'moves': moves, 'score': score, 'col': 'kill_moves_json'})
            return found
    # fallback 老列
    found = []
    for fenCol, scoreCol in LEGACY_PV_COLS:
        sc = row.get(scoreCol)
        if pd.isna(sc) or sc < KILL_THRESHOLD:
            continue
        pv = row.get(fenCol)
        if not isinstance(pv, str) or not pv:
            continue
        moves = [m.strip() for m in pv.split(',') if m.strip()]
        if not moves:
            continue
        found.append({'moves': moves, 'score': int(sc), 'col': scoreCol})
    return found


def killFirstMovesOf(row):
    return [(pv['moves'][0], pv['score'], pv['col']) for pv in killPvsOf(row)]


def isMissed(row, killMoveSet):
    userMove = row.get('move_fen')
    if not isinstance(userMove, str) or not userMove:
        return True
    if userMove in killMoveSet:
        return False
    # 用户这步本身就是杀(score >= 9000),即便不在收录里也不算漏
    userScore = row.get('score')
    if not pd.isna(userScore) and userScore >= KILL_THRESHOLD:
        return False
    return True


def scanOne(csvPath):
    df = pd.read_csv(csvPath)
    rows = []
    for _, row in df.iterrows():
        kills = killFirstMovesOf(row)
        if not kills:
            continue
        killMoveSet = {k[0] for k in kills}
        primary = kills[0]
        missed = isMissed(row, killMoveSet)
        rows.append({
            'file': csvPath.name,
            'idx': int(row['idx']),
            'side': sideOf(int(row['idx'])),
            'fen': row['fen'],
            'userMove': row.get('move_fen') if isinstance(row.get('move_fen'), str) else '',
            'userScore': None if pd.isna(row.get('score')) else int(row.get('score')),
            'killMove': primary[0],
            'killScore': primary[1],
            'killPv': primary[2],
            'killMoveSet': sorted(killMoveSet),
            'missed': missed,
        })
    return rows


def sideOfFen(fen):
    # 靠局面推断轮到谁走:FEN 中红车为'R',黑车为'r'。
    # 这里 missKill 只拿到 fen 本身(没有 wOrB 字段),通过 rank 0 是否还有红大子推断不靠谱。
    # 退化方案:用 kill_moves 的首步首字符(UCI 起点格)上的棋子大小写判断。
    return None


def sideOfPvEntry(fen, move):
    # move 起点格的棋子大小写决定该步谁在走
    fx = ord(move[0]) - ord('a')
    fy = 9 - int(move[1])
    rows = fen.split('/')
    if fy < 0 or fy >= len(rows):
        return 'red'
    cells = []
    for ch in rows[fy]:
        if ch.isdigit():
            cells.extend([' '] * int(ch))
        else:
            cells.append(ch)
    if fx < 0 or fx >= len(cells):
        return 'red'
    ch = cells[fx]
    return 'red' if ch.isupper() else 'black'


def buildQuestionBank(includeMissedOnly=False):
    bank = []
    seenFen = set()
    # 第一轮:从 CSV 收集「实际棋谱」上的 kill 局面
    for p in listCsv():
        try:
            df = pd.read_csv(p)
        except Exception:
            continue
        for _, row in df.iterrows():
            pvs = killPvsOf(row)
            if not pvs:
                continue
            killMoveSet = {pv['moves'][0] for pv in pvs}
            missed = isMissed(row, killMoveSet)
            if includeMissedOnly and not missed:
                continue
            fen = row['fen']
            seenFen.add(fen)
            bank.append({
                'file': p.name,
                'idx': int(row['idx']),
                'side': 'red' if int(row['idx']) % 2 == 1 else 'black',
                'fen': fen,
                'pvs': pvs,
                'killMoveSet': sorted(killMoveSet),
                'missed': missed,
                'userMove': row.get('move_fen') if isinstance(row.get('move_fen'), str) else '',
                'source': 'csv',
            })
    # 第二轮:从 .pv.json 补充 PV 展开的中间局面
    if not QIPU_DIR.exists():
        return bank
    for pvPath in sorted(QIPU_DIR.glob('*.pv.json')):
        try:
            with open(pvPath, 'r', encoding='utf-8') as f:
                killMap = json.load(f)
        except Exception:
            continue
        for fen, entries in killMap.items():
            if fen in seenFen:
                continue
            if not entries:
                continue
            pvs = [
                {
                    'moves': e['remaining'],
                    'score': int(e['score']),
                    'col': 'pv.json',
                }
                for e in entries
            ]
            killMoveSet = {pv['moves'][0] for pv in pvs}
            # 展开局面的 "missed" 是没有意义的(没有用户真实走法),标 False
            missed = False
            if includeMissedOnly:
                continue
            side = sideOfPvEntry(fen, entries[0]['move'])
            bank.append({
                'file': pvPath.name,
                'idx': 0,
                'side': side,
                'fen': fen,
                'pvs': pvs,
                'killMoveSet': sorted(killMoveSet),
                'missed': missed,
                'userMove': '',
                'source': 'pv',
            })
            seenFen.add(fen)
    # 同一 FEN 可能在多盘棋谱中重复出现(开局套路、复盘重入)。
    # 保留规则:优先 missed=True,其次 killMoveSet 最大(解法更全)
    dedup = {}
    for q in bank:
        key = q['fen']
        prev = dedup.get(key)
        if prev is None:
            dedup[key] = q
            continue
        if q['missed'] and not prev['missed']:
            dedup[key] = q
        elif q['missed'] == prev['missed'] and len(q['killMoveSet']) > len(prev['killMoveSet']):
            dedup[key] = q
    return list(dedup.values())


def main():
    paths = listCsv()
    if not paths:
        print(f'[scan] {QIPU_DIR} \u4e2d\u6ca1\u6709 csv')
        return 1

    allRows = []
    for p in paths:
        try:
            rs = scanOne(p)
        except Exception as e:
            print(f'[scan] {p.name} \u5931\u8d25: {e}')
            continue
        allRows.extend(rs)
        killCount = len(rs)
        missCount = sum(1 for r in rs if r['missed'])
        print(f'[scan] {p.name}: \u6740\u5c40 {killCount} / \u6f0f\u6740 {missCount}')

    totalKill = len(allRows)
    totalMiss = sum(1 for r in allRows if r['missed'])
    print('=' * 48)
    print(f'\u5171\u626b {len(paths)} \u4e2a\u6587\u4ef6 | \u603b\u6740\u5c40 {totalKill} \u4e2a | \u603b\u6f0f\u6740 {totalMiss} \u4e2a')
    if totalKill:
        print(f'\u6f0f\u6740\u7387 {totalMiss*100/totalKill:.1f}%')

    if totalMiss == 0:
        return 0

    print()
    print('\u6f0f\u6740\u660e\u7ec6(\u6309\u6587\u4ef6+\u56de\u5408):')
    print('-' * 48)
    for r in allRows:
        if not r['missed']:
            continue
        us = 'None' if r['userScore'] is None else str(r['userScore'])
        killSet = ','.join(r['killMoveSet'])
        print(f"  {r['file']}  idx={r['idx']:>3}  {r['side']}  "
              f"\u4f60\u8d70={r['userMove'] or '-'}({us})  "
              f"\u6740\u624b\u96c6\u5408={killSet}")
        print(f"    fen: {r['fen']}")

    return 0


if __name__ == '__main__':
    sys.exit(main())
