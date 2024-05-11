import os
import datetime
import numpy as np
import pandas as pd
from img2Fen import Img2Fen
from tools import getMove

class Export:
    def __init__(self, filename=None):
        self.img2fen = Img2Fen()
        self.img2fen.init()
        self.fenList = []
        self.moveList = []
        self.filename = filename or datetime.datetime.now().strftime('%Y%m%d%H%M%S') + '.txt'

    def detectBoard(self, img):
        ret = self.img2fen.getBoardRect(img)
        self.img2fen.boardPosition = None
        if ret == 'ok':
            return True
        else:
            return False

    def exportFen(self, img):
        fen = self.img2fen.getFenFromImg(img)
        if not self.fenList or fen != self.fenList[-1]:
            if len(self.fenList) > 0:
                lastFen = self.fenList[-1]
                if fen != lastFen:
                    try:
                        p, move = getMove(lastFen, fen, debug=False)
                    except ValueError as e:
                        # print(e)
                        pass
                    else:
                        self.moveList.append({'p': p, 'move': move})
                        if len(self.moveList) > 1 and self.moveList[-1]['p'] == self.moveList[-2]['p']:
                            self.moveList[-2]['move'] += move
                            self.moveList.pop()
                            self.fenList.pop()

                        self.fenList.append(fen)
            else:
                self.fenList.append(fen)
        return fen

    def save(self):
        with open(self.filename, 'w') as f:
            f.write('\n'.join(self.fenList))

        # 记录moveList
        pList = []
        moveList = []
        for move in self.moveList:
            pList.append(move['p'])
            moveList.append(move['move'])
        df = pd.DataFrame({'p': pList, 'move': moveList})
        moveFilename = os.path.splitext(self.filename)[0] + '_move.csv'
        df.to_csv(moveFilename, index=False)

import cv2
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

        lastFrame = None
        lastFrameProcessed = False

        count = 0
        while ret:
            count += 1
            if lastFrame is None:
                lastFrame = frame.copy()
                lastFrameProcessed = False
            else:
                # 计算两帧之间的差异
                diff = cv2.absdiff(frame, lastFrame)
                # 将差异转换为二值图像，以便更清楚地看到差异
                _, diff = cv2.threshold(diff, 150, 255, cv2.THRESH_BINARY)
                # 如果两帧之间的差异大于阈值，则更新lastFrame并将lastFrameProcessed设置为False
                if np.any(diff):
                    lastFrame = frame.copy()
                    lastFrameProcessed = False
                else:
                    
                    if not lastFrameProcessed:
                        print(count)
                        # exporter.exportFen(lastFrame)

                        cv2.imshow('frame', lastFrame)
                        cv2.waitKey(0)
                        cv2.destroyAllWindows()
                        
                        lastFrameProcessed = True

            ret, frame = cap.read()
    else:
        print("棋盘检测失败，请重试。")

    # exporter.save()
    cap.release()

def compare_first_two_frames(video_filename):
    cap = cv2.VideoCapture(video_filename)

    if not cap.isOpened():
        print("Error: Could not open video file.")
        return

    # 读取第一帧和第二帧
    ret, frame1 = cap.read()
    ret, frame2 = cap.read()

    # 遍历所有可能的阈值
    for threshold in range(1, 256):
        # 计算两帧之间的差异
        diff = cv2.absdiff(frame1, frame2)

        # 将差异转换为二值图像
        _, diff = cv2.threshold(diff, threshold, 255, cv2.THRESH_BINARY)

        # 如果二值图像中没有白色像素（值为255），则认为两帧一致
        is_diff = np.any(diff)

        print(f"Threshold: {threshold}, is_diff: {is_diff}")

    cap.release()

if __name__ == '__main__':
    video_filename = "../screenSnapshot/2024-05-11_12-24-13.avi"
    test(video_filename)
    # compare_first_two_frames(video_filename)
