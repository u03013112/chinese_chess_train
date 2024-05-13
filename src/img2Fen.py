import cv2
import os
import time
import numpy as np
import copy

class Img2Fen:
    def __init__(self, outputImgPath = '../img'):
        # 获取当前脚本所在的绝对路径
        scriptDir = os.path.dirname(os.path.realpath(__file__))
        # 根据当前脚本的绝对路径生成输出目录
        self.outputImgPath = os.path.abspath(os.path.join(scriptDir, outputImgPath))
        
        self.lstNameMap = {
            "红仕": "A",
            "红帅": "K",
            "红相": "B",
            "红马": "N",
            "红兵": "P",
            "红炮": "C",
            "红车": "R",
            "黑士": "a",
            "黑炮": "c",
            "黑车": "r",
            "黑卒": "p",
            "黑将": "k",
            "黑象": "b",
            "黑马": "n"
        }
        self.boardRect = None
        self.boardPosition = None

        self.dataList = None
        self.sift = cv2.SIFT_create()

    def init(self, imgPath="/Users/u03013112/Downloads/cc2.png"):
        if os.path.exists(self.outputImgPath):
            print('已存在', self.outputImgPath)
            print('如果想重新生成，请删除该文件夹')

            # 必须有如下文件，否则无法识别
            filenameList = [
                '红车.jpg' , '红帅.jpg' , '红马.jpg' , '红炮.jpg' , '红仕.jpg' , '红相.jpg' , '红兵.jpg', 
                '黑车.jpg' , '黑将.jpg' , '黑马.jpg' , '黑炮.jpg' , '黑士.jpg' , '黑象.jpg' , '黑卒.jpg'
            ]
            self.data = []
            for f in filenameList:
                img2 = cv2.imdecode(np.fromfile(os.path.join(self.outputImgPath, f), dtype=np.uint8), -1)
                self.data.append({f: img2})

            return

        os.makedirs(self.outputImgPath)
        img = cv2.imread(imgPath)
        imgSrc = img.copy()
        img = cv2.resize(img, (img.shape[1] // 2, img.shape[0] // 2))
        imgSrc = cv2.resize(imgSrc, (imgSrc.shape[1] // 2, imgSrc.shape[0] // 2))
        _, circles = self.detectCircle(img, 50, 20, 50)
        dst, lstRect = self.getRect(imgSrc, circles)
        self.saveChess(dst, lstRect)
        print('已将棋子图片保存在', self.outputImgPath)
        print('请将棋子图片分辨，并改名为类似：')
        print('红仕.jpg        红帅.jpg        红相.jpg        红马.jpg        黑士.jpg        黑炮.jpg        黑车.jpg')

    def getLstNameAndLstRect(self, img):
        imgSrc = img.copy()
        _, circles = self.detectCircle(img, 50, 20, 50)
        # print(circles)
        # debug
        # 将圆画出来
        # for i in circles[0, :]:
        #     x, y, r = i[0], i[1], i[2]
        #     cv2.circle(img, (x, y), r, (0, 255, 0), 2)
        # cv2.imshow('img', img)
        # cv2.waitKey(0)
        # cv2.destroyAllWindows()

        dst, lstRect = self.getRect(imgSrc, circles)
        lstName = self.getChessName(dst, lstRect)
        return lstName, lstRect

    def detectCircle(self, img, threshold, minRadius, maxRadius):
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        circles = cv2.HoughCircles(gray, cv2.HOUGH_GRADIENT, 1, 20, param1=50,
                                param2=threshold, minRadius=minRadius, maxRadius=maxRadius)
        if circles is not None:
            circles = np.uint16(np.around(circles))
            for i in circles[0, :]:
                cv2.circle(img, (i[0], i[1]), i[2], (0, 255, 0), 2)
        return img, circles

    def getRect(self, img, circles):
        lstRect = []
        for i in circles[0, :]:
            x, y, r = i[0], i[1], i[2]
            x1, y1, x2, y2 = x - r, y - r, x + r, y + r
            cv2.rectangle(img, pt1=(x1, y1), pt2=(x2, y2), color=(0, 255, 0), thickness=2)
            lstRect.append([x1, y1, x2, y2])
        return img, lstRect

    def saveChess(self, img, lst):
        for i, xy in enumerate(lst):
            x1, y1, x2, y2 = xy
            cv2.imwrite(self.outputImgPath + "/chess" + str(i + 1) + ".jpg", img[y1:y2, x1:x2])

    def extractColorHistogram(self, image, bins=(16, 16, 16)):
        # hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        hist = cv2.calcHist([image], [0, 1, 2], None, bins, [0, 180, 0, 256, 0, 256])
        cv2.normalize(hist, hist)
        return hist.flatten()

    def compareHistograms(self, hist1, hist2):
        return cv2.compareHist(hist1, hist2, cv2.HISTCMP_CORREL)

    def getFeature(self, img):
        img = cv2.resize(img, (35, 35))
        _, des = self.sift.detectAndCompute(img, None)
        return des

    def compareFeature(self, img1, img2):
        # 将图片缩小，加快特征提取速度
        des1 = self.getFeature(img1)
        des2 = self.getFeature(img2)

        bf = cv2.BFMatcher()
        matches = bf.knnMatch(des1, des2, k=2)
        good = []
        for m, n in matches:
            if m.distance < 0.75 * n.distance:
                good.append([m])
        return len(good)

    def compareFeature2(self, img1, des):
        des1 = self.getFeature(img1)
        bf = cv2.BFMatcher()
        matches = bf.knnMatch(des1, des, k=2)
        good = []
        for m, n in matches:
            if m.distance < 0.75 * n.distance:
                good.append([m])
        return len(good)
    
    def extract_center_color(self,img):
        h, w, _ = img.shape
        a = 2
        center = (int(w/2), int(h/2))
        square = img[center[1]-int(a):center[1]+int(a), center[0]-int(a):center[0]+int(a)]
        return np.mean(np.mean(square, axis=0), axis=0)

    def compare_color(self,color1, color2):
        return np.sqrt(np.sum((color1 - color2) ** 2))

    def compare_color2(self,color1, color2):
        return abs(color1[0] - color2[0]) + abs(color1[1] - color2[1]) + abs(color1[2] - color2[2])

    def getChessName(self, imgSrc, lstRect):
        
        lstName = [] 
        
        if self.dataList is None:
            # 等待比对的图片列表，限制匹配数量，加速
            dataList = []
            for d1 in self.data:
                f = list(d1.keys())[0]
                img2 = d1[f]
                count = 2
                if f == '红帅.jpg' or f == '黑将.jpg':
                    count = 1
                if f == '红兵.jpg' or f == '黑卒.jpg':
                    count = 5

                dataList.append({'f': f, 'des': self.getFeature(img2), 'count': count})
            self.dataList = dataList
        
        dataList = copy.deepcopy(self.dataList)

        for xy in lstRect:
            x1, y1, x2, y2 = xy
            img = imgSrc[y1:y2, x1:x2]
            lstSim = []
            
            for data in dataList:
                if data['count'] == 0:
                    continue
                f = data['f']
                des = data['des']
                
                sim = self.compareFeature2(img, des)
                
                lstSim.append({f: sim})
            if len(lstSim) == 0:
                break
            lstSim.sort(key=lambda x: x[list(x.keys())[0]], reverse=True)
            chessName = list(lstSim[0].keys())[0].split(".")[0]
            
            for data in dataList:
                if data['f'] == chessName + '.jpg':
                    data['count'] -= 1
                    break
            # for data in dataList:
            #     print(data['f'], data['count'])
            
            lstName.append(chessName)

        return lstName

    # 将棋盘的范围，以便之后可以裁剪出棋盘，加快后续的识别速度
    def getBoardRect(self,img):
        # 标准分辨率会比较大，缩小一倍不影响识别，并且会加快识别速度
        img = cv2.resize(img, (img.shape[1] // 2, img.shape[0] // 2))
        lstName, lstRect = self.getLstNameAndLstRect(img)
    
        # 找到 红车 与 黑车 的位置，以此确定棋盘的位置
        rRectList = []
        for i in range(len(lstName)):
            if lstName[i] == '红车':
                rRectList.append(lstRect[i])
            if lstName[i] == '黑车':
                rRectList.append(lstRect[i])

        if len(rRectList) != 4:
            print('未找到红车和黑车')
            return ''
        boardX1, boardY1 = min([x1 for x1, _, _, _ in rRectList]), min([y1 for _, y1, _, _ in rRectList])
        boardX2, boardY2 = max([x2 for _, _, x2, _ in rRectList]), max([y2 for _, _, _, y2 in rRectList])
        
        self.boardRect = (boardX1*2-20, boardY1*2-20, boardX2*2+20, boardY2*2+40)
        return 'ok'

    # isYoloOutput,返回yolo的格式输出
    # 其中名字分类直接用self.lstNameMap来做，按顺序，从0开始
    def getFenFromImg(self, img, isYoloOutput=False):
        # 标准分辨率会比较大，缩小一倍不影响识别，并且会加快识别速度
        img = cv2.resize(img, (img.shape[1] // 2, img.shape[0] // 2))
        
        lstName, lstRect = self.getLstNameAndLstRect(img)
        
        if self.boardPosition is None:
            # 找到 红车 与 黑车 的位置，以此确定棋盘的位置
            rRectList = []
            for i in range(len(lstName)):
                if lstName[i] == '红车':
                    rRectList.append(lstRect[i])
                if lstName[i] == '黑车':
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
            piece = self.lstNameMap[name]
            x = (x1 + x2) / 2
            y = (y1 + y2) / 2
            j = round((x - boardX1) / cellWidth)
            i = round((y - boardY1) / cellHeight)
            # i = round((boardY2 - y) / cellHeight)
            boardMatrix[i][j] = piece

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

        if isYoloOutput:
            # 将棋盘中每一个棋子作为一行
            # 每一行的格式类似 ：45 0.479492 0.688771 0.955609 0.5955
            # 第一个数字是类别，按照self.lstNameMap的key的顺序，从0开始
            # 后面四个数字是中心点的坐标，以及宽高，都是相对于整个图片的比例，即左上角是(0,0)，右下角是(1,1)
            yoloRet = []
            imgHeight, imgWidth = img.shape[:2]
            for name, (x1, y1, x2, y2) in zip(lstName, lstRect):
                piece_class = list(self.lstNameMap.keys()).index(name)
                centerX = (x1 + x2) / 2.0 / imgWidth
                centerY = (y1 + y2) / 2.0 / imgHeight
                width = abs(x2 - x1) / imgWidth
                height = abs(y2 - y1) / imgHeight
                yoloRet.append(f"{piece_class} {centerX} {centerY} {width} {height}")

            return fen, "\n".join(yoloRet)

        return fen
    
    def yoloCheck(self, img, yoloStr):
        imgHeight, imgWidth = img.shape[:2]
        yoloLines = yoloStr.split("\n")

        for line in yoloLines:
            parts = line.split()
            piece_class = int(parts[0])
            centerX = float(parts[1]) * imgWidth
            centerY = float(parts[2]) * imgHeight
            width = float(parts[3]) * imgWidth
            height = float(parts[4]) * imgHeight

            x1 = int(centerX - width / 2)
            y1 = int(centerY - height / 2)
            x2 = int(centerX + width / 2)
            y2 = int(centerY + height / 2)

            piece_name = list(self.lstNameMap.values())[piece_class]

            cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(img, piece_name, (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (36,255,12), 2)

        cv2.imshow("Image", img)
        cv2.waitKey(0)
        cv2.destroyAllWindows()


if __name__ == '__main__':
    # from PIL import ImageGrab
    # img = ImageGrab.grab()
    # imgNp = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
    # imgNp.save('screen.png')
    img2fen = Img2Fen()
    img2fen.init('cc3.png')

    img1 = cv2.imread('cc3.png')    
    img2fen.getBoardRect(img1)
    print(img2fen.boardRect)

    fen,yoloStr = img2fen.getFenFromImg(img1, isYoloOutput=True)
    print(fen)

    img2fen.yoloCheck(img1, yoloStr)
    
