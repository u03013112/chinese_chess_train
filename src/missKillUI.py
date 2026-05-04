
import json
import time
import tkinter as tk
from pathlib import Path

from ChessBoard import ChessBoard
from missKill import buildQuestionBank


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
PROGRESS_PATH = REPO_ROOT / 'qipu' / 'progress.json'

GRADUATE_STREAK = 3

SIDE_ZH = {'red': '红', 'black': '黑'}


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


def applyMove(fen, move):
    rows = [list(expandRow(r)) for r in fen.split('/')]
    fx = ord(move[0]) - ord('a')
    fy = 9 - int(move[1])
    tx = ord(move[2]) - ord('a')
    ty = 9 - int(move[3])
    piece = rows[fy][fx]
    rows[fy][fx] = ' '
    rows[ty][tx] = piece
    return '/'.join(compressRow(r) for r in rows)


def expandRow(row):
    out = []
    for ch in row:
        if ch.isdigit():
            out.extend([' '] * int(ch))
        else:
            out.append(ch)
    return out


def compressRow(cells):
    out = []
    blank = 0
    for c in cells:
        if c == ' ':
            blank += 1
        else:
            if blank:
                out.append(str(blank))
                blank = 0
            out.append(c)
    if blank:
        out.append(str(blank))
    return ''.join(out)


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
        self.geometry('760x560')

        self.progress = loadProgress()
        rawBank = buildQuestionBank()
        self.bank = sortBank(rawBank, self.progress)
        self.questionIdx = 0

        self.currentFen = ''
        self.activePv = None
        self.stepInPv = 0
        self.clickFirst = None
        self.lastMove = None

        self.initUI()
        self.loadQuestion()

    def initUI(self):
        left = tk.Frame(self)
        left.grid(row=0, column=0, sticky='nw', padx=10, pady=10)

        self.lblTitle = tk.Label(left, text='', font=('Arial', 14, 'bold'))
        self.lblTitle.grid(row=0, column=0, columnspan=2, sticky='w', pady=4)

        self.lblStat = tk.Label(left, text='', font=('Arial', 11), fg='gray30', justify='left')
        self.lblStat.grid(row=1, column=0, columnspan=2, sticky='w', pady=2)

        self.lblStatus = tk.Label(left, text='', font=('Arial', 12), fg='blue', justify='left')
        self.lblStatus.grid(row=2, column=0, columnspan=2, sticky='w', pady=6)

        self.lblHistory = tk.Label(left, text='', font=('Arial', 11), justify='left', anchor='nw')
        self.lblHistory.grid(row=3, column=0, columnspan=2, sticky='nw', pady=6)

        tk.Button(left, text='上一题', width=10, command=self.prevQuestion).grid(row=10, column=0, pady=2)
        tk.Button(left, text='下一题', width=10, command=self.nextQuestion).grid(row=10, column=1, pady=2)
        tk.Button(left, text='提示', width=10, command=self.showHint).grid(row=11, column=0, pady=2)
        tk.Button(left, text='看答案', width=10, command=self.showAnswer).grid(row=11, column=1, pady=2)
        tk.Button(left, text='重置本题', width=10, command=self.resetQuestion).grid(row=12, column=0, pady=2)
        tk.Button(left, text='跳到第一道未毕业', width=18, command=self.jumpPending).grid(row=12, column=1, pady=2)

        self.chessBoard = ChessBoard(self, width=330, height=360, w=32)
        self.chessBoard.draw_board(style=2)
        self.chessBoard.grid(row=0, column=1, padx=16, pady=10, sticky='n')
        self.chessBoard.bind('<Button-1>', self.onBoardClick)

    def loadQuestion(self):
        if not self.bank:
            self.lblStatus.config(text='题库为空', fg='red')
            return
        q = self.bank[self.questionIdx]
        self.currentFen = q['fen']
        self.activePv = None
        self.stepInPv = 0
        self.clickFirst = None
        self.lastMove = None
        self.chessBoard.delete('highlight')
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
        w = self.chessBoard.w
        fx = round(event.x / w - 1)
        ucirank = round(10 - event.y / w)
        if not (0 <= fx <= 8) or not (0 <= ucirank <= 9):
            return None
        return f'{chr(ord("a") + fx)}{ucirank}'

    def onBoardClick(self, event):
        q = self.bank[self.questionIdx]
        if self.activePv is not None and self.stepInPv >= len(self.activePv['moves']):
            return
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
        col = ord(pos[0]) - ord('a')
        rank = int(pos[1])
        cx = (col + 1) * w
        cy = (10 - rank) * w
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
        self.currentFen = applyMove(self.currentFen, move)
        self.chessBoard.readFen(self.currentFen)
        self.chessBoard.draw_arrow(move[:2], move[2:], arrowColor, self.stepInPv + 1)
        self.lastMove = move
        self.appendHistory(move)

    def appendHistory(self, move):
        old = self.lblHistory.cget('text')
        q = self.bank[self.questionIdx]
        step = self.stepInPv + 1
        mover = q['side'] if step % 2 == 1 else ('black' if q['side'] == 'red' else 'red')
        line = f'{step}. {SIDE_ZH[mover]} {move}'
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
        hintSet = ','.join(q['killMoveSet'])
        self.lblStatus.config(
            text=f'{move} 不在杀手集合。错 {p["wrong"]} 次。杀手:{hintSet}\n重置本题再来',
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
        q = self.bank[self.questionIdx]
        if self.activePv is None:
            firstSet = ','.join(q['killMoveSet'])
            self.lblStatus.config(text=f'提示:第一步可走 {firstSet}', fg='purple')
        else:
            nxt = self.activePv['moves'][self.stepInPv] if self.stepInPv < len(self.activePv['moves']) else ''
            self.lblStatus.config(text=f'提示:下一步 {nxt}', fg='purple')

    def showAnswer(self):
        q = self.bank[self.questionIdx]
        pv = q['pvs'][0]
        self.chessBoard.readFen(q['fen'])
        self.currentFen = q['fen']
        for i, move in enumerate(pv['moves']):
            mover = q['side'] if i % 2 == 0 else ('black' if q['side'] == 'red' else 'red')
            color = 'red' if mover == 'red' else 'black'
            self.chessBoard.draw_arrow(move[:2], move[2:], color, i + 1)
        self.activePv = None
        self.stepInPv = 0
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
