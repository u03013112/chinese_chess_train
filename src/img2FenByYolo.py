import cv2
import os
import numpy as np
from ultralytics import YOLO

class Img2FenByYolo:
    def __init__(self, model_path):
        self.lstNameMap = {
            0: "A",
            1: "K",
            2: "B",
            3: "N",
            4: "P",
            5: "C",
            6: "R",
            7: "a",
            8: "c",
            9: "r",
            10: "p",
            11: "k",
            12: "b",
            13: "n"
        }
        self.boardRect = None
        self.boardPosition = None

        # Load a pretrained YOLO model
        self.model = YOLO(model_path)

    def getLstNameAndLstRect(self, img):
        # Resize the image
        # img = cv2.resize(img, (640, 640))

        # Run inference on the source
        results = self.model(img)  # list of Results objects

        # Get the height and width of the image
        height, width = img.shape[:2]

        lstName = []
        lstRect = []
        for result in results:
            # Get the bounding boxes and their labels
            boxes = result.boxes.xyxy  # box with xyxy format, (N, 4)
            labels = result.boxes.cls  # cls, (N, 1)

            for i in range(len(boxes)):
                x1, y1, x2, y2 = [int(x) for x in boxes[i]]
                label = labels[i]
                name = self.lstNameMap[int(label.item())]

                lstName.append(name)
                lstRect.append([x1, y1, x2, y2])

        return lstName, lstRect

    def getBoardRect(self, img):
        lstName, lstRect = self.getLstNameAndLstRect(img)

        # 找到 红车 与 黑车 的位置，以此确定棋盘的位置
        rRectList = []
        for i in range(len(lstName)):
            if lstName[i] == 'R' or lstName[i] == 'r':
                rRectList.append(lstRect[i])

        if len(rRectList) < 4:
            print('未找到红车和黑车', len(rRectList))
            return ''
        
        boardX1, boardY1 = min([x1 for x1, _, _, _ in rRectList]), min([y1 for _, y1, _, _ in rRectList])
        boardX2, boardY2 = max([x2 for _, _, x2, _ in rRectList]), max([y2 for _, _, _, y2 in rRectList])
        w = (boardX2 - boardX1)//16

        self.boardRect = (boardX1-w, boardY1-w, boardX2+w, boardY2+w)
        return 'ok'

    def getFenFromImg(self, img):
        lstName, lstRect = self.getLstNameAndLstRect(img)

        if self.boardPosition is None:
            # 找到 红车 与 黑车 的位置，以此确定棋盘的位置
            rRectList = []
            for i in range(len(lstName)):
                if lstName[i] == 'R':
                    rRectList.append(lstRect[i])
                if lstName[i] == 'r':
                    rRectList.append(lstRect[i])

            if len(rRectList) != 4:
                print('未找到红车和黑车')
                return ''
            boardX1, boardY1 = min([(x1 + x2) // 2 for x1, _, x2, _ in rRectList]), min([(y1 + y2) // 2 for _, y1, _, y2 in rRectList])
            boardX2, boardY2 = max([(x1 + x2) // 2 for x1, _, x2, _ in rRectList]), max([(y1 + y2) // 2 for _, y1, _, y2 in rRectList])
            self.boardPosition = (boardX1, boardY1, boardX2, boardY2)
        else:
            boardX1, boardY1, boardX2, boardY2 = self.boardPosition

        cellWidth = (boardX2 - boardX1) // 8
        cellHeight = (boardY2 - boardY1) // 9

        boardMatrix = [['' for _ in range(9)] for _ in range(10)]

        for name, (x1, y1, x2, y2) in zip(lstName, lstRect):
            x = (x1 + x2) / 2
            y = (y1 + y2) / 2
            j = round((x - boardX1) / cellWidth)
            i = round((y - boardY1) / cellHeight)
            boardMatrix[i][j] = name

        fen = ""
        for row in boardMatrix:
            emptyCount = 0
            for piece in row:
                if piece == '':
                    emptyCount += 1
                else:
                    if emptyCount > 0:
                        fen += str(emptyCount)
                        emptyCount = 0
                    fen += piece
            if emptyCount > 0:
                fen += str(emptyCount)
            fen += '/'
        fen = fen[:-1]

        return fen

if __name__ == '__main__':
    img2fen = Img2FenByYolo('../yolo/last.pt')

    img1 = cv2.imread('cc3.png')
    
    # lstName, lstRect = img2fen.getLstNameAndLstRect(img1)
    # # debug 将lstName, lstRect 画出来
    # for name, (x1, y1, x2, y2) in zip(lstName, lstRect):
    #     img1 = cv2.rectangle(img1, (x1, y1), (x2, y2), (0, 255, 0), 2)
    #     img1 = cv2.putText(img1, name, (x1, y1), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
    # cv2.imshow('img', img1)
    # cv2.waitKey(0)
    # cv2.destroyAllWindows()
    
    img2fen.getBoardRect(img1)    
    img = img1[img2fen.boardRect[1]:img2fen.boardRect[3], img2fen.boardRect[0]:img2fen.boardRect[2]]


    # debug 将棋盘画出来
    # rect = img2fen.boardRect
    # img1 = cv2.rectangle(img1, (rect[0], rect[1]), (rect[2], rect[3]), (0, 255, 0), 2)
    cv2.imshow('img', img)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

    fen = img2fen.getFenFromImg(img)
    print(fen)
