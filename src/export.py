import os
import datetime
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
    # cv2.imshow("frame", frame)
    # cv2.waitKey(0)
    # cv2.destroyAllWindows()
    # print('视频分辨率:', frame.shape[1], frame.shape[0])

    # 检测棋盘
    if exporter.detectBoard(frame):
        print("棋盘检测成功，开始导出棋谱。")

        # 逐帧处理视频
        while ret:
            # 导出FEN
            exporter.exportFen(frame)

            # 读取下一帧
            ret, frame = cap.read()
            # cv2.imshow("frame", frame)
            # cv2.waitKey(0)
            # cv2.destroyAllWindows()
    else:
        print("棋盘检测失败，请重试。")

    # 保存结果
    exporter.save()

    # 释放视频资源
    cap.release()

if __name__ == '__main__':
    video_filename = "../screenSnapshot/2024-05-11_12-24-13.avi"
    test(video_filename)
