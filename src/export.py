# 棋谱导出，简易版本

# 做一个简单界面
# 上面3个按钮
# 1.检测棋盘
# 2.开始导出
# 3.结束导出

# 在检测棋盘时，弹出一个窗口，提示 “请将《天天象棋》游戏界面尽量不缩小，棋盘不要被遮挡，并且保持开局状态。”
# 弹出窗口两个按钮，1.确定 2.取消
# 点击确定后，开始屏幕截图，并检测棋盘，检测到棋盘后，弹出窗口提示 “棋盘检测成功，点击开始导出按钮，开始导出棋谱。”
# 调用 img2Fen.py 中的 getFenFromImg 方法，获取棋盘的 fen 字符串，如果检测到结果是“rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR” 或者“RNBAKABNR/9/1C5C1/P1P1P1P1P/9/9/p1p1p1p1p/1c5c1/9/rnbakabnr” 则提示检测成功，否则提示检测失败。

# 点击开始导出按钮后，每隔1秒，屏幕截图，并调用 img2Fen.py 中的 getFenFromImg 方法，获取棋盘的 fen 字符串
# 检测结果记录在一行中，连续的发现相同的 fen 字符串，只记录一次，直到检测到新的 fen 字符串
# 当检测到新的开局状态时，或者用户点击结束导出，将之前记录的棋谱保存到指定路径下，并用 yyyyMMddHHmmss.txt 命名

# 点击结束后，保存完棋谱，退出程序

import sys
import time
import datetime
import tkinter as tk
from tkinter import messagebox
from PIL import ImageGrab
from img2Fen import Img2Fen
import cv2
import numpy as np

class ChessGui(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('棋谱导出')
        self.geometry('500x200')  # 增加窗口宽度以适应更长的文本
        self.initUI()
        self.img2fen = Img2Fen()
        self.img2fen.init()
        self.fenList = []
        self.after_id = None

    def initUI(self):
        self.btnDetect = tk.Button(self, text='检测棋盘', command=self.detectBoard)
        self.btnDetect.pack(pady=5)
        self.btnStart = tk.Button(self, text='开始导出', command=self.startExport)
        self.btnStart.pack(pady=5)
        self.btnEnd = tk.Button(self, text='结束导出', command=self.endExport)
        self.btnEnd.pack(pady=5)

        # 添加一个Label组件来显示文本
        self.textLabel = tk.Label(self, text='', width=80)  # 设置足够的宽度以适应更长的文本
        self.textLabel.pack()
    
    def updateText(self, text):
        # 更新Label组件的文本
        self.textLabel.config(text=text)

    def getScreen(self):
        img = ImageGrab.grab()
        imgNp = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
        # 去掉下面工具条，大约200像素
        # 苹果的图标好多都是圆的，好烦人
        imgNp = imgNp[:-200, :, :]
        return imgNp
    
    def detectBoard(self):
        # if messagebox.askokcancel('提示', "请将《天天象棋》游戏界面尽量不缩小，棋盘不要被遮挡，并且保持开局状态。"):
            img = self.getScreen()

            fen = self.img2fen.getFenFromImg(img)
            if fen in ["rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR",
                        "RNBAKABNR/9/1C5C1/P1P1P1P1P/9/9/p1p1p1p1p/1c5c1/9/rnbakabnr"]:
                messagebox.showinfo('提示', "棋盘检测成功，点击开始导出按钮，开始导出棋谱。")
            else:
                messagebox.showwarning('提示', "棋盘检测失败，请重试。\n请将《天天象棋》游戏界面尽量不缩小，棋盘不要被遮挡，并且保持开局状态。")

    def startExport(self):
        self.exportFen()
        
    def exportFen(self):
        img = self.getScreen()
        fen = self.img2fen.getFenFromImg(img)
        if not self.fenList or fen != self.fenList[-1]:
            print(fen)
            self.updateText(fen)
            self.fenList.append(fen)
        self.after_id = self.after(100, self.exportFen)

    def endExport(self):
        if self.after_id:
            self.after_cancel(self.after_id)
            self.after_id = None
        with open(datetime.datetime.now().strftime('%Y%m%d%H%M%S') + '.txt', 'w') as f:
            f.write('\n'.join(self.fenList))
        self.quit()

    def debugFen(self, fen):
        # 将fen表示成更易读的形式
        # 先将数字换成空格
        # 再将斜杠换成换行
        fen = fen.replace('1', ' ').replace('2', '  ').replace('3', '   ').replace('4', '    ').replace('5', '     ').replace('6', '      ').replace('7', '       ').replace('8', '        ').replace('9', '         ')
        fen = fen.replace('/', '\n')
        # 上下颠倒
        fen_lines = fen.split('\n')
        fen = '\n'.join(reversed(fen_lines))
        return fen

    def getMove(self, lastFen, fen):
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
                    raise ValueError("Too many differences in FEN strings")

                if fen[i] == ' ':
                    move_from = i
                else:
                    move_to = i

        if diff_count != 2:
            return None

        col_labels = 'abcdefghi'
        row_labels = '0123456789'
        move = col_labels[move_from % 9] + row_labels[move_from // 10] + col_labels[move_to % 9] + row_labels[move_to // 10]
        return move


if __name__ == '__main__':
    app = ChessGui()
    # app.mainloop()
    fen1 = 'rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR'
    fen2 = 'rnbakabnr/9/1c2c4/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR'
    
    print(app.debugFen(fen1))
    print(app.debugFen(fen2))

    print(app.getMove(fen1, fen2))
