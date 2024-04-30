
pNameList = [
    {'qpName':"仕",'fenName':"a"},
    {'qpName':"帅",'fenName':"k"},
    {'qpName':"相",'fenName':"b"},
    {'qpName':"马",'fenName':"n"},
    {'qpName':"兵",'fenName':"p"},
    {'qpName':"炮",'fenName':"c"},
    {'qpName':"车",'fenName':"r"},
    {'qpName':"士",'fenName':"A"},
    {'qpName':"炮",'fenName':"C"},
    {'qpName':"车",'fenName':"R"},
    {'qpName':"卒",'fenName':"P"},
    {'qpName':"将",'fenName':"K"},
    {'qpName':"象",'fenName':"B"},
    {'qpName':"马",'fenName':"N"}
]

def getMove(lastFen, fen, debug=False):
        def expand_fen(fen):
            expanded = []
            for char in fen:
                if char.isdigit():
                    expanded.extend([' '] * int(char))
                else:
                    expanded.append(char)
            return expanded

        lastFen = expand_fen(lastFen.replace('/', ''))
        fen = expand_fen(fen.replace('/', ''))

        if len(lastFen) != len(fen):
            raise ValueError("Invalid FEN strings")

        diff_count = 0
        move_from = None
        move_to = None

        for i in range(len(lastFen)):
            if lastFen[i] != fen[i]:
                diff_count += 1
                if diff_count > 2:
                    raise ValueError("变化的数量太多了, diff_count={diff_count}")

                if fen[i] == ' ':
                    move_from = i
                else:
                    move_to = i

        if diff_count != 2:
            raise ValueError(f"变化的数量不是2个, diff_count={diff_count}")

        pLast = lastFen[move_from]
        p = fen[move_to]

        if debug:
            print(''.join(lastFen))
            print(''.join(fen))
            print('p last:', pLast)
            print('p:', p)

        # 按照中国象棋的规则，棋子是不能凭空消失的，pLast 与 p 必须相同
        if pLast != p:
            raise ValueError(f"棋子发生了变化, {pLast} => {p}")

        col_labels = 'abcdefghi'
        row_labels = '0123456789'
        move = col_labels[move_from % 9] + row_labels[move_from // 9] + col_labels[move_to % 9] + row_labels[move_to // 9]
        return p,move

# 从类似c,h2e2 转化成 红方 炮二平五
def fenMove2Qp(p,move):
    ret = ''
    fromX = move[0]
    fromY = int(move[1]) + 1
    toX = move[2]
    toY = int(move[3]) + 1
    fromX = ord('i') - ord(fromX) + 1
    toX = ord('i') - ord(toX) + 1

    if p.islower():
        color = '红'
    else:
        color = '黑'
        fromX = 9 - fromX + 1
        toX = 9 - toX + 1
        fromY = 10 - fromY
        toY = 10 - toY

    name = ''
    for pName in pNameList:
        if pName['fenName'] == p:
            name = pName['qpName']
            break
    
    ret = f'{color} {name}'
    if fromY == toY:
        ret += f'{fromX}平{toX}'
    
    if fromX == toX:
        if fromY > toY:
            s = fromY - toY
            ret += f'{fromY}退{s}'
        else:
            s = toY - fromY
            ret += f'{fromY}进{s}'

    if name in ['马','相','象','士','仕']:
        if fromY > toY:
            ret += f'{fromX}退{toX}'
        else:
            ret += f'{fromX}进{toX}'

    return ret


def testGetMove():
    fen1 = 'rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR'
    fen2 = 'rnbakabnr/9/1c2c4/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR'
    fen3 = 'rnbakabnr/9/1c2c4/p1p1p1p1p/9/9/P1P1P1P1P/1C2C4/9/RNBAKABNR'
    fen4 = 'rnbakab1r/9/1c2c1n2/p1p1p1p1p/9/9/P1P1P1P1P/1C2C4/9/RNBAKABNR'
    fen5 = 'rnbakab1r/9/1c2c1n2/p1p1p1p1p/9/9/P1P1P1P1P/1C2C1N2/9/RNBAKAB1R'
    p,move = getMove(fen4, fen5, debug=False)
    print( p,move )
    print(fenMove2Qp(p,move))

if __name__ == '__main__':
    testGetMove()