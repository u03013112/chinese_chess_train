参考
https://docs.ultralytics.com/modes/train/#apple-m1-and-m2-mps-training
将数据放到 ~/datasets中，然后运行以下命令：
```bash
yolo train data=coco8.yaml model=yolov8n.pt epochs=300 lr0=0.01 device=mps
```

检测训练效果
```bash
yolo detect predict model=/Users/u03013112/.pyenv/runs/detect/train6/weights/last.pt source='/Users/u03013112/Documents/git/chinese_chess_train/yolo/images/val/2.jpg'
```

目前想过一般，可能还是给出的图太少，或者标注不准确。