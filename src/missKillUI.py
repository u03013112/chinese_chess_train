
import json
import time
import tkinter as tk
from pathlib import Path
from tkinter import ttk

from ChessBoard import ChessBoard
from missKill import buildQuestionBank
from tools import applyMove, expandFenRow


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
PROGRESS_PATH = REPO_ROOT / 'qipu' / 'progress.json'

GRADUATE_STREAK = 3

SIDE_ZH = {'red': '红', 'black': '黑'}

# 难度选项: (label, exactSteps | None),exactSteps=None 表示不限步数(含所有长度)
DIFFICULTY_OPTS = [
    ('1 步杀', 1),
    ('3 步杀', 3),
    ('5 步杀', 5),
    ('7 步杀', 7),
    ('9 步杀', 9),
    ('全部', None),
]

# 来源选项: (label, sourceFilter)
#   'csv' = 仅棋谱实际局面的杀题(根 FEN)
#   'pv'  = 仅 PV 沿途展开的中间局面
#   None  = 全部
SOURCE_OPTS = [
    ('仅根局面', 'csv'),
    ('含展开', None),
    ('仅展开', 'pv'),
]

# 中文数字
CN_NUM = ['', '一', '二', '三', '四', '五', '六', '七', '八', '九']

PIECE_NAME = {
    'R': '车', 'r': '车',
    'N': '马', 'n': '马',
    'B': '相', 'b': '象',
    'A': '仕', 'a': '士',
    'K': '帅', 'k': '将',
    'C': '炮', 'c': '炮',
    'P': '兵', 'p': '卒',
}

DIAGONAL_PIECES = set('NnBbAa')  # 马/相/象/士/仕 走斜线,记谱用"进/退 目标列"


def loadProgress():
    if not PROGRESS_PATH.exists():
        return {}
    try:
        with open(PROGRESS_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {}


def saveProgress(data):
    PROGRESS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(PROGRESS_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def pieceAt(fen, move):
    rows = fen.split('/')
    fy = 9 - int(move[1])
    fx = ord(move[0]) - ord('a')
    row = list(expandFenRow(rows[fy]))
    if fx >= len(row):
        return ' '
    return row[fx]


def moveToQp(fen, move):
    piece = pieceAt(fen, move)
    if piece == ' ':
        return move
    isRed = piece.isupper()
    name = PIECE_NAME.get(piece, piece)

    fromCol = ord(move[0]) - ord('a')
    toCol = ord(move[2]) - ord('a')
    fromRank = int(move[1])
    toRank = int(move[3])

    if isRed:
        fromColNum = 9 - fromCol
        toColNum = 9 - toCol
        forward = toRank > fromRank
        sideTag = '红'
    else:
        fromColNum = fromCol + 1
        toColNum = toCol + 1
        forward = toRank < fromRank
        sideTag = '黑'

    def colStr(n):
        return CN_NUM[n] if isRed else str(n)

    if fromRank == toRank:
        action = f'平{colStr(toColNum)}'
    elif piece in DIAGONAL_PIECES:
        verb = '进' if forward else '退'
        action = f'{verb}{colStr(toColNum)}'
    else:
        verb = '进' if forward else '退'
        steps = abs(toRank - fromRank)
        action = f'{verb}{colStr(steps)}'

    return f'{sideTag} {name}{colStr(fromColNum)}{action}'


def sortBank(bank, progress):
    # 优先 missed,其次 streak 小的,再次按文件名
    def key(q):
        p = progress.get(q['fen'], {})
        streak = p.get('streak', 0)
        graduated = 1 if streak >= GRADUATE_STREAK else 0
        missedKey = 0 if q['missed'] else 1
        return (graduated, missedKey, streak, q['file'], q['idx'])
    return sorted(bank, key=key)


class MissKillUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('看杀主动训练')
        self.geometry('780x580')

        self.progress = loadProgress()
        self.rawBank = buildQuestionBank()
        self.exactSteps = 3
        self.sourceFilter = 'csv'
        self.bank = []
        self.questionIdx = 0

        self.currentFen = ''
        self.activePv = None
        self.stepInPv = 0
        self.clickFirst = None
        self.lastMove = None

        self.initUI()
        self.applyDifficulty()
        self.loadQuestion()

    def applyDifficulty(self):
        filtered = list(self.rawBank)
        if self.exactSteps is not None:
            filtered = [q for q in filtered if len(q['pvs'][0]['moves']) == self.exactSteps]
        if self.sourceFilter is not None:
            filtered = [q for q in filtered if q.get('source') == self.sourceFilter]
        self.bank = sortBank(filtered, self.progress)
        self.questionIdx = 0

    def onDifficultyChange(self, _event=None):
        label = self.cbDiff.get()
        for text, n in DIFFICULTY_OPTS:
            if text == label:
                self.exactSteps = n
                break
        self.applyDifficulty()
        self.loadQuestion()

    def onSourceChange(self, _event=None):
        label = self.cbSource.get()
        for text, s in SOURCE_OPTS:
            if text == label:
                self.sourceFilter = s
                break
        self.applyDifficulty()
        self.loadQuestion()

    def initUI(self):
        left = tk.Frame(self)
        left.grid(row=0, column=0, sticky='nw', padx=10, pady=10)

        self.lblTitle = tk.Label(left, text='', font=('Arial', 14, 'bold'))
        self.lblTitle.grid(row=0, column=0, columnspan=2, sticky='w', pady=4)

        self.lblStat = tk.Label(left, text='', font=('Arial', 11), fg='gray30', justify='left')
        self.lblStat.grid(row=1, column=0, columnspan=2, sticky='w', pady=2)

        diffRow = tk.Frame(left)
        diffRow.grid(row=2, column=0, columnspan=2, sticky='w', pady=4)
        tk.Label(diffRow, text='难度:', font=('Arial', 11)).pack(side=tk.LEFT)
        self.cbDiff = ttk.Combobox(
            diffRow, state='readonly', width=8,
            values=[t for t, _ in DIFFICULTY_OPTS],
        )
        self.cbDiff.set('3 步杀')
        self.cbDiff.pack(side=tk.LEFT, padx=4)
        self.cbDiff.bind('<<ComboboxSelected>>', self.onDifficultyChange)

        tk.Label(diffRow, text='  来源:', font=('Arial', 11)).pack(side=tk.LEFT)
        self.cbSource = ttk.Combobox(
            diffRow, state='readonly', width=8,
            values=[t for t, _ in SOURCE_OPTS],
        )
        self.cbSource.set('仅根局面')
        self.cbSource.pack(side=tk.LEFT, padx=4)
        self.cbSource.bind('<<ComboboxSelected>>', self.onSourceChange)

        self.lblStatus = tk.Label(left, text='', font=('Arial', 12), fg='blue', justify='left', wraplength=340)
        self.lblStatus.grid(row=3, column=0, columnspan=2, sticky='w', pady=6)

        self.lblHistory = tk.Label(left, text='', font=('Arial', 11), justify='left', anchor='nw')
        self.lblHistory.grid(row=4, column=0, columnspan=2, sticky='nw', pady=6)

        tk.Button(left, text='上一题', width=10, command=self.prevQuestion).grid(row=10, column=0, pady=2)
        tk.Button(left, text='下一题', width=10, command=self.nextQuestion).grid(row=10, column=1, pady=2)
        tk.Button(left, text='提示', width=10, command=self.showHint).grid(row=11, column=0, pady=2)
        tk.Button(left, text='看答案', width=10, command=self.showAnswer).grid(row=11, column=1, pady=2)
        tk.Button(left, text='重置本题', width=10, command=self.resetQuestion).grid(row=12, column=0, pady=2)
        tk.Button(left, text='跳到第一道未毕业', width=18, command=self.jumpPending).grid(row=12, column=1, pady=2)

        self.chessBoard = ChessBoard(self, width=330, height=360, w=32)
        self.chessBoard.draw_board(style=3)
        self.chessBoard.grid(row=0, column=1, padx=16, pady=10, sticky='n')
        self.chessBoard.bind('<Button-1>', self.onBoardClick)

    def loadQuestion(self):
        if not self.bank:
            self.lblTitle.config(text='')
            self.lblStat.config(text='')
            self.lblHistory.config(text='')
            self.chessBoard.delete('piece')
            self.chessBoard.delete('arrow')
            self.chessBoard.delete('highlight')
            self.lblStatus.config(text=f'当前难度无题目(共 {len(self.rawBank)} 题,过滤后 0)', fg='red')
            return
        q = self.bank[self.questionIdx]
        self.currentFen = q['fen']
        self.activePv = None
        self.stepInPv = 0
        self.clickFirst = None
        self.lastMove = None
        self.chessBoard.delete('highlight')
        self.chessBoard.flipped = (q['side'] == 'black')
        self.chessBoard.delete('all')
        self.chessBoard.draw_board(style=3)
        self.chessBoard.readFen(self.currentFen)

        p = self.progress.get(q['fen'], {})
        streak = p.get('streak', 0)
        correct = p.get('correct', 0)
        wrong = p.get('wrong', 0)
        gradTag = '已毕业 ✓' if streak >= GRADUATE_STREAK else f'连对 {streak}/{GRADUATE_STREAK}'
        missedTag = ' (漏杀)' if q['missed'] else ''

        sideZh = SIDE_ZH[q['side']]
        bestStep = len(q['pvs'][0]['moves'])
        self.lblTitle.config(text=f'{sideZh}方 {bestStep} 步杀{missedTag}')
        self.lblStat.config(
            text=(
                f'第 {self.questionIdx + 1}/{len(self.bank)} 题  |  {q["file"]}#{q["idx"]}\n'
                f'{gradTag}  |  累计对 {correct} / 错 {wrong}'
            )
        )
        self.lblStatus.config(text=f'轮到{sideZh}方,点击起点→终点', fg='blue')
        self.lblHistory.config(text='')

    def posFromEvent(self, event):
        return self.chessBoard.xyToUci(event.x, event.y)

    def onBoardClick(self, event):
        if not self.bank:
            return
        q = self.bank[self.questionIdx]
        if self.activePv is not None and self.stepInPv >= len(self.activePv['moves']):
            return
        self.chessBoard.delete('hint')
        pos = self.posFromEvent(event)
        if pos is None:
            return
        if self.clickFirst is None:
            if not self.hasOwnPieceAt(pos, q['side']):
                self.lblStatus.config(text=f'那格不是{SIDE_ZH[q["side"]]}方棋子,重选起点', fg='orange')
                return
            self.clickFirst = pos
            self.highlightSquare(pos, 'blue')
            return
        if pos == self.clickFirst:
            self.clickFirst = None
            self.chessBoard.delete('highlight')
            return
        move = self.clickFirst + pos
        self.clickFirst = None
        self.chessBoard.delete('highlight')
        self.tryUserMove(move)

    def hasOwnPieceAt(self, pos, side):
        col = ord(pos[0]) - ord('a')
        rank = int(pos[1])
        rows = self.currentFen.split('/')
        targetRow = rows[9 - rank]
        cells = []
        for ch in targetRow:
            if ch.isdigit():
                cells.extend([' '] * int(ch))
            else:
                cells.append(ch)
        if col >= len(cells):
            return False
        ch = cells[col]
        if ch == ' ':
            return False
        isUpper = ch.isupper()
        return (isUpper and side == 'red') or ((not isUpper) and side == 'black')

    def highlightSquare(self, pos, color):
        w = self.chessBoard.w
        cx, cy = self.chessBoard.uciToXY(pos)
        r = w * 0.45
        self.chessBoard.delete('highlight')
        self.chessBoard.create_oval(
            cx - r, cy - r, cx + r, cy + r,
            outline=color, width=3, tags='highlight',
        )

    def tryUserMove(self, move):
        q = self.bank[self.questionIdx]
        if self.activePv is None:
            candidates = [pv for pv in q['pvs'] if pv['moves'][0] == move]
            if not candidates:
                self.onWrong(move)
                return
            self.activePv = max(candidates, key=lambda pv: pv['score'])
            self.stepInPv = 0
            self.applyAndRender(move, 'green')
            self.stepInPv = 1
            if self.stepInPv >= len(self.activePv['moves']):
                self.onQuestionComplete()
            else:
                self.after(500, self.playOpponent)
            return
        expected = self.activePv['moves'][self.stepInPv]
        if move != expected:
            self.onWrong(move)
            return
        self.applyAndRender(move, 'green')
        self.stepInPv += 1
        if self.stepInPv >= len(self.activePv['moves']):
            self.onQuestionComplete()
        else:
            self.after(500, self.playOpponent)

    def playOpponent(self):
        if self.activePv is None:
            return
        if self.stepInPv >= len(self.activePv['moves']):
            self.onQuestionComplete()
            return
        move = self.activePv['moves'][self.stepInPv]
        self.applyAndRender(move, 'gray40')
        self.stepInPv += 1
        q = self.bank[self.questionIdx]
        if self.stepInPv >= len(self.activePv['moves']):
            self.onQuestionComplete()
        else:
            self.lblStatus.config(text=f'轮到{SIDE_ZH[q["side"]]}方,点击起点→终点', fg='blue')

    def applyAndRender(self, move, arrowColor):
        fenBefore = self.currentFen
        self.currentFen = applyMove(self.currentFen, move)
        self.chessBoard.readFen(self.currentFen)
        self.chessBoard.draw_arrow(move[:2], move[2:], arrowColor, self.stepInPv + 1)
        self.lastMove = move
        self.appendHistory(move, fenBefore)

    def appendHistory(self, move, fenBefore):
        old = self.lblHistory.cget('text')
        step = self.stepInPv + 1
        qp = moveToQp(fenBefore, move)
        line = f'{step}. {qp}  ({move})'
        self.lblHistory.config(text=(old + '\n' + line) if old else line)

    def onWrong(self, move):
        q = self.bank[self.questionIdx]
        fen = q['fen']
        p = self.progress.setdefault(fen, {})
        p['wrong'] = p.get('wrong', 0) + 1
        p['streak'] = 0
        p['last_ts'] = time.time()
        p['file'] = q['file']
        p['idx'] = q['idx']
        saveProgress(self.progress)
        userQp = moveToQp(self.currentFen, move) if pieceAt(self.currentFen, move) != ' ' else move
        hintSet = '、'.join(moveToQp(fen, m) for m in q['killMoveSet'])
        self.lblStatus.config(
            text=f'{userQp} 不在杀手集合。错 {p["wrong"]} 次。\n杀手:{hintSet}\n点"重置本题"再来',
            fg='red',
        )

    def onQuestionComplete(self):
        q = self.bank[self.questionIdx]
        fen = q['fen']
        p = self.progress.setdefault(fen, {})
        p['correct'] = p.get('correct', 0) + 1
        p['streak'] = p.get('streak', 0) + 1
        p['last_ts'] = time.time()
        p['file'] = q['file']
        p['idx'] = q['idx']
        saveProgress(self.progress)
        tag = '毕业 ✓' if p['streak'] >= GRADUATE_STREAK else f'连对 {p["streak"]}/{GRADUATE_STREAK}'
        self.lblStatus.config(text=f'完成杀招!{tag}。按"下一题"继续', fg='green')

    def showHint(self):
        if not self.bank:
            return
        q = self.bank[self.questionIdx]
        self.chessBoard.delete('hint')
        if self.activePv is None:
            moves = q['killMoveSet']
            colors = ['purple', 'deep pink', 'dark orange', 'brown', 'magenta']
            for i, m in enumerate(moves):
                self.drawHintArrow(m, colors[i % len(colors)])
            qpList = [moveToQp(q['fen'], m) for m in moves]
            self.lblStatus.config(text=f'提示:可走 {" / ".join(qpList)}', fg='purple')
        else:
            if self.stepInPv >= len(self.activePv['moves']):
                return
            nxt = self.activePv['moves'][self.stepInPv]
            self.drawHintArrow(nxt, 'purple')
            self.lblStatus.config(text=f'提示:下一步 {moveToQp(self.currentFen, nxt)}', fg='purple')

    def drawHintArrow(self, move, color):
        x1, y1 = self.chessBoard.uciToXY(move[:2])
        x2, y2 = self.chessBoard.uciToXY(move[2:])
        self.chessBoard.create_line(
            x1, y1, x2, y2,
            arrow=tk.LAST, fill=color, width=4, dash=(6, 3),
            arrowshape=(16, 18, 8), tags='hint',
        )

    def showAnswer(self):
        if not self.bank:
            return
        q = self.bank[self.questionIdx]
        pv = q['pvs'][0]
        self.chessBoard.readFen(q['fen'])
        self.chessBoard.delete('hint')
        self.currentFen = q['fen']
        qpLines = []
        fenIter = q['fen']
        for i, move in enumerate(pv['moves']):
            mover = q['side'] if i % 2 == 0 else ('black' if q['side'] == 'red' else 'red')
            color = 'red' if mover == 'red' else 'black'
            self.chessBoard.draw_arrow(move[:2], move[2:], color, i + 1)
            qpLines.append(f'{i + 1}. {moveToQp(fenIter, move)}')
            fenIter = applyMove(fenIter, move)
        self.activePv = None
        self.stepInPv = 0
        self.lblHistory.config(text='\n'.join(qpLines))
        self.lblStatus.config(text='答案已展示。按"重置本题"练习,或"下一题"', fg='gray30')

    def resetQuestion(self):
        self.loadQuestion()

    def prevQuestion(self):
        if not self.bank:
            return
        self.questionIdx = (self.questionIdx - 1) % len(self.bank)
        self.loadQuestion()

    def nextQuestion(self):
        if not self.bank:
            return
        self.questionIdx = (self.questionIdx + 1) % len(self.bank)
        self.loadQuestion()

    def jumpPending(self):
        for i, q in enumerate(self.bank):
            p = self.progress.get(q['fen'], {})
            if p.get('streak', 0) < GRADUATE_STREAK:
                self.questionIdx = i
                self.loadQuestion()
                return
        self.lblStatus.config(text='题库所有题都已毕业 🎉', fg='green')


if __name__ == '__main__':
    app = MissKillUI()
    app.mainloop()
