# 看杀
import os
import pandas as pd

class LookKill:
    def __init__(self,qipuPath=os.getcwd()+'/../qipu'):
        self.qipuPath = qipuPath
        self.df = self.readAllCsv(qipuPath)

    def readCsv(self,csvFilename):
        df = pd.read_csv(csvFilename)
            
        ret = pd.DataFrame(columns=['filename','idx','color','fen','bestMoveFen1','step'])

        for i in range(len(df)):
            idx = df['idx'][i]
            fen = df['fen'][i]
            bestMoveFen1 = df['best_move1_fen'][i]
            bestScore1 = df['best_score1'][i]
            color = 'red' if idx % 2 == 1 else 'black'
            if bestScore1 > 9000:
                step = (10000 - bestScore1) / 100
                new_row = pd.DataFrame({
                    'filename': [csvFilename],
                    'idx': [idx],
                    'color': [color],
                    'fen': [fen],
                    'bestMoveFen1': [bestMoveFen1],
                    'step': [step]
                })
                ret = ret.append(new_row, ignore_index=True)
            
        return ret
    
    def readAllCsv(self, path):
        ret = pd.DataFrame(columns=['filename', 'idx', 'color', 'fen', 'bestMoveFen1', 'step'])
        for filename in os.listdir(path):
            if filename.endswith('.csv'):
                csv_path = os.path.join(path, filename)
                df = self.readCsv(csv_path)
                ret = ret.append(df, ignore_index=True)
        return ret

if __name__ == '__main__':
    lookKill = LookKill()
    print(lookKill.df)
