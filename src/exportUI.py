import sys
import time
import datetime
import tkinter as tk
from tkinter import messagebox
from PIL import ImageGrab
from mss import mss
import cv2
import numpy as np
import pandas as pd
import os
from export import Export
from ChessBoard import ChessBoard

class ChessGui(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('棋谱导出')
        self.geometry('500x400')  # 增加窗口宽度以适应更长的文本
        self.initUI()
        self.exporter = Export()
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
            # mss获得的分辨率是原始分辨率的2倍，需要缩放
            # imgNp = cv2.resize(imgNp, (int(imgNp.shape[1] / 2), int(imgNp.shape[0] / 2)))

            if isFullScreen == False:
                box = self.exporter.img2fen.boardRect
                
                imgNp = imgNp[box[1]:box[3], box[0]:box[2], :]
            else:
                # 去掉下面工具条，大约200像素
                # 苹果的图标好多都是圆的，好烦人
                imgNp = imgNp[:-200, :, :]
            
        imgNp = cv2.cvtColor(imgNp, cv2.COLOR_BGRA2BGR)
        return imgNp
    
    def detectBoard(self,debug=False):        
        img = self.getScreen(isFullScreen=True)
        ret = self.exporter.img2fen.getBoardRect(img)
        self.exporter.img2fen.boardPosition = None
        if ret == 'ok':
            self.updateText('棋盘检测成功，点击开始导出按钮，开始导出棋谱。')

            # debug 将棋盘画出来
            if debug:
                print(self.exporter.img2fen.boardRect)
                img = cv2.rectangle(img, (self.exporter.img2fen.boardRect[0], self.exporter.img2fen.boardRect[1]), (self.exporter.img2fen.boardRect[2], self.exporter.img2fen.boardRect[3]), (0, 255, 0), 2)
                cv2.imshow('img', img)
                cv2.waitKey(0)
                cv2.destroyAllWindows()

        else:
            self.updateText('棋盘检测失败，请重试。')

    def startExport(self):
        self.exporter.filename = os.getcwd()+'/../qipu/'+datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S') + '.txt'
        self.exportFen()
        self.timeCheck()
        
    def exportFen(self):
        if self.exporter.img2fen.boardRect is None:
            self.updateText('请先检测棋盘。')
            return
        img = self.getScreen()
        # debug
        # cv2.imshow('img', img)
        # cv2.waitKey(0)
        # cv2.destroyAllWindows()

        fen = self.exporter.exportFen(img)
        if fen:
            self.chessBoard.readFen(fen)
            stepCount = len(self.exporter.fenList) - 1 if len(self.exporter.fenList) > 0 else 0
            self.updateText(f'目前是第{stepCount}步。')
        
        self.after_id = self.after(10, self.exportFen)

    def endExport(self):
        if self.after_id:
            self.after_cancel(self.after_id)
            self.after_id = None
        self.exporter.save()
        # self.quit()

if __name__ == '__main__':
    app = ChessGui()
    app.mainloop()
