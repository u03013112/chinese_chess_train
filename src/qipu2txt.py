
# 将 qipu/raw/*.json(天天象棋抓取的结构化棋谱)转成 qipu/<name>.txt(每行一个 FEN,兼容 AnaylizeFenFile.py)
#
# 支持两种 JSON 格式:
#
# 【老格式】(早期图像识别 + 人工清洗产物,如 qipu/raw_legacy/74600159056.old.json)
#   startFen:      起始 FEN(标准开局)
#   moves:         [[fx, fy, tx, ty], ...],坐标系与 tools.getMove 一致
#                  fx/fy: 起点列(0-8)/行(0-9,顶部=0)
#                  tx/ty: 终点列/行
#
# 【新格式】(Playwright 从 H5 版天天象棋 fdk.getModel('QipuModel') hook 抓取)
#   sData:         JSON 字符串,解包后取:
#                    sData.moveinfo.binit    起始棋子布局串(标准开局 == "8979...6383")
#                    sData.moveinfo.movelist 压缩 move 串,每 4 字符 1 步: fx fy tx ty
#                                            坐标系与老格式完全一致(已核对)
#                    sData.userinfo          红黑方信息(参考用)
#                    sData.result / classinfo.sevent 结果/赛事类型(参考用)
#   qipuId/playersInfo/t 等字段仅作元数据
#
# 输出 txt 格式(统一):
#   第 1 行:       起始 FEN
#   第 2 行:       走第 1 步之后的 FEN
#   ...
#   第 N+1 行:     走第 N 步之后的 FEN

import os
import json

# 天天象棋 H5 记录的"标准开局" binit 串(每 2 字符 1 个棋子的 xy,共 32 个棋子)
STANDARD_BINIT = '8979695949392919097717866646260600102030405060708012720323436383'
# 标准开局 FEN(与 tools.py testGetMove 中的 fen1 一致;大写=黑,小写=红,行顶部到底部)
STANDARD_START_FEN = 'rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR'


def expandFen(fen):
    # 将 FEN 展开为长度 90 的列表,空格字符表示空位
    rows = fen.split('/')
    if len(rows) != 10:
        raise ValueError(f"FEN 行数不是 10: {fen}")
    board = []
    for row in rows:
        rowCells = []
        for ch in row:
            if ch.isdigit():
                rowCells.extend([' '] * int(ch))
            else:
                rowCells.append(ch)
        if len(rowCells) != 9:
            raise ValueError(f"FEN 行宽不是 9: row={row} len={len(rowCells)}")
        board.extend(rowCells)
    return board


def compressFen(board):
    # 将长度 90 的 board 列表压回 FEN 字符串
    if len(board) != 90:
        raise ValueError(f"board 长度不是 90: {len(board)}")
    rows = []
    for r in range(10):
        rowCells = board[r * 9:(r + 1) * 9]
        s = ''
        empty = 0
        for c in rowCells:
            if c == ' ':
                empty += 1
            else:
                if empty > 0:
                    s += str(empty)
                    empty = 0
                s += c
        if empty > 0:
            s += str(empty)
        rows.append(s)
    return '/'.join(rows)


def applyMoveToFen(fen, fx, fy, tx, ty):
    # 在 fen 上应用一步走棋 (fx,fy) -> (tx,ty),返回新 FEN
    # 坐标系:fy=0 是 FEN 第一行(顶部黑方),fy=9 是最后一行(底部红方);fx=0 是最左列(a)
    if not (0 <= fx <= 8 and 0 <= tx <= 8 and 0 <= fy <= 9 and 0 <= ty <= 9):
        raise ValueError(f"坐标越界: ({fx},{fy}) -> ({tx},{ty})")
    board = expandFen(fen)
    fromIdx = fy * 9 + fx
    toIdx = ty * 9 + tx
    piece = board[fromIdx]
    if piece == ' ':
        raise ValueError(f"起点无棋子: ({fx},{fy}) idx={fromIdx} fen={fen}")
    dead = board[toIdx]
    if dead != ' ' and dead.isupper() == piece.isupper():
        raise ValueError(f"终点是自己方棋子: piece={piece} dead={dead}")
    board[toIdx] = piece
    board[fromIdx] = ' '
    return compressFen(board)


def parseMovelistStr(movelist):
    # 将天天象棋 movelist 压缩串拆成 [(fx,fy,tx,ty), ...]
    if len(movelist) % 4 != 0:
        raise ValueError(f"movelist 长度不是 4 的倍数: len={len(movelist)}")
    steps = []
    for i in range(0, len(movelist), 4):
        s = movelist[i:i + 4]
        if not s.isdigit():
            raise ValueError(f"movelist 第 {i // 4 + 1} 步不是纯数字: {s}")
        steps.append((int(s[0]), int(s[1]), int(s[2]), int(s[3])))
    return steps


def normalizeQipuJson(qipuJson):
    # 将任意支持的格式归一成 {'startFen': str, 'moves': [(fx,fy,tx,ty),...]}
    if 'sData' in qipuJson:
        sData = json.loads(qipuJson['sData'])
        moveinfo = sData.get('moveinfo') or {}
        binit = moveinfo.get('binit', '')
        if binit != STANDARD_BINIT:
            raise ValueError(f"非标准开局 binit 暂不支持: {binit[:40]}...")
        startFen = STANDARD_START_FEN
        movelist = moveinfo.get('movelist', '')
        moves = parseMovelistStr(movelist)
        return {'startFen': startFen, 'moves': moves}
    if 'startFen' in qipuJson and 'moves' in qipuJson:
        return {'startFen': qipuJson['startFen'], 'moves': qipuJson['moves']}
    raise ValueError(f"无法识别的棋谱 JSON 结构,keys={list(qipuJson.keys())}")


def jsonToFenList(qipuJson):
    # 从一个 qipu JSON 对象生成 FEN 序列(包含起始 FEN),自动兼容新老格式
    norm = normalizeQipuJson(qipuJson)
    fen = norm['startFen']
    moves = norm['moves']
    out = [fen]
    for i, mv in enumerate(moves):
        fx, fy, tx, ty = mv
        try:
            fen = applyMoveToFen(fen, fx, fy, tx, ty)
        except ValueError as e:
            raise ValueError(f"第 {i + 1} 步走棋失败: move={mv} err={e}")
        out.append(fen)
    return out


def convertOne(jsonPath, txtPath):
    with open(jsonPath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    fens = jsonToFenList(data)
    with open(txtPath, 'w', encoding='utf-8') as f:
        for line in fens:
            f.write(line + '\n')
    return len(fens)


def convertAll(rawDir, outDir):
    # 批量转化 rawDir/*.json -> outDir/<qipuId>.txt
    if not os.path.isdir(rawDir):
        raise ValueError(f"raw 目录不存在: {rawDir}")
    os.makedirs(outDir, exist_ok=True)
    results = []
    for name in sorted(os.listdir(rawDir)):
        if not name.endswith('.json'):
            continue
        jsonPath = os.path.join(rawDir, name)
        qipuId = name[:-len('.json')]
        txtPath = os.path.join(outDir, f'{qipuId}.txt')
        try:
            n = convertOne(jsonPath, txtPath)
            results.append((qipuId, n, None))
            print(f'OK  {qipuId}: {n} 行 -> {txtPath}')
        except Exception as e:
            results.append((qipuId, 0, str(e)))
            print(f'ERR {qipuId}: {e}')
    return results


def smokeTest():
    # 标准开局走"炮二平五"(h2->e2) 等价于 (fx=7,fy=7) -> (tx=4,ty=7)
    startFen = 'rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR'
    expectedAfter1 = 'rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C2C4/9/RNBAKABNR'
    actual = applyMoveToFen(startFen, 7, 7, 4, 7)
    assert actual == expectedAfter1, f'炮二平五 FEN 不匹配\n期望: {expectedAfter1}\n实际: {actual}'
    print('smoke 炮二平五 OK')

    # 第 2 步:黑炮 8 平 5 (fx=7,fy=2) -> (tx=4,fy=2)
    expectedAfter2 = 'rnbakabnr/9/1c2c4/p1p1p1p1p/9/9/P1P1P1P1P/1C2C4/9/RNBAKABNR'
    actual2 = applyMoveToFen(actual, 7, 2, 4, 2)
    assert actual2 == expectedAfter2, f'黑炮 8 平 5 FEN 不匹配\n期望: {expectedAfter2}\n实际: {actual2}'
    print('smoke 黑炮 8 平 5 OK')

    # 第 3 步:红马二进三 (fx=7,fy=9) -> (tx=6,fy=7)
    expectedAfter3 = 'rnbakabnr/9/1c2c4/p1p1p1p1p/9/9/P1P1P1P1P/1C2C1N2/9/RNBAKAB1R'
    actual3 = applyMoveToFen(actual2, 7, 9, 6, 7)
    assert actual3 == expectedAfter3, f'马二进三 FEN 不匹配\n期望: {expectedAfter3}\n实际: {actual3}'
    print('smoke 马二进三 OK')

    print('全部 smoke 通过')


if __name__ == '__main__':
    import sys
    if len(sys.argv) >= 2 and sys.argv[1] == 'smoke':
        smokeTest()
    else:
        # 默认批量转化:../qipu/raw/ -> ../qipu/
        rawDir = os.path.join(os.path.dirname(__file__), '..', 'qipu', 'raw')
        outDir = os.path.join(os.path.dirname(__file__), '..', 'qipu')
        results = convertAll(rawDir, outDir)
        okCount = sum(1 for _, _, e in results if e is None)
        print(f'\n完成: {okCount}/{len(results)} 成功')
