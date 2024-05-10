# 做一个简单界面
# 左侧是功能，包括按钮和一些信息
# 右侧是一个棋盘，用于展示可视化棋谱。

# 目前暂时只有一个按钮
# 《看杀》 功能暂时不做，点了没用


# 右侧添加一个棋盘等待展示棋谱

import tkinter as tk
from lookKill import LookKill
from ChessBoard import ChessBoard

class SimpleChessGui(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('简单棋盘展示')
        self.geometry('500x420')
        self.initUI()
        # mode 暂时只有init和lookKill两种
        self.mode = 'init'
        self.lookKill = None

    def initUI(self):
        self.btnWatchKill = tk.Button(self, text='看杀', width=10, command=self.watchKill)
        self.btnWatchKill.grid(row=0, column=0, pady=5)

        self.btnPrev = tk.Button(self, text='上一题', command=self.prevQuestion)
        self.btnPrev.grid(row=1, column=0, pady=5)

        self.btnNext = tk.Button(self, text='下一题', command=self.nextQuestion)
        self.btnNext.grid(row=2, column=0, pady=5)

        self.textLabel = tk.Text(self, wrap=tk.WORD, height=4,width=25)
        self.textLabel.grid(row=7, column=0)
        self.textLabel.tag_configure('red', foreground='red')
        self.textLabel.tag_configure('black', foreground='black')
        self.textLabel.tag_configure('blue', foreground='blue')
        self.textLabel.config(state=tk.DISABLED)

        self.chessBoard = ChessBoard(self, width=300, height=350)
        self.chessBoard.draw_board(style=2)
        self.chessBoard.grid(row=0, column=1, rowspan=8, padx=20)

    def watchKill(self):
        print('看杀')
        if self.lookKill is None:
            self.lookKill = LookKill()
            self.mode = 'lookKill'

    def updateText(self):
        self.textLabel.config(state=tk.NORMAL)
        self.textLabel.delete('1.0', tk.END)

        if self.mode == 'lookKill':
            question = self.lookKill.getCurrentQuestion()
            color = question['color']
            colorZ = '红' if color == 'red' else '黑'
            step = question['step']
            self.textLabel.insert(tk.END, f'{colorZ}方', color)
            self.textLabel.insert(tk.END, f' {step}步杀\n', 'blue')
        else:
            self.textLabel.insert(tk.END, '请先选择模式')

    def prevQuestion(self):
        if self.mode == 'lookKill':
            question = self.lookKill.prevQuestion()
            self.chessBoard.readFen(question['fen'])
            self.updateText()
        else:
            print('请先选择模式')

    def nextQuestion(self):
        if self.mode == 'lookKill':
            question = self.lookKill.nextQuestion()
            self.chessBoard.readFen(question['fen'])
            self.updateText()
        else:
            print('请先选择模式')
        

if __name__ == '__main__':
    app = SimpleChessGui()
    app.mainloop()
