import cv2
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFont

#检测圆形，返回圆心坐标和半径,参数为输入图像，阈值，最小半径，最大半径
def detect_circle(img,threshold,min_radius,max_radius):
    gray=cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
    circles=cv2.HoughCircles(gray,cv2.HOUGH_GRADIENT,1,20, param1=50,
                            param2=threshold,minRadius=min_radius,maxRadius=max_radius)
    # 绘制检测到的圆形
    if circles is not None:
        circles = np.uint16(np.around(circles))
        for i in circles[0, :]:
            cv2.circle(img, (i[0], i[1]), i[2], (0, 255, 0), 2)

        # 显示图像
        # cv2.imshow('detected circles', img)
        # cv2.waitKey(0)
        # cv2.destroyAllWindows()

    return img,circles

#根据圆心和半径，返回外接矩形
def get_rect(img,circles):
    
    lstrect=[]
    for i in circles[0, :]:
        x,y,r=i[0],i[1],i[2]
        x1,y1,x2,y2=x-r,y-r,x+r,y+r
        cv2.rectangle(img,pt1=(x1,y1),pt2=(x2,y2),color=(0,255,0), thickness=2)
        lstrect.append([x1,y1,x2,y2])
    return img,lstrect

#比较两张图片的特征点,返回相似度
def compare_feature(img1,img2):
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

outputImgPath = '../img'
if not os.path.exists(outputImgPath):
    os.makedirs(outputImgPath)

    #棋子检测
    # 找到一张天天象棋的截图，尽可能的清晰，保持原本分辨率
    imgpath="/Users/u03013112/Downloads/cc2.png"
    img=cv2.imread(imgpath)
    imgsrc=img.copy()
    img=cv2.resize(img,(img.shape[1]//2,img.shape[0]//2))
    imgsrc=cv2.resize(imgsrc,(imgsrc.shape[1]//2,imgsrc.shape[0]//2))
    
    #保存棋子图片,作为原始数据
    def save_chess(img,lst:list):
        for i,xy in enumerate(lst):
            x1,y1,x2,y2=xy
            cv2.imwrite("../img/chess"+str(i+1)+".jpg",img[y1:y2,x1:x2])

    #检测棋子
    _,circles=detect_circle(img,50,20,50)
    #获取外接矩形
    dst,lstrect=get_rect(imgsrc,circles)

    #保存棋子图片（只运行一次）
    save_chess(dst,lstrect)

# ocr效果不好
# 后续人工将棋子分辨，并改名为
# 红仕.jpg        红帅.jpg        红相.jpg        红马.jpg        黑士.jpg        黑炮.jpg        黑车.jpg
# 红兵.jpg        红炮.jpg        红车.jpg        黑卒.jpg        黑将.jpg        黑象.jpg        黑马.jpg
    

# 找到一张天天象棋的截图，尽可能的清晰，保持原本分辨率
imgpath="/Users/u03013112/Downloads/cc2.png"
img=cv2.imread(imgpath)
imgsrc=img.copy()
img=cv2.resize(img,(img.shape[1]//2,img.shape[0]//2))
imgsrc=cv2.resize(imgsrc,(imgsrc.shape[1]//2,imgsrc.shape[0]//2))

#保存棋子图片,作为原始数据
def save_chess(img,lst:list):
    for i,xy in enumerate(lst):
        x1,y1,x2,y2=xy
        cv2.imwrite("../img/chess"+str(i+1)+".jpg",img[y1:y2,x1:x2])

#检测棋子
_,circles=detect_circle(img,50,20,50)
#获取外接矩形
dst,lstrect=get_rect(imgsrc,circles)


lstname=[] #棋盘上的棋子名称
for xy in lstrect:
    x1,y1,x2,y2=xy
    img=imgsrc[y1:y2,x1:x2]
    # cv2.imshow("img",img)
    # cv2.waitKey(0)
    # cv2.destroyAllWindows()
    lstsim=[]
    
    for f in os.listdir(outputImgPath):
        #文件名包括中文
        img2=cv2.imdecode(np.fromfile(os.path.join(outputImgPath,f),dtype=np.uint8),-1)
        #img2=cv2.cvtColor(img2,cv2.COLOR_RGB2BGR)
        sim=compare_feature(img,img2)
        lstsim.append({f:sim})
    #按照相似度排序
    lstsim.sort(key=lambda x:x[list(x.keys())[0]],reverse=True)
    #获取最相似的图片的棋子名称
    chessname=list(lstsim[0].keys())[0].split(".")[0]
    lstname.append(chessname)

#输出当前棋子
# print(len(lstname),lstname)
    
#显示中文
# def cv2ImgAddText(img, text, left, top, textColor=(0, 255, 0), textSize=20):
#     draw = ImageDraw.Draw(img)
#     fontText = ImageFont.truetype("font/simsun.ttc", textSize, encoding="utf-8")
#     # draw.text((left, top), text, textColor, font=fontText)
#     draw.text((left, top), text, textColor)
#     return cv2.cvtColor(np.asarray(img), cv2.COLOR_RGB2BGR)


# 棋子名字映射，因为中文显示有问题，所以用英文代替
lstNameMap = {
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

def cv2ImgAddText(img, text, left, top, textColor=(0, 255, 0), textSize=20):
    fontScale = textSize / 20
    font = cv2.FONT_HERSHEY_SIMPLEX
    thickness = 2
    textSize, _ = cv2.getTextSize(text, font, fontScale, thickness)
    text_origin = (left, top + textSize[1])
    cv2.putText(img, text, text_origin, font, fontScale, textColor, thickness)
    return img

#把棋子名称根据棋子坐标放置到棋盘上
def put_chess(blank,lstname,lstrect):
    for i,xy in enumerate(lstrect):
        x1,y1,x2,y2=xy
        if lstname[i][0]=="红":
            textColor=(255,0,0)
        else:
            textColor=(0,0,0)
        blank=cv2ImgAddText(blank,lstNameMap[lstname[i]],x1,y1,textColor=textColor,textSize=20)
    return blank

result=put_chess(imgsrc,lstname,lstrect)

# cv2.imshow("Original",dst)
cv2.imshow("Result",result)

cv2.waitKey(0)
cv2.destroyAllWindows()