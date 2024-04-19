import subprocess

# 运行 nsenter 命令
nsenter_cmd = "nsenter --mount=/host/proc/1/ns/mnt docker exec -i pikafish /app/pikafish"
process = subprocess.Popen(nsenter_cmd, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

# 向容器发送 UCI 命令
def send_command(command):
    print(f"Sending command: {command}")
    process.stdin.write(command + "\n")
    process.stdin.flush()

# 读取容器的响应
def read_response():
    response = ""
    while True:
        line = process.stdout.readline()
        response += line
        if "uciok" in response or "bestmove" in response:
            break
    print(f"Engine response:\n{response}")
    return response

# 初始化引擎
send_command("uci")
read_response()

# 设置棋局状态（FEN表示法）
send_command("position fen rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")

# 让引擎计算最佳下一步
send_command("go depth 10")
response = read_response()

# 提取最佳下一步
best_move = response.split(" ")[1]
print(f"Best move: {best_move}")
