import math
import tkinter as tk

CN_NUM_RED = ['', '一', '二', '三', '四', '五', '六', '七', '八', '九']


class ChessBoard(tk.Canvas):
    def __init__(self, master=None, w=30, **kwargs):
        super().__init__(master, **kwargs)
        self.w = w  # 棋盘格子的大小
        self.flipped = False  # True = 黑方视角(黑方放屏幕下方)

    def draw_board(self, style=1):
        # style=1 早期开发用;style=2 UCI 坐标(a..i / 0..9);style=3 中式
        self.delete('axis')
        # 画棋盘横线
        for i in range(10):
            self.create_line(self.w, self.w + i * self.w, 9 * self.w, self.w + i * self.w)
            if style == 2:
                self.create_text(self.w * 0.4, self.w * (i + 1), text=str(9 - i),
                                 font=('Arial', 10), tags='axis')
        # 画棋盘竖线
        for i in range(9):
            if i == 0 or i == 8:
                self.create_line(self.w + i * self.w, self.w, self.w + i * self.w, 10 * self.w)
            else:
                self.create_line(self.w + i * self.w, self.w, self.w + i * self.w, 5 * self.w)
                self.create_line(self.w + i * self.w, 6 * self.w, self.w + i * self.w, 10 * self.w)

            if style == 1:
                self.create_text(self.w * (i + 1), self.w * 0.4, text=str(i + 1),
                                 font=('Arial', 10), tags='axis')
                self.create_text(self.w * (i + 1), self.w * 10.6, text=str(9 - i),
                                 font=('Arial', 10), tags='axis')
            elif style == 2:
                self.create_text(self.w * (i + 1), self.w * 10.6, text=chr(ord('a') + i),
                                 font=('Arial', 10), tags='axis')
            elif style == 3:
                # 中式标注:屏幕上方 = 黑方列号(阿拉伯 1..9,从左往右)
                #          屏幕下方 = 红方列号(汉字 九..一,从左往右)
                # 翻转视角时红黑互换
                if not self.flipped:
                    topText = str(i + 1)
                    botText = CN_NUM_RED[9 - i]
                else:
                    topText = CN_NUM_RED[i + 1]
                    botText = str(9 - i)
                self.create_text(self.w * (i + 1), self.w * 0.4, text=topText,
                                 font=('Arial', 11), tags='axis')
                self.create_text(self.w * (i + 1), self.w * 10.6, text=botText,
                                 font=('Arial', 11), tags='axis')

        # 画九宫格
        self.create_line(4 * self.w, self.w, 6 * self.w, 3 * self.w)
        self.create_line(4 * self.w, 3 * self.w, 6 * self.w, self.w)
        self.create_line(4 * self.w, 8 * self.w, 6 * self.w, 10 * self.w)
        self.create_line(4 * self.w, 10 * self.w, 6 * self.w, 8 * self.w)



    def uciToXY(self, pos):
        col = ord(pos[0]) - ord('a')
        rank = int(pos[1])
        x = (col + 1) * self.w
        y = (10 - rank) * self.w
        return x, y

    def xyToUci(self, px, py):
        col = round(px / self.w - 1)
        rank = round(10 - py / self.w)
        if not (0 <= col <= 8) or not (0 <= rank <= 9):
            return None
        return f'{chr(ord("a") + col)}{rank}'

    def draw_piece(self, x, y, color, text):
        a = int(self.w*0.9/2)
        if color == '红':
            fillColor = 'white'
            textColor = 'red'
        else:
            fillColor = 'white'
            textColor = 'black'
        self.create_oval(x - a, y - a, x + a, y + a, fill=fillColor, tags='piece')
        self.create_text(x, y, text=text, fill=textColor, font=('Arial', 15, 'bold'), tags='piece')

    def place_piece(self, pos, color, text):
        # Convert FEN position to canvas coordinates
        x, y = self.uciToXY(pos)
        self.draw_piece(x, y, color, text)

    def readFen(self, fen):
        self.delete("piece")
        self.delete("arrow")
        fen_rows = fen.split('/')
        for row_idx, row in enumerate(fen_rows):
            col_idx = 0
            for char in row:
                if char.isdigit():
                    col_idx += int(char)
                else:
                    # FEN 约定:rows[0] 是黑方底线(最上方),rank 9;rows[9] 是红方底线(最下方),rank 0
                    pos = chr(ord('a') + col_idx) + str(9 - row_idx)
                    # FEN 大小写约定:大写=红方,小写=黑方(与标准 UCI 一致)
                    color = '红' if char.isupper() else '黑'
                    
                    text = ''
                    if char.lower() == 'r':
                        text = '车'
                    elif char.lower() == 'n':
                        text = '马'
                    elif char.lower() == 'c':
                        text = '炮'
                    elif char == 'A':
                        text = '仕'
                    elif char == 'a':
                        text = '士'
                    elif char == 'K':
                        text = '帅'
                    elif char == 'k':
                        text = '将'
                    elif char == 'P':
                        text = '兵'
                    elif char == 'p':
                        text = '卒'
                    elif char == 'B':
                        text = '象'
                    elif char == 'b':
                        text = '相'

                    self.place_piece(pos, color, text)
                        
                    col_idx += 1
        
    def draw_arrow(self, pos1, pos2, color,number):
        x1, y1 = self.uciToXY(pos1)
        x2, y2 = self.uciToXY(pos2)

        # Draw arrow
        self.create_line(x1, y1, x2, y2, arrow=tk.LAST, fill=color, width=5, arrowshape=(20, 20, 10), tags='arrow')

        # Calculate the position of the number
        dx, dy = x2 - x1, y2 - y1
        dist = math.sqrt(dx*dx + dy*dy)
        x_number = x2 - dx / dist * self.w / 2
        y_number = y2 - dy / dist * self.w / 2

        # Draw a green circle
        radius = self.w / 5
        self.create_oval(x_number - radius, y_number - radius, x_number + radius, y_number + radius, fill='green', tags='arrow')

        # Draw the number with white text
        self.create_text(x_number, y_number, text=str(number), fill='white', font=('Arial', 10, 'bold'), tags='arrow')

        


class ChessGui(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('棋谱导出')
        self.geometry('300x350')
        self.initUI()

    def initUI(self):
        self.board = ChessBoard(self, width=600, height=600)
        self.board.pack()
        self.board.draw_board(style=2)
        # self.board.place_piece('a0', '红', '车')
        # self.board.place_piece('b0', '黑', '马')
        self.board.readFen('rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C2C4/9/RNBAKABNR')

        # self.board.draw_arrow('h2', 'e2','red', 1)

if __name__ == '__main__':
    app = ChessGui()
    app.mainloop()
