import tkinter as tk
from lookKill import LookKill
from ChessBoard import ChessBoard

class LookKillUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('自我训练之看杀')
        self.geometry('500x420')
        self.lookKill = LookKill()
        self.initUI()

    def initUI(self):
        self.btnPrev = tk.Button(self, text='上一题', command=self.prevQuestion)
        self.btnPrev.grid(row=0, column=0, pady=5)

        self.btnNext = tk.Button(self, text='下一题', command=self.nextQuestion)
        self.btnNext.grid(row=1, column=0, pady=5)

        self.btnBest1 = tk.Button(self, text='看答案', command=self.showAnswer)
        self.btnBest1.grid(row=2, column=0, pady=5)

        self.btnBest1 = tk.Button(self, text='隐藏答案', command=self.hideAnswer)
        self.btnBest1.grid(row=3, column=0, pady=5)

        self.textLabel = tk.Text(self, wrap=tk.WORD, height=4,width=25)
        self.textLabel.grid(row=4, column=0)
        self.textLabel.tag_configure('red', foreground='red')
        self.textLabel.tag_configure('black', foreground='black')
        self.textLabel.tag_configure('blue', foreground='blue')
        self.textLabel.config(state=tk.DISABLED)

        self.chessBoard = ChessBoard(self, width=300, height=350)
        self.chessBoard.draw_board(style=2)
        self.chessBoard.grid(row=0, column=1, rowspan=8, padx=20)

        # 初始化看杀模式
        question = self.lookKill.getCurrentQuestion()
        self.chessBoard.readFen(question['fen'])
        self.updateText()

    def updateText(self):
        self.textLabel.config(state=tk.NORMAL)
        self.textLabel.delete('1.0', tk.END)

        question = self.lookKill.getCurrentQuestion()
        color = question['color']
        colorZ = '红' if color == 'red' else '黑'
        step = int(question['step'])
        self.textLabel.insert(tk.END, f'{colorZ}方', color)
        self.textLabel.insert(tk.END, f' {step}步杀\n', 'blue')

        totalQuestion = len(self.lookKill.df)
        currentQuestion = self.lookKill.currentQuestionCount + 1
        self.textLabel.insert(tk.END, f'第{currentQuestion}/{totalQuestion}题\n', 'blue')

    def prevQuestion(self):
        question = self.lookKill.prevQuestion()
        self.chessBoard.readFen(question['fen'])
        self.updateText()

    def nextQuestion(self):
        question = self.lookKill.nextQuestion()
        self.chessBoard.readFen(question['fen'])
        self.updateText()

    def showAnswer(self):
        question = self.lookKill.getCurrentQuestion()
        color = question['color']
        bestMoveFen1 = question['bestMoveFen1']
        moves = bestMoveFen1.split(',')
        for i, move in enumerate(moves):
            start, end = move[:2], move[2:]
            if i % 2 == 0:
                color2 = color
            else:
                color2 = 'red' if color == 'black' else 'black'

            self.chessBoard.draw_arrow(start, end, color2, i+1)

    def hideAnswer(self):
        question = self.lookKill.getCurrentQuestion()
        self.chessBoard.readFen(question['fen'])

if __name__ == '__main__':
    app = LookKillUI()
    app.mainloop()
