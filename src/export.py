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
from mss import mss
from img2Fen import Img2Fen
import cv2
import numpy as np
from ChessBoard import ChessBoard

class ChessGui(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('棋谱导出')
        self.geometry('500x400')  # 增加窗口宽度以适应更长的文本
        self.initUI()
        self.img2fen = Img2Fen()
        self.img2fen.init()
        self.fenList = []
        self.moveList = []
        self.after_id = None

        # 用于计算运行效率
        self.timer = None
        self.getScreenCount = 0
    
    def timeCheck(self):
        if self.timer == None or time.time() - self.timer > 1:
            self.timer = time.time()
            print(f'getScreenCount: {self.getScreenCount}')
            self.getScreenCount = 0
            
        self.after(10, self.timeCheck)
        
    def initUI(self):
        self.btnDetect = tk.Button(self, text='检测棋盘', command=self.detectBoard)
        self.btnDetect.grid(row=0, column=0, pady=5)

        self.btnStart = tk.Button(self, text='开始导出', command=self.startExport)
        self.btnStart.grid(row=1, column=0, pady=5)

        self.btnEnd = tk.Button(self, text='结束导出', command=self.endExport)
        self.btnEnd.grid(row=2, column=0, pady=5)

        # 添加一个Label组件来显示文本
        self.textLabel = tk.Label(self, text='1234567890', width=20)  # 设置足够的宽度以适应更长的文本
        self.textLabel.grid(row=3, column=0)

        # 添加ChessBoard到界面中
        self.chessBoard = ChessBoard(self, width=300, height=350)
        self.chessBoard.draw_board(style=2)
        self.chessBoard.grid(row=0, column=1, rowspan=4)
    
    def updateText(self, text):
        # 更新Label组件的文本
        self.textLabel.config(text=text)

    def getScreen(self,isFullScreen=False,debug=False):
        self.getScreenCount += 1
        with mss() as sct:
            monitor = sct.monitors[0]
            img = sct.grab(monitor)

            imgNp = np.array(img)

            if isFullScreen == False:
                box = self.img2fen.boardRect
                imgNp = imgNp[box[1]:box[3], box[0]:box[2], :]
            
        imgNp = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
        # 去掉下面工具条，大约200像素
        # 苹果的图标好多都是圆的，好烦人
        imgNp = imgNp[:-200, :, :]
        return imgNp
    
    def detectBoard(self,debug=False):        
        img = self.getScreen(isFullScreen=True)
        ret = self.img2fen.getBoardRect(img)
        self.img2fen.boardPosition = None
        if ret == 'ok':
            self.updateText('棋盘检测成功，点击开始导出按钮，开始导出棋谱。')
            if True or debug:
                rect = self.img2fen.boardRect
                
                img = ImageGrab.grab()
                imgNp = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)

                cv2.rectangle(imgNp, (rect[0], rect[1]), (rect[2], rect[3]), (0, 0, 255), 2)                

                cv2.imwrite('ccTest1.png', imgNp)

                bbox = (rect[0], rect[1], rect[2], rect[3])
                img = ImageGrab.grab(bbox)
                imgNp = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
                cv2.imwrite('ccTest2.png', imgNp)

        else:
            self.updateText('棋盘检测失败，请重试。')

    def startExport(self):
        self.exportFen()
        self.timeCheck()
        
    def exportFen(self):
        if self.img2fen.boardRect is None:
            self.updateText('请先检测棋盘。')
            return
        img = self.getScreen()
        # startTime = time.time()
        try:
            fen = self.img2fen.getFenFromImg(img)
            # print(f'getFenFromImg time: {time.time() - startTime}')
            if not self.fenList or fen != self.fenList[-1]:
                print(fen)
                if len(self.fenList) > 0:
                    lastFen = self.fenList[-1]
                    if fen != lastFen:
                        try:
                            p,move = self.getMove(lastFen, fen)
                        except ValueError as e:
                            # 解决各种异常，比如由于各种问题导致的棋盘检测失败
                            print(e)
                        else:
                            # 记录行动的棋子与行动
                            print(p,move)
                            self.moveList.append({'p': p, 'move': move})
                            # 判断是否是同一个棋子连续行动，如果是，需要合并
                            if len(self.moveList) > 1 and self.moveList[-1]['p'] == self.moveList[-2]['p']:
                                self.moveList[-2]['move'] += move
                                self.moveList.pop()
                                # self.fenList 也需要做相应处理，将最后一个fen去掉
                                self.fenList.pop()

                            self.chessBoard.readFen(fen)
                            self.fenList.append(fen)
                            stepCount = len(self.fenList) - 1 if len(self.fenList) > 0 else 0
                            self.updateText(f'目前是第{stepCount}步。{move}')
                else:
                    self.chessBoard.readFen(fen)
                    self.fenList.append(fen)
        except Exception as e:
            pass
        
        self.after_id = self.after(10, self.exportFen)

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

    def getMove(self, lastFen, fen, debug=False):
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

        pLast = lastFen[move_from]
        p = fen[move_to]

        if debug:
            print(''.join(lastFen))
            print(''.join(fen))
            print('p last:', pLast)
            print('p:', p)

        # 按照中国象棋的规则，棋子是不能凭空消失的，pLast 与 p 必须相同
        if pLast != p:
            raise None

        col_labels = 'abcdefghi'
        row_labels = '0123456789'
        move = col_labels[move_from % 9] + row_labels[move_from // 9] + col_labels[move_to % 9] + row_labels[move_to // 9]
        return p,move

def debug():
    app = ChessGui()
    with open('20240426233230.txt', 'r') as f:
        content = f.read()
        fenList = content.split('\n')
        # print(fenList)
    
    for i in range(len(fenList) - 1):
        fen1 = fenList[i]
        fen2 = fenList[i + 1]
        print(fen1)
        print(fen2)
        print(app.getMove(fen1, fen2))

if __name__ == '__main__':
    app = ChessGui()
    app.mainloop()


    
    
