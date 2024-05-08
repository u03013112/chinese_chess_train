import os
import time
import fcntl
import select
import subprocess

class Pikafish:
    def __init__(self,cmd = "nsenter --mount=/host/proc/1/ns/mnt docker exec -i pikafish /app/pikafish"):
        self.process = subprocess.Popen(cmd, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
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

    def sendCMDSync(self, command, needResponse=False):
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
        if needResponse:
            response = self._read_response(timeout=5)
            return response
        return None
    
    def _read_response(self, timeout=3):
        response = ""
        while True:
            readable, _, _ = select.select([self.process.stdout], [], [], timeout)
            if readable:
                output = self.process.stdout.read()
                if output:
                    response += output
                else:
                    break
            else:
                break

        return response

if __name__ == '__main__':
    def my_callback(response):
        print(f"Callback received response: {response}")

    pikafish = Pikafish()
    time.sleep(1)
    # 使用回调函数
    pikafish.sendCMD("uci", my_callback)

    # 不使用回调函数
    # response = pikafish.sendCMD("position fen rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w KQkq - 0 1")
    # print(f"Received response: {response}")

    pikafish.sendCMD('setoption name MultiPV value 10')
    pikafish.sendCMD('position startpos')
    pikafish.sendCMD('position fen rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR b - - 10 10')
    pikafish.sendCMD('go depth 10', my_callback)
