# Pikafish

https://github.com/official-pikafish/Pikafish

Pikafish是目前比较流行的一个象棋AI引擎，它是一个开源项目，支持UCI协议。

## 有关UCI协议

UCI（Universal Chess Interface）是一种通用的象棋游戏接口协议，主要用于象棋软件和象棋引擎之间的通信。然而，UCI协议主要是为国际象棋设计的，对于中国象棋并不完全适用。

中国象棋的UCI协议可能需要进行一些修改和扩展，以适应中国象棋的特殊规则和情况。例如，中国象棋的棋盘布局、棋子的移动规则、将军和将死的判断等都与国际象棋有所不同，这些都需要在UCI协议中进行特殊处理。

目前，已经有一些中国象棋软件和引擎开始支持UCI协议，但由于中国象棋的复杂性，这些软件和引擎的实现可能会有所不同，可能需要根据具体的软件和引擎进行适当的调整和优化。

https://github.com/official-pikafish/Pikafish/wiki/UCI-&-Commands

## 使用Pikafish

pikafish放到docker里，方便部署。
其实我没有自己编译，而是采用了hub.docker.com上的镜像leetun2k2/pikafish。
这玩意也不涉及到什么涉密、敏感信息。我看到他的版本非常新，所以直接用了。

作为命令行UCI，他是用命令行的标准输入和标准输出来进行通信的。

范例：
```shell
Pikafish dev-20240411-nogit by the Pikafish developers (see AUTHORS file)
uci
id name Pikafish dev-20240411-nogit
id author the Pikafish developers (see AUTHORS file)

option name Debug Log File type string default
option name Threads type spin default 1 min 1 max 1024
option name Hash type spin default 16 min 1 max 33554432
option name Clear Hash type button
option name Ponder type check default false
option name MultiPV type spin default 1 min 1 max 128
option name Move Overhead type spin default 10 min 0 max 5000
option name nodestime type spin default 0 min 0 max 10000
option name UCI_ShowWDL type check default false
option name EvalFile type string default pikafish.nnue
uciok
position startpos
position fen rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - - 0 1
position fen rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - - 0 1 moves h2e2
go depth 10
info string NNUE evaluation using pikafish.nnue
info depth 1 seldepth 7 multipv 1 score cp -26 nodes 177 nps 35400 hashfull 0 tbhits 0 time 5 pv b9c7
info depth 2 seldepth 3 multipv 1 score cp -24 nodes 256 nps 42666 hashfull 0 tbhits 0 time 6 pv h9g7
info depth 3 seldepth 3 multipv 1 score cp -24 nodes 302 nps 50333 hashfull 0 tbhits 0 time 6 pv h9g7
info depth 4 seldepth 3 multipv 1 score cp -10 nodes 351 nps 58500 hashfull 0 tbhits 0 time 6 pv h9g7
info depth 5 seldepth 4 multipv 1 score cp -5 nodes 405 nps 67500 hashfull 0 tbhits 0 time 6 pv h9g7
info depth 6 seldepth 4 multipv 1 score cp 17 nodes 524 nps 74857 hashfull 0 tbhits 0 time 7 pv h9g7 e2f2
info depth 7 seldepth 8 multipv 1 score cp 1 nodes 2764 nps 120173 hashfull 0 tbhits 0 time 23 pv h9g7 h0g2 g6g5 c3c4 i9h9 i0h0
info depth 8 seldepth 14 multipv 1 score cp -19 nodes 8088 nps 183818 hashfull 3 tbhits 0 time 44 pv h9g7 h0g2 g6g5 i0h0 i9h9 h0h4 d9e8 g3g4 g5g4 h4g4
info depth 9 seldepth 14 multipv 1 score cp -35 nodes 15908 nps 230550 hashfull 5 tbhits 0 time 69 pv h9g7 g3g4 i9h9 h0g2 h7i7 b0c2 b9c7
info depth 10 seldepth 14 multipv 1 score cp -39 nodes 23036 nps 274238 hashfull 6 tbhits 0 time 84 pv h9g7 h0g2 b9c7 i0h0 i9h9
bestmove h9g7 ponder h0g2
```

这是一个典型的中国象棋UCI引擎的输出。让我们来解析一下这个输出：

1. `uci`：这是你发送给引擎的命令，要求引擎使用UCI协议。

2. `id name Pikafish dev-20240411-nogit`：这是引擎的名称。

3. `id author the Pikafish developers (see AUTHORS file)`：这是引擎的作者信息。

4. `option name ...`：这些是引擎的配置选项，你可以通过这些选项来调整引擎的行为。

5. `uciok`：这是引擎对`uci`命令的响应，表示引擎已经准备好并进入UCI模式。

6. `position startpos`：这是你发送给引擎的命令，要求引擎从标准的初始位置开始。

7. `position fen ...`：这是你发送给引擎的命令，要求引擎从特定的棋盘位置开始。

8. `go depth 10`：这是你发送给引擎的命令，要求引擎计算深度为10的最佳走法。

9. `info depth ...`：这些是引擎在计算过程中的输出，包括当前的搜索深度、评估的分数、已经搜索的节点数等信息。

10. `bestmove h9g7 ponder h0g2`：这是引擎的最终输出，表示引擎认为最佳的走法是从h9到g7，然后预计对手可能会从h0走到g2。

总的来说，这个输出显示了引擎的计算过程和结果，可以帮助你理解引擎是如何工作的，以及引擎认为的最佳走法是什么。

## 总结

暂时没有搞明白引擎的所有功能，但是大致可以用起来了。
比如可以通过
```shell
setoption name MultiPV value 10
```
来设置多PV搜索，这样引擎会返回多个最佳走法，而不仅仅是一个。这个值可以是设的比较大，比如30，这样来对我的各种走法进行评分。如果我的走法仍旧不在引擎的最佳走法中，那么就说明我的走法有问题。

另外，go depth 命令用来进行深度搜索。这里不需要太考虑人的理解，既然决定要学习软件招数，那就直接至少深度10开始搜索。
```shell
go depth 10
```

棋盘开始的命令是
```shell
position startpos
```

另外，和中国象棋棋谱差异比较明显的是，UCI是沿用国际象棋的方式，用白方（红方）为下方，黑方为上方。左下角为坐标原点a1。向右为b1，c1，d1，e1，f1，g1，h1。向上为a2，a3，a4，a5，a6，a7，a8，a9。这个和中国象棋的坐标系是不一样的。所以在使用UCI的时候，需要注意这个坐标系的转换。注意，整张棋盘都用这一个坐标系，黑方也是用这个坐标系，并不颠倒。

暂未完全搞明白的部分
棋子分布是按照下面的格式：
rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - - 0 1
大写是黑色
w是该白色走了，后面的- - 好像是国际象棋的升变和将军的标志，暂时不用管。0 1 代表步数，国际象棋好想有规则和步数有关。中国象棋不确认给错步数是否会有问题。
