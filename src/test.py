# 读取之前的错误fen文件，改成正确的fen文件

def fixFen(filename, outputFilename):
    # 按行读取文件
    # 读到的每一行，都是一个fen，类似这样的：
    # rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR
    # 先用‘/’拆分，再倒序，再用‘/’连接起来
    # 然后目前大写的字母，改成小写的字母；小写的字母，改成大写的字母
    # 最后，写入到新的文件中
    with open(filename, 'r') as f, open(outputFilename, 'w') as out:
        for line in f:
            # 去除行尾的换行符
            line = line.strip()
            # 使用'/'拆分行
            parts = line.split('/')
            # 倒序
            parts.reverse()
            # 使用'/'连接起来
            new_line = '/'.join(parts)
            # 大写字母改成小写字母，小写字母改成大写字母
            new_line = new_line.swapcase()
            # 写入到新的文件中
            out.write(new_line + '\n')

if __name__ == '__main__':
    fixFen('../qipu/20240427230906.txt', '../qipu/20240427230906fen.txt')