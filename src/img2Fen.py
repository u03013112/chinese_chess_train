# 从图片转换为FEN格式的棋局状态
import cv2
import os
import math
import numpy as np

class Img2Fen:
    def __init__(self,outputImgPath = '../img'):
        self.outputImgPath = outputImgPath
        self.lstNameMap = {
            "红仕":"a",
            "红帅":"k",
            "红相":"b",
            "红马":"n",
            "红兵":"p",
            "红炮":"c",
            "红车":"r",
            "黑士":"A",
            "黑炮":"C",
            "黑车":"R",
            "黑卒":"P",
            "黑将":"K",
            "黑象":"B",
            "黑马":"N"
        }
        self.board_position = None

    def init(self,imgpath="/Users/u03013112/Downloads/cc2.png"):
        # 初始化，主要是针对棋子检测
        # 给出imgpath，需要拥有所有棋子的图片
        # 生成的图片保存在outputImgPath中
        if os.path.exists(self.outputImgPath):
            print('已存在',self.outputImgPath)
            print('如果想重新生成，请删除该文件夹')
            return
            
        os.makedirs(self.outputImgPath)
        img=cv2.imread(imgpath)
        imgsrc=img.copy()
        img=cv2.resize(img,(img.shape[1]//2,img.shape[0]//2))
        imgsrc=cv2.resize(imgsrc,(imgsrc.shape[1]//2,imgsrc.shape[0]//2))
        _,circles=self.detect_circle(img,50,20,50)
        dst,lstrect=self.get_rect(imgsrc,circles)
        self.save_chess(dst,lstrect)
        print('已将棋子图片保存在',self.outputImgPath)
        print('请将棋子图片分辨，并改名为类似：')
        print('红仕.jpg        红帅.jpg        红相.jpg        红马.jpg        黑士.jpg        黑炮.jpg        黑车.jpg')

    def getLstnameAndLstrect(self,imgpath="/Users/u03013112/Downloads/cc2.png"):
        img=cv2.imread(imgpath)
        imgsrc=img.copy()
        img=cv2.resize(img,(img.shape[1]//2,img.shape[0]//2))
        imgsrc=cv2.resize(imgsrc,(imgsrc.shape[1]//2,imgsrc.shape[0]//2))
        _,circles=self.detect_circle(img,50,20,50)
        dst,lstrect=self.get_rect(imgsrc,circles)
        lstname=self.get_chess_name(dst,lstrect)
        return lstname, lstrect

    def detect_circle(self,img,threshold,min_radius,max_radius):
        gray=cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
        circles=cv2.HoughCircles(gray,cv2.HOUGH_GRADIENT,1,20, param1=50,
                                param2=threshold,minRadius=min_radius,maxRadius=max_radius)
        if circles is not None:
            circles = np.uint16(np.around(circles))
            for i in circles[0, :]:
                cv2.circle(img, (i[0], i[1]), i[2], (0, 255, 0), 2)
        return img,circles

    def get_rect(self,img,circles):
        lstrect=[]
        for i in circles[0, :]:
            x,y,r=i[0],i[1],i[2]
            x1,y1,x2,y2=x-r,y-r,x+r,y+r
            cv2.rectangle(img,pt1=(x1,y1),pt2=(x2,y2),color=(0,255,0), thickness=2)
            lstrect.append([x1,y1,x2,y2])
        return img,lstrect

    def save_chess(self,img,lst:list):
        for i,xy in enumerate(lst):
            x1,y1,x2,y2=xy
            cv2.imwrite(self.outputImgPath+"/chess"+str(i+1)+".jpg",img[y1:y2,x1:x2])

    def compare_feature(self,img1,img2):
        sift=cv2.xfeatures2d.SIFT_create()
        kp1,des1=sift.detectAndCompute(img1,None)
        kp2,des2=sift.detectAndCompute(img2,None)
        bf=cv2.BFMatcher()
        matches=bf.knnMatch(des1,des2,k=2)
        good=[]
        for m,n in matches:
            if m.distance<0.75*n.distance:
                good.append([m])
        return len(good)

    def get_chess_name(self,imgsrc,lstrect):
        lstname=[] 
        for xy in lstrect:
            x1,y1,x2,y2=xy
            img=imgsrc[y1:y2,x1:x2]
            lstsim=[]
            for f in os.listdir(self.outputImgPath):
                img2=cv2.imdecode(np.fromfile(os.path.join(self.outputImgPath,f),dtype=np.uint8),-1)
                sim=self.compare_feature(img,img2)
                lstsim.append({f:sim})
            lstsim.sort(key=lambda x:x[list(x.keys())[0]],reverse=True)
            chessname=list(lstsim[0].keys())[0].split(".")[0]
            lstname.append(chessname)
        return lstname
    
    def getFenFromImg(self, imgpath="/Users/u03013112/Downloads/cc2.png"):
        lstname, lstrect = self.getLstnameAndLstrect(imgpath)

        if self.board_position is None:
            # 获取棋盘位置和范围
            board_x1, board_y1 = min([(x1 + x2) // 2 for x1, _, x2, _ in lstrect]), min([(y1 + y2) // 2 for _, y1, _, y2 in lstrect])
            board_x2, board_y2 = max([(x1 + x2) // 2 for x1, _, x2, _ in lstrect]), max([(y1 + y2) // 2 for _, y1, _, y2 in lstrect])
            self.board_position = (board_x1, board_y1, board_x2, board_y2)
        else:
            board_x1, board_y1, board_x2, board_y2 = self.board_position

        # 计算棋盘格子大小
        cell_width = (board_x2 - board_x1) // 8
        cell_height = (board_y2 - board_y1) // 9

        # 初始化棋盘矩阵
        board_matrix = [['' for _ in range(9)] for _ in range(10)]

        # 将棋子放置到棋盘矩阵中
        for name, (x1, y1, x2, y2) in zip(lstname, lstrect):
            piece = self.lstNameMap[name]
            x = (x1 + x2) / 2
            y = (y1 + y2) / 2
            j = round((x - board_x1) / cell_width)
            i = round((y - board_y1) / cell_height)
            board_matrix[i][j] = piece

        # 生成FEN格式的棋局状态
        fen = ""
        for row in board_matrix:
            empty_count = 0
            for piece in row:
                if piece == '':
                    empty_count += 1
                else:
                    if empty_count > 0:
                        fen += str(empty_count)
                        empty_count = 0
                    fen += piece
            if empty_count > 0:
                fen += str(empty_count)
            fen += '/'
        fen = fen[:-1]  # 去掉最后一个'/'

        return fen

    
if __name__ == '__main__':
    img2fen = Img2Fen()
    fen = img2fen.getFenFromImg()
    print(fen)
