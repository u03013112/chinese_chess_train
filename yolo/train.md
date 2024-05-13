参考
https://docs.ultralytics.com/modes/train/#apple-m1-and-m2-mps-training
将数据放到 ~/datasets中，然后运行以下命令：
```bash
yolo train data=coco8.yaml model=yolov8n.pt epochs=100 lr0=0.01 device=mps
```
