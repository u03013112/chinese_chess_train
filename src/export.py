import os
import datetime
import numpy as np
import pandas as pd
from img2Fen import Img2Fen
from tools import getMove
import cv2

class Export:
    def __init__(self, filename=None):
        self.img2fen = Img2Fen()
        self.img2fen.init()
        self.fenList = []
        self.moveList = []
        self.imgList = []
        self.yoloStrList = []
        self.filename = filename or datetime.datetime.now().strftime('%Y%m%d%H%M%S') + '.txt'
        self.lastFrame = None
        self.lastFrameProcessed = False

    def reset(self, filename=None):
        print('reset')
        # 记录棋盘位置
        lastBoardRect = self.img2fen.boardRect
        self.img2fen = Img2Fen()
        self.img2fen.init()
        self.img2fen.boardRect = lastBoardRect
        self.fenList = []
        self.moveList = []
        self.filename = filename or datetime.datetime.now().strftime('%Y%m%d%H%M%S') + '.txt'
        self.lastFrame = None
        self.lastFrameProcessed = False

    def detectBoard(self, img):
        ret = self.img2fen.getBoardRect(img)
        self.img2fen.boardPosition = None
        if ret == 'ok':
            return True
        else:
            return False

    def isNeedDetect(self, img):
        if self.lastFrame is None:
            self.lastFrame = img.copy()
            self.lastFrameProcessed = False
            return True

        diff = cv2.absdiff(img, self.lastFrame)
        _, diff = cv2.threshold(diff, 100, 255, cv2.THRESH_BINARY)
        if np.any(diff):
            self.lastFrame = img.copy()
            self.lastFrameProcessed = False
            return True
        else:
            return not self.lastFrameProcessed

    def exportFen(self, img, isYoloOutput=False):
        if not self.isNeedDetect(img):
            return None

        if isYoloOutput:
            fen,yoloStr = self.img2fen.getFenFromImg(img, isYoloOutput=True)
        else:
            fen = self.img2fen.getFenFromImg(img)

        if not self.fenList or fen != self.fenList[-1]:
            if len(self.fenList) > 0:
                lastFen = self.fenList[-1]
                if fen != lastFen:
                    try:
                        p, move = getMove(lastFen, fen, debug=True)
                    except ValueError as e:
                        print(e)
                        pass
                    else:
                        self.moveList.append({'p': p, 'move': move})
                        if len(self.moveList) > 1 and self.moveList[-1]['p'] == self.moveList[-2]['p']:
                            self.moveList[-2]['move'] += move
                            self.moveList.pop()
                            self.fenList.pop()
                            if isYoloOutput:
                                self.imgList.pop()
                                self.yoloStrList.pop()

                        self.fenList.append(fen)
                        if isYoloOutput:
                            self.imgList.append(img)
                            self.yoloStrList.append(yoloStr)
            else:
                self.fenList.append(fen)
                if isYoloOutput:
                    self.imgList.append(img)
                    self.yoloStrList.append(yoloStr)

        self.lastFrameProcessed = True
        return self.fenList[-1]

    def save(self, isSaveMove = False):
        with open(self.filename, 'w') as f:
            f.write('\n'.join(self.fenList))

        # 记录moveList
        if isSaveMove:
            pList = []
            moveList = []
            for move in self.moveList:
                pList.append(move['p'])
                moveList.append(move['move'])
            df = pd.DataFrame({'p': pList, 'move': moveList})
            moveFilename = os.path.splitext(self.filename)[0] + '_move.csv'
            df.to_csv(moveFilename, index=False)

def test(video_filename):
    exporter = Export()
    cap = cv2.VideoCapture(video_filename)

    if not cap.isOpened():
        print("Error: Could not open video file.")
        return

    # 读取第一帧
    ret, frame = cap.read()

    # 检测棋盘
    if exporter.detectBoard(frame):
        print("棋盘检测成功，开始导出棋谱。")

        while ret:
            exporter.exportFen(frame)
            ret, frame = cap.read()
    else:
        print("棋盘检测失败，请重试。")

    exporter.save()
    cap.release()

def yoloDataCreate(video_filename):
    exporter = Export()
    cap = cv2.VideoCapture(video_filename)

    if not cap.isOpened():
        print("Error: Could not open video file.")
        return

    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    # 读取第一帧
    ret, frame = cap.read()
    frame = cv2.resize(frame, (w*2, h*2))

    # 检测棋盘
    if exporter.detectBoard(frame):
        print("棋盘检测成功，开始导出棋谱。")

        while ret:
            exporter.exportFen(frame, isYoloOutput=True)
            ret, frame = cap.read()
            if frame is not None:
                frame = cv2.resize(frame, (w*2, h*2))
    else:
        print("棋盘检测失败，请重试。")

    exporter.save()
    cap.release()

    for i in range(len(exporter.imgList)):
        print(i)
        img = exporter.imgList[i]
        cv2.imwrite(f'../yolo/images/{i}.jpg', img)
        with open(f'../yolo/labels/{i}.txt', 'w') as f:
            f.write(exporter.yoloStrList[i])

if __name__ == '__main__':
    video_filename = "../screenSnapshot/2024-05-11_12-24-13.avi"
    # test(video_filename)
    yoloDataCreate(video_filename)
