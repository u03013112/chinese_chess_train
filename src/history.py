# 历史棋谱观看

# 做一个简单界面
# 左侧是功能，包括按钮和一些信息
# 右侧是一个棋盘，用于展示可视化棋谱。


# 做一个按钮
# 选择棋谱文件
# 点击后，罗列qipu目录中的所有文件
# 选择文件后点击确认按钮，开始显示棋谱

# 开始显示棋谱之后
# 显示 按钮（之前是隐藏的，现在显示出来）
# 上一步，下一步
# 隐藏后续，我的后续，最佳后续1，最佳后续2，最佳后续3

# 显示一些信息， N/Total 当前第N步，总共Total步
# 显示当前棋谱的名称（文件名）

import os
import csv
import tkinter as tk
from tkinter import filedialog
from ChessBoard import ChessBoard

class ChessHistoryGui(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('历史棋谱观看')
        self.geometry('500x400')
        self.initUI()
        self.fenList = []
        self.bestMoveList = []
        self.currentStep = 0

    def initUI(self):
        self.btnSelectFile = tk.Button(self, text='选择棋谱文件', command=self.selectFile)
        self.btnSelectFile.grid(row=0, column=0, pady=5)

        self.btnPrev = tk.Button(self, text='上一步', command=self.prevStep)
        self.btnPrev.grid(row=1, column=0, pady=5)

        self.btnNext = tk.Button(self, text='下一步', command=self.nextStep)
        self.btnNext.grid(row=2, column=0, pady=5)

        self.textLabel = tk.Label(self, text='', width=20)
        self.textLabel.grid(row=3, column=0)

        self.chessBoard = ChessBoard(self, width=300, height=350)
        self.chessBoard.draw_board(style=2)
        self.chessBoard.grid(row=0, column=1, rowspan=4)

    def selectFile(self):
        file_path = filedialog.askopenfilename(initialdir=os.getcwd()+'/../qipu', title='选择棋谱文件', filetypes=(('CSV文件', '*.csv'), ('所有文件', '*.*')))
        if file_path:
            with open(file_path, 'r') as f:
                reader = csv.reader(f)
                next(reader)  # skip header
                for row in reader:
                    self.fenList.append(row[1])
                    self.bestMoveList.append([row[5], row[8], row[11]])
                self.currentStep = 0
                self.updateStep()
                self.updateText()

    def prevStep(self):
        if self.currentStep > 0:
            self.currentStep -= 1
            self.updateStep()
            self.updateText()

    def nextStep(self):
        if self.currentStep < len(self.fenList) - 1:
            self.currentStep += 1
            self.updateStep()
            self.updateText()

    def updateStep(self):
        fen = self.fenList[self.currentStep]
        self.chessBoard.readFen(fen)

    def updateText(self):
        text = f'步数：{self.currentStep}/{len(self.fenList) - 1}'
        text += f'\n最优走法：{self.bestMoveList[self.currentStep]}'
        self.textLabel.config(text=text)

if __name__ == '__main__':
    app = ChessHistoryGui()
    app.mainloop()
