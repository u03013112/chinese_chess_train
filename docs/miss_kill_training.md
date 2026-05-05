# missKill 看杀训练 - 进度与待办

## 本次完成(2026-05-04)

### 目标
把"训练系统识别不了某些能杀的招"的问题解决:Pikafish 默认 MultiPV=20,老 CSV 只存 top3 PV,很多真正能杀的走法(比如 `b9d9` 在 depth=16 下排第 13)被截断。

### 方案(用户定)
不走"UI 临时调 Pikafish"路线。**在分析时把所有 score ≥ 9000 的 PV 全部落盘**,并沿每条 PV 展开每一步的中间局面,把中间局面也作为独立题目。红黑双方的每一步都存;不对中间 FEN 重新跑 Pikafish(直接从 PV 里抽下一步)。

### 最终决策清单

| 决策点 | 选择 |
|---|---|
| CSV schema | `kill_moves_json` 单列 JSON(向后兼容老的 `best_moveN`) |
| MultiPV | 保持 20 |
| PV 展开粒度 | 每条 PV 独立展开,红黑双方每一步都存 |
| 同 FEN 聚合 | 多条 PV 覆盖同一 FEN 时,取所有 killMove 的并集(同 move 保留最高 score) |
| 中间 FEN 是否再跑 Pikafish | 不跑,直接从 PV 抽 |
| KILL_THRESHOLD | 从 `> 9000` 改为 `>= 9000` |
| 展开结果存储 | 每局多一个 `qipu/<qipuId>.pv.json` |
| 老 CSV | 全部重跑(先试 5 局验收) |

### 代码改动

- **`src/tools.py`** — 新增 `applyMove / expandFenRow / compressFenRow`(跨模块复用)
- **`src/AnaylizeFenFile.py`** — 新增 `kill_moves_json` 列;`expandPvIntoKillMap` / `dedupeKillMap` 沿 PV 展开中间 FEN,写入 `.pv.json`;`analyzeFenFile` 多一个 `output_pv_json` 参数
- **`src/missKill.py`** — `killPvsOf` 优先读新列,fallback 老列;`buildQuestionBank` 第二轮加载 `.pv.json` 的中间局面,同 FEN 去重;阈值 `>= 9000`;新辅助 `sideOfPvEntry` 从 UCI 起点格的棋子大小写推断执子方
- **`src/missKillUI.py`** — 删除本地 `applyMove/expandRow/compressRow`,统一用 `tools.applyMove` / `tools.expandFenRow`
- **`src/batchAnalyze5.py`** — 一次性脚本,只跑 5 局样本

### 5 局试跑结果

| qipu | 步数 | 耗时 |
|---|---|---|
| 73760308467 | 20 | 100s |
| 73760594457 | 18 | 90s |
| 73761161761 | 18 | 90s |
| 73767038546 | 22 | 111s |
| 73843862420 | 60 | 307s |
| **合计** | **138** | **11.6 min** |

- 题库总数:194 → **420**(新增 226 道展开题)
- 对 `73843862420.csv#55` 的 b9d9 验证 PASS:作为独立 11 步杀题进入 bank,FEN = `1R1ckab2/9/2Nab4/p1p5p/4r4/2P6/P2R5/4C4/9/2BAKA3`,killMove=`b9d9`,score=9300
- 老 CSV 的 fallback 路径 OK(读 top3)

### 时间估算(剩余 116 局批跑)

- 按 138 步 / 11.6 min ≈ **5 秒/步**
- 116 局平均 25 步 → 约 **4 小时**(保守估计 6 小时)
- 建议:开后台 `batchAnalyze.py`,晚上挂

### 文件清单

- 重跑过:`qipu/{73760308467,73760594457,73761161761,73767038546,73843862420}.{csv,pv.json}`
- 日志:`qipu/batchAnalyze5.log`
- 老格式未重跑:40 个老 CSV(从 2024-05-11 到 74457796141)
- 未分析:116 个 txt

---

## 待办(未做,不着急)

### 1. 黑方杀题要上下反转棋盘
**现状**:`buildQuestionBank` 里红黑双方的中间局面都作为题,UI 里黑方视角的题目仍然把红方画在屏幕下方,用户要"反着想",体验差。
**需求**:当 `q['side'] == 'black'` 时,UI 应把**黑方画在屏幕下方**(翻转棋盘视角)。
**涉及改动**:
- `src/ChessBoard.py::readFen` / `draw_board` 加"视角"参数,或 UI 层做坐标转换
- `src/missKillUI.py`:点击坐标 `posFromEvent` 要按当前视角翻转(`fx = 8 - fx`, `ucirank = 9 - ucirank`)
- `drawHintArrow` / `draw_arrow` 也要翻转
- `highlightSquare` 同理
**风险点**:ChessBoard 组件原本就有 fen 渲染约定的历史 bug(见 README),动视角会再次碰这块。

### 2. 棋盘边上的坐标标注改成中国象棋习惯
**现状**:用的国际象棋字母+数字(`a..i` / `0..9`,见截图底部 `a b c d ... i` 和左侧 `0..9`)。
**需求**:按中国象棋习惯标注:
- 红方视角:红方底线列号 **九 八 七 六 五 四 三 二 一**(从左到右),黑方顶线 **1 2 3 4 5 6 7 8 9**(从左到右)
- 行号不标(中国象棋不说"第几行")
- 黑方视角反过来
**涉及改动**:`src/ChessBoard.py::draw_board` 里画刻度的部分全部重写
**注意**:中国象棋"进/退/平"的记谱与列号相关,红方列号从右往左数一到九,黑方用阿拉伯数字 1-9 从左往右——这是本项目 `lastFenAndMove2Qp` 里已经实现的约定。

### 3. 不是所有的杀都支持(截图案例)
**现状**:`20240427230906fen.csv#53`,红方 3 步杀,UI 杀手集合只给 `c8e8 / c5e7 / g7g9`(来自老 top3),用户点"车七退二"(`h9h7`)被判错。
**原因**:老 CSV 没有 `kill_moves_json` 列,fallback 只能读 top3;即便 `h9h7` 在 PV #4~#20 里且 score ≥ 9000,也收不到。
**解法**:把所有老 CSV 重跑一遍。
**候选**:
- 方案 A:全部 150 个 txt(40 老 csv + 116 新 txt)全量重跑一次,一刀切。**推荐**,一劳永逸。
- 方案 B:只把 40 个老 csv 对应的 txt 删 csv 重跑,剩下 116 个按现状先跑。
**时间**:方案 A ≈ 12~15 小时;方案 B ≈ 4~5 小时(老 csv)+ 后续分批。
**决策**:等用户验收完本轮 5 局再定。

### 4. "N 步杀"难度是否拆分
**现状**:展开题把 1 条 3 步 PV 拆成 3 条题(3 步、2 步、1 步),分别进不同难度桶。
- 好处:每一步都有训练,"看到杀的临门一脚"也能练
- 坏处:同一根 PV 被切成 3 题,数据冗余;3 步难度桶里会混进原本展开自 5 步 PV 中间第 3 步位置的"3 步杀",这些和"原始根 FEN 就是 3 步杀"在训练意义上不等价
**两种选择**:
- A. 保持现状(拆分)
- B. 难度固定:3 步难度只收 **根 FEN 就是 3 步杀**(PV 展开的中间局面不算)。更干净,但题库量小,训练可能单调。
- C. 折衷:给展开题加 tag,UI 难度桶可选"仅原始根"或"含展开"
**决策**:等用户体验几轮后说。

---

## 2026-05-05 本轮推进

按 **4 → 3 → 2 → 1** 顺序做。

### 待办 4(难度纯化) ✔
- `missKillUI.py` 的难度从"≤N 步"改为"精确 ==N 步"。
- 新增难度档 1 步杀、9 步杀。
- 新增 **来源筛选** Combobox:`仅根局面 / 含展开 / 仅展开`,默认"仅根局面"。
- `applyDifficulty` 改为 `exactSteps + sourceFilter` 双过滤。
- 筛选组合数据:3 步+仅根=29、3 步+含展开=60、全部+全部=420。

### 待办 3(中式坐标) ✔
- `ChessBoard.py` 新增 `style=3`:顶部黑方列号(阿拉伯 1..9 从左往右),底部红方列号(汉字 九..一 从左往右)。
- 翻转视角时红黑自动互换。
- `draw_board` 开头 `self.delete('axis')`,所有 `create_text` 加 `tags='axis'`,支持重绘不叠加。
- `missKillUI.py` 入口改成 `draw_board(style=3)`。

### 待办 2(黑方视角翻转) ✖ **阻塞 — 已回滚**

**过程**:
- 初版尝试用标准 UCI 语义(rank 0=红方底线=屏幕下方)写 `uciToXY / xyToUci`,并在 `loadQuestion` 根据 `q['side']` 设 `flipped`。
- 测试暴露**根本矛盾**:
  - FEN 数据本身是标准 UCI(`rows[0]` 小写 b/a/k = 黑方底线 = rank 9)
  - 但 `ChessBoard.readFen` 历史上把 `row_idx` **直接当 rank**(即认为 `row_idx==rank`),配老 `place_piece` 的 `y=(rank+1)*w`,等于把"数据 rank 9 画到屏幕 rank 9 对应 y=10w 下方",但实际感受上"黑方(rows[0])画到上方、红方(rows[9])画到下方"— 这其实就是**渲染正确**(黑上红下),只是变量语义是拧的(ranks 在代码里和 UCI 标准反)。
  - 这套拧巴的语义渗透整个项目:`tools.getMove / pieceAt / hasOwnPieceAt / tools.applyMove` 都假设 `row_idx==rank`。
- 改 `uciToXY` 为标准 UCI → 渲染位置翻了(红方跑到上方)→ 只修 `readFen` 又导致 `hasOwnPieceAt` 等全体 mismatch → 级联 bug。
- **决策**:回滚到项目既有语义(`y=(rank+1)*w` 且 `row_idx==rank`),**不实现翻转功能**。style=3 顶部始终是黑方列号、底部是红方列号,固定视角。
- 真正实现黑方翻转需要:把全项目的 "row_idx==rank" 语义重构为标准 UCI(`rank = 9 - row_idx`),改 `tools.py / ChessBoard / AnaylizeFenFile / missKill / missKillUI / history.py` 等,scope 大,留作独立任务。

**本轮产物**:
- `ChessBoard.py` 加 `uciToXY / xyToUci` 集中坐标换算(项目语义不变,语义是 `y=(rank+1)*w`),顺便修复 `draw_arrow` 原 `y=(10-rank)*w` vs `place_piece` 原 `y=(rank+1)*w` 的历史不一致。
- `missKillUI.py` 三处坐标换算改走新方法,行为与改前等价但代码更紧凑。
- `self.flipped` 变量保留但**无效**,style=3 的 `flipped` 分支**死代码**,留给后续重构。

### 待办 1(重跑老 CSV) — 进行中
- 用户决定先跑 5 盘看效果。
- `src/batchAnalyze5b.py` 目标:`20240427230906fen / 2024-05-11_21-03-44 / 73753676038 / 73756200504 / 73872354067`
  - 必含截图案例 `20240427230906fen`(验证车七退二 `h9h7` 是否进 killMoveSet)
  - 其它 4 盘覆盖老命名 + 天天象棋 ID 两种格式
- 5 局总 404 行,预估 20 分钟;日志 `qipu/batchAnalyze5b.log`。

---

## 后续待办(未决)

1. **剩余 40 老 CSV + 116 未分析 txt 全量重跑**:~12~15 小时,挂夜里。
2. **11 步杀"看答案"时 11 条箭头太乱**:仍未处理,体验观察后再定。
3. **`sortBank` 是否把展开题打散穿插**:用户体验后再说。
4. **UI Canvas 宽度是否需要调**:汉字比阿拉伯数字宽,目测后按需调整 `w=32`。
