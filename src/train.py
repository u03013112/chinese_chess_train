# 做一个简单界面
# 左侧是功能，包括按钮和一些信息
# 右侧是一个棋盘，用于展示可视化棋谱。

# 目前暂时只有一个按钮
# 《看杀》 功能暂时不做，点了没用


# 右侧添加一个棋盘等待展示棋谱

import tkinter as tk
from ChessBoard import ChessBoard

class SimpleChessGui(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('简单棋盘展示')
        self.geometry('500x420')
        self.initUI()

    def initUI(self):
        self.btnWatchKill = tk.Button(self, text='看杀', width=10)
        self.btnWatchKill.grid(row=0, column=0, pady=5)

        self.chessBoard = ChessBoard(self, width=300, height=350)
        self.chessBoard.draw_board(style=2)
        self.chessBoard.grid(row=0, column=1, rowspan=8, padx=20)

if __name__ == '__main__':
    app = SimpleChessGui()
    app.mainloop()
