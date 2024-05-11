import time
import tkinter as tk
from pynput import mouse
from mss import mss
from PIL import ImageGrab
import threading
import os
import cv2
import numpy as np
import datetime

class ScreenRecorder(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('录屏')
        self.geometry('300x200')
        self.initUI()
        self.is_recording = False
        self.start_x, self.start_y, self.end_x, self.end_y = 0, 0, 0, 0
        self.mouse_listener = mouse.Listener(on_click=self.on_click)
        self.click_count = 0
        self.writer = None
        self.start_x, self.start_y = 0, 0
        self.end_x, self.end_y = self.winfo_screenwidth(), self.winfo_screenheight()

    def initUI(self):
        self.btnSelectRange = tk.Button(self, text='选定范围', command=self.selectRange)
        self.btnSelectRange.pack(pady=10)

        self.btnStart = tk.Button(self, text='开始', command=self.startRecording)
        self.btnStart.pack()

        self.btnStop = tk.Button(self, text='停止', command=self.stopRecording)
        self.btnStop.pack(pady=10)

        self.textLabel = tk.Label(self, text='')
        self.textLabel.pack()

    def on_click(self, x, y, button, pressed):
        if pressed:
            self.click_count += 1
            if self.click_count == 1:
                self.start_x, self.start_y = x, y
                self.textLabel.config(text=f'左上角: ({self.start_x}, {self.start_y})')
            elif self.click_count == 2:
                self.end_x, self.end_y = x, y
                self.textLabel.config(text=f'右下角: ({self.end_x}, {self.end_y})')
                self.mouse_listener.stop()

    def selectRange(self):
        self.click_count = 0
        self.mouse_listener = mouse.Listener(on_click=self.on_click)
        self.mouse_listener.start()

    def startRecording(self):
        self.is_recording = True
        self.textLabel.config(text='开始录制')
        width = int(self.end_x - self.start_x)
        height = int(self.end_y - self.start_y)
        outputFilename = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S') + '.avi'
        outputFilename = os.getcwd() + '/../screenSnapshot/'+outputFilename
        print(outputFilename)
        self.writer = cv2.VideoWriter(outputFilename, cv2.VideoWriter_fourcc(*'XVID'), 15, (width, height))
        threading.Thread(target=self.record).start()


    def stopRecording(self):
        self.is_recording = False
        self.textLabel.config(text='停止录制')
        
    def record(self):
        sct = mss()
        monitor = {'top': int(self.start_y), 'left': int(self.start_x), 'width': int(self.end_x - self.start_x), 'height': int(self.end_y - self.start_y)}
        width = int(self.end_x - self.start_x)
        height = int(self.end_y - self.start_y)
        fps = 16
        frame_duration = 1 / fps

        frame_counter = 0
        last_print_time = time.perf_counter()

        while self.is_recording:
            start_time = time.perf_counter()

            img = sct.grab(monitor)  # use mss to take a screenshot
            img_np = np.array(img)
            img_bgr = cv2.cvtColor(img_np, cv2.COLOR_BGRA2BGR)  # change the color conversion from RGBA to BGRA
            img_bgr_resized = cv2.resize(img_bgr, (width, height))  # resize the image to the desired size
            self.writer.write(img_bgr_resized)

            elapsed_time = time.perf_counter() - start_time
            sleep_time = max(frame_duration - elapsed_time, 0)
            time.sleep(sleep_time)

            frame_counter += 1
            time_since_last_print = time.perf_counter() - last_print_time
            if time_since_last_print >= 1:
                # print(f"FPS: {frame_counter / time_since_last_print}")  # print the actual FPS
                frame_counter = 0
                last_print_time = time.perf_counter()

        self.writer.release()

        
if __name__ == '__main__':
    app = ScreenRecorder()
    app.mainloop()
