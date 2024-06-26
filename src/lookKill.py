# 看杀
import os
import pandas as pd

class LookKill:
    def __init__(self,qipuPath=os.getcwd()+'/../qipu',isRandom=True):
        self.qipuPath = qipuPath
        self.df = self.readAllCsv(qipuPath)
        self.currentQuestionCount = 0
        if isRandom:
            self.df = self.df.sample(frac=1).reset_index(drop=True)

    def readCsv(self, csvFilename):
        df = pd.read_csv(csvFilename)

        # 使用pandas过滤满足条件的行
        filtered_df = df[df['best_score1'] > 9000]

        ret = pd.DataFrame(columns=['filename', 'idx', 'color', 'fen', 'bestMoveFen1', 'step'])

        for i in range(len(filtered_df)):
            idx = filtered_df.iloc[i]['idx']
            fen = filtered_df.iloc[i]['fen']
            bestMoveFen1 = filtered_df.iloc[i]['best_move1_fen']
            bestScore1 = filtered_df.iloc[i]['best_score1']
            color = 'red' if idx % 2 == 1 else 'black'
            # step = (10000 - bestScore1) / 100
            step = len(bestMoveFen1.split(','))
            new_row = pd.DataFrame({
                'filename': [csvFilename],
                'idx': [idx],
                'color': [color],
                'fen': [fen],
                'bestMoveFen1': [bestMoveFen1],
                'step': [step]
            })
            ret = pd.concat([ret, new_row], ignore_index=True)


        return ret

    
    def readAllCsv(self, path):
        dfs = []  # 创建一个空列表来存储每个CSV文件的DataFrame
        for filename in os.listdir(path):
            if filename.endswith('.csv'):
                csv_path = os.path.join(path, filename)
                df = self.readCsv(csv_path)
                dfs.append(df)  # 将DataFrame添加到列表中
        
        ret = pd.concat(dfs, ignore_index=True)
        # 下面这行为什么在IDE中是不能运行到的？
        return ret

    def getCurrentQuestion(self):
        return self.df.iloc[self.currentQuestionCount]
    
    def nextQuestion(self):
        self.currentQuestionCount += 1
        if self.currentQuestionCount >= len(self.df):
            self.currentQuestionCount = 0
        return self.getCurrentQuestion()
    
    def prevQuestion(self):
        self.currentQuestionCount -= 1
        if self.currentQuestionCount < 0:
            self.currentQuestionCount = len(self.df) - 1
        return self.getCurrentQuestion()

if __name__ == '__main__':
    lookKill = LookKill()
    df = lookKill.df
    print(len(df))

    # 找到df中是否存在fen重复的行
    # print(df[df.duplicated(['fen'], keep=False)])

    print(df[df['step'] == 1])



    # print(df['color'].unique())
    # print(df['step'].unique()) 
