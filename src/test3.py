import easyocr

chess_pieces = ["車", "馬", "象", "仕", "將", "砲", "兵"]
chess_pieces_black = ["車", "馬", "相", "士", "帥", "炮", "卒"]

allowlist = list(set(chess_pieces + chess_pieces_black))

reader = easyocr.Reader(['ch_tra', 'en'])
# reader = easyocr.Reader(['ch_sim', 'en'])
# reader = easyocr.Reader(['ch_tra'])
# result = reader.readtext('/Users/u03013112/Downloads/che.png',allowlist=allowlist)
result = reader.readtext('/Users/u03013112/Downloads/cc.png',allowlist=allowlist,min_size=5)

print(result)