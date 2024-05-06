import math
import tkinter as tk

class ChessBoard(tk.Canvas):
    def __init__(self, master=None, w=30, **kwargs):
        super().__init__(master, **kwargs)
        self.w = w  # 棋盘格子的大小
        
    def draw_board(self, style=1):
        # 画棋盘
        for i in range(10):
            self.create_line(self.w, self.w + i * self.w, 9 * self.w, self.w + i * self.w)
            if style == 2:
                self.create_text(self.w * 0.4, self.w * (i + 1), text=str(9-i), font=('Arial', 10))
        for i in range(9):
            if i == 0 or i == 8:  # 画边界线
                self.create_line(self.w + i * self.w, self.w, self.w + i * self.w, 10 * self.w)
            else:  # 画楚河汉界中间没有竖线
                self.create_line(self.w + i * self.w, self.w, self.w + i * self.w, 5 * self.w)
                self.create_line(self.w + i * self.w, 6 * self.w, self.w + i * self.w, 10 * self.w)

            # 添加坐标
            if style == 1:
                self.create_text(self.w * (i + 1), self.w * 0.4, text=str(i + 1), font=('Arial', 10))
                self.create_text(self.w * (i + 1), self.w * 10.6, text=str(9 - i), font=('Arial', 10))
            elif style == 2:
                self.create_text(self.w * (i + 1), self.w * 10.6, text=chr(ord('a') + i), font=('Arial', 10))
                

        # 画九宫格
        self.create_line(4 * self.w, self.w, 6 * self.w, 3 * self.w)
        self.create_line(4 * self.w, 3 * self.w, 6 * self.w, self.w)
        self.create_line(4 * self.w, 8 * self.w, 6 * self.w, 10 * self.w)
        self.create_line(4 * self.w, 10 * self.w, 6 * self.w, 8 * self.w)



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
        x = (ord(pos[0]) - ord('a') + 1) * self.w
        y = (10 - int(pos[1])) * self.w
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
                    pos = chr(ord('a') + col_idx) + str(row_idx)
                    color = '黑' if char.isupper() else '红'
                    
                    text = ''
                    if char.lower() == 'r':
                        text = '车'
                    elif char.lower() == 'n':
                        text = '马'
                    elif char.lower() == 'c':
                        text = '炮'
                    elif char == 'a':
                        text = '仕'
                    elif char == 'A':
                        text = '士'
                    elif char == 'k':
                        text = '帅'
                    elif char == 'K':
                        text = '将'
                    elif char == 'p':
                        text = '兵'
                    elif char == 'P':
                        text = '卒'
                    elif char == 'b':
                        text = '象'
                    elif char == 'B':
                        text = '相'

                    self.place_piece(pos, color, text)
                        
                    col_idx += 1
        
    def draw_arrow(self, pos1, pos2, color,number):
        # Convert FEN positions to canvas coordinates
        x1 = (ord(pos1[0]) - ord('a') + 1) * self.w
        y1 = (10 - int(pos1[1])) * self.w
        x2 = (ord(pos2[0]) - ord('a') + 1) * self.w
        y2 = (10 - int(pos2[1])) * self.w

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
        # self.board.readFen('rnbakabnr/9/1c2c4/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR')

        # self.board.draw_arrow('h2', 'e2','red', 1)

if __name__ == '__main__':
    app = ChessGui()
    app.mainloop()
