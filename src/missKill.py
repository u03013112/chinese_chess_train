
import os
import sys
from pathlib import Path

import pandas as pd


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
QIPU_DIR = REPO_ROOT / 'qipu'

KILL_THRESHOLD = 9000
PV_COLS = [
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


def killFirstMovesOf(row):
    found = []
    for fenCol, scoreCol in PV_COLS:
        sc = row.get(scoreCol)
        if pd.isna(sc) or sc <= KILL_THRESHOLD:
            continue
        pv = row.get(fenCol)
        if not isinstance(pv, str) or not pv:
            continue
        first = pv.split(',')[0].strip()
        found.append((first, int(sc), scoreCol))
    return found


def isMissed(row, killMoveSet):
    userMove = row.get('move_fen')
    if not isinstance(userMove, str) or not userMove:
        return True
    if userMove in killMoveSet:
        return False
    # 用户这步本身就是杀(score > 9000),即便不在 top3 PV 里也不算漏
    userScore = row.get('score')
    if not pd.isna(userScore) and userScore > KILL_THRESHOLD:
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
