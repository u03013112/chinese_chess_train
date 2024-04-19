import os
import time
import fcntl
import select
import subprocess

class Pikafish:
    def __init__(self):
        nsenter_cmd = "nsenter --mount=/host/proc/1/ns/mnt docker exec -i pikafish /app/pikafish"
        self.process = subprocess.Popen(nsenter_cmd, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        # 设置 stdout 为非阻塞
        flags = fcntl.fcntl(self.process.stdout, fcntl.F_GETFL)
        fcntl.fcntl(self.process.stdout, fcntl.F_SETFL, flags | os.O_NONBLOCK)

    def sendCMD(self, command, callback=None):
        # 清空 stdout
        while True:
            try:
                line = self.process.stdout.readline()
                if not line:
                    break
            except IOError:
                break
        print(f"Sending command: {command}")
        self.process.stdin.write(command + "\n")
        self.process.stdin.flush()
        
        # 有的cmd是没有返回的，就可以不用callback
        if callback:
            response = self._read_response()
            callback(response)
            return response
        return None

    def _read_response(self, timeout=3):
        response = ""
        start_time = time.time()
        while True:
            try:
                line = self.process.stdout.readline()
                if line:
                    response += line
                    
                elif time.time() - start_time > timeout:
                    print("Timeout reached1")
                    break
                else:
                    time.sleep(0.1)  # 如果没有数据可读，等待 0.1 秒
            except IOError:
                if time.time() - start_time > timeout:
                    print("Timeout reached2")
                    break
                else:
                    time.sleep(0.1)  # 如果读取时发生 IOError，等待 0.1 秒
        # print(f"Engine response:\n{response}")
        return response
    
if __name__ == '__main__':
    def my_callback(response):
        print(f"Callback received response: {response}")

    pikafish = Pikafish()
    time.sleep(1)
    # 使用回调函数
    pikafish.sendCMD("uci", my_callback)

    # 不使用回调函数
    # response = pikafish.sendCMD("position fen rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")
    # print(f"Received response: {response}")
