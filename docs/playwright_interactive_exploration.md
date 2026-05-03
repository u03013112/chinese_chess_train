# Playwright 交互式探索天天象棋

> **本文档是天天象棋 Playwright 抓取的唯一权威文档**(2026-05-03 起)。
> 同目录 `web_data_extraction_workflow.md` 的"实战:天天象棋棋谱提取"章节及 `chess_explorer.py` 使用说明**已作废**,那份文档只保留通用方法论部分仍有效。

## 概述

使用 Playwright (有头 Chromium) 直接操作天天象棋 H5 的 Cocos2d-JS 场景，替代老的图像识别管道，从场景树里直接抓 UCI 棋谱数据。

**目标网址**: https://h5login.qqchess.qq.com/

**最后更新**: 2026-05-03 (登录 + 导航 + 单局棋谱读取跑通;内部 API 方案跑通,可完全绕过 UI;29 局批量导入完整贯通到 Pikafish csv,pipeline 已关环)

---

## TL;DR（跑通的事实）

- **引擎**: Cocos2d-JS。`cc` 全局对象可用,场景可通过 `cc.director.getScene()` 遍历。
- **点击方式**: **必须用 `MouseEvent`**(`mousedown` → 80ms → `mouseup` + `click`),**不要用 `TouchEvent`**。桌面 Chromium `ontouchstart=false, maxTouchPoints=0`,Cocos 的 touch 通道根本没挂。
- **坐标公式**:
  ```
  screenX = worldX * scaleX
  screenY = frameSize.height - (worldY * scaleY + viewportRect.y)
  ```
  在 1280×720 视口下实测精确(偏差 <5px,完全在命中区内)。
- **登录 UI 当前形态**: 登录面板 `LoginPanelForLandscape` 直接显示两个 `StartBtn_1`(上=微信、下=QQ),**不需要**先激活 `NodeQRLogin`。点微信按钮会弹出微信 iframe 二维码,用户手机扫码完成 OAuth。
- **无法绕过扫码**: `login_info.json` 里的 token 过期极快(wx token < 1 周,refresh < 1 月),实际每次都要扫。

---

## 交互基础设施

### 坐标/视口实测值 (1280×720 viewport)

| 量 | 值 |
|---|---|
| `canvasSize` (DOM canvas w/h) | 1280 × 720 |
| `designResolution` | 1024 × 768 |
| `frameSize` | 1280 × 720 |
| `viewportRect` | `{x:0, y:-120, w:1280, h:960}` |
| `scaleX` / `scaleY` | 1.25 / 1.25 |
| Canvas 节点 world pos | (512, 384) |
| Canvas DOM rect | `{left:0, top:0, width:1280, height:720}` |

### 核心工具函数（evaluate 片段）

```javascript
// 递归找首个同名节点
function findNodeByName(node, name) {
  if (node.name === name) return node;
  if (node.children) for (const c of node.children) {
    const r = findNodeByName(c, name);
    if (r) return r;
  }
  return null;
}

// 找所有同名节点(多个重名时必用)
function findAllNodes(node, name, out = []) {
  if (node.name === name) out.push(node);
  if (node.children) for (const c of node.children) findAllNodes(c, name, out);
  return out;
}

// Cocos 世界坐标 -> DOM 屏幕坐标(clientX/clientY)
function cocosNodeToScreen(node) {
  const world = node.convertToWorldSpaceAR(cc.v2(0, 0));
  const view = cc.view;
  const frameSize = view.getFrameSize();
  const viewportRect = view.getViewportRect();
  return {
    x: world.x * view.getScaleX(),
    y: frameSize.height - (world.y * view.getScaleY() + viewportRect.y),
    world,
  };
}

// 原生 MouseEvent 点击(桌面 Chromium 唯一可用通道)
async function cocosClick(x, y) {
  const canvas = cc.game.canvas;
  function mk(type) {
    return new MouseEvent(type, {
      bubbles: true, cancelable: true, view: window,
      clientX: x, clientY: y, screenX: x, screenY: y,
      button: 0, buttons: type === 'mousedown' ? 1 : 0,
    });
  }
  canvas.dispatchEvent(mk('mousedown'));
  await new Promise(r => setTimeout(r, 80));
  canvas.dispatchEvent(mk('mouseup'));
  canvas.dispatchEvent(mk('click'));
}
```

### 坐标双重可视化(调试必做)

点前一定要在 Cocos 层和 DOM 层各画一个标记,截图肉眼对齐再点。**本次卡点就是历史上只画 Cocos label 不画 DOM 点,label 的基线偏移 10~15px 让人误以为公式错了。**

```javascript
// (1) Cocos 层:在节点世界坐标画红★
function debugMarkCocos(targetNode, color = cc.Color.RED) {
  const scene = cc.director.getScene();
  const canvas = findNodeByName(scene, 'Canvas');
  canvas.children.filter(c => c.name && c.name.startsWith('DEBUG_')).forEach(c => c.destroy());
  const world = targetNode.convertToWorldSpaceAR(cc.v2(0, 0));
  const local = canvas.convertToNodeSpaceAR(world);
  const m = new cc.Node('DEBUG_MARKER');
  const label = m.addComponent(cc.Label);
  label.string = '★'; label.fontSize = 60; label.lineHeight = 60;
  m.color = color;
  m.setPosition(local.x, local.y);
  canvas.addChild(m, 99999);
}

// (2) DOM 层:在 (x,y) 画绿点,权威对照
function debugMarkDom(x, y) {
  const old = document.getElementById('DOM_DEBUG_DOT');
  if (old) old.remove();
  const d = document.createElement('div');
  d.id = 'DOM_DEBUG_DOT';
  d.style.cssText = `position:fixed;left:${x}px;top:${y}px;width:20px;height:20px;` +
    'margin-left:-10px;margin-top:-10px;background:lime;border:3px solid red;' +
    'border-radius:50%;z-index:999999;pointer-events:none;';
  document.body.appendChild(d);
}

// 清理
function debugClear() {
  const scene = cc.director.getScene();
  const canvas = findNodeByName(scene, 'Canvas');
  if (canvas) canvas.children.filter(c => c.name && c.name.startsWith('DEBUG_')).forEach(c => c.destroy());
  const d = document.getElementById('DOM_DEBUG_DOT');
  if (d) d.remove();
}
```

**判定标准**: DOM 绿点落在目标按钮的图形范围内即算成功。Cocos 红★的偏移是 Label 渲染问题,忽略。

---

## 登录流程(已跑通)

### 场景树(Login 场景,登录面板部分)

```
Login
└── Canvas
    └── SceneFrame_MainLayer / ... / LoginPanelForLandscape
        ├── content
        │   ├── agreement
        │   │   └── check / checkBox   ← 协议勾选
        │   │       ├── on  (active=false)
        │   │       └── off (active=true)
        │   ├── StartBtn_1 (world.y=344)  ← 微信登录 (上)
        │   ├── StartBtn_1 (world.y=292)  ← QQ 登录  (下)
        │   └── Logo / BtnAgePromptEntry / agreement1..4 / ...
        └── NodeQRLogin  (active=false,本 UI 版本未使用)
            └── btnQRWX  (历史残留)
```

**注意两个重名 `StartBtn_1`**。用 `findAllNodes` + 按 `y` 降序取第 0 个才是微信。

### Step 1. 勾选协议

```javascript
const scene = cc.director.getScene();
const checkBox = findNodeByName(scene, 'checkBox');
const pos = cocosNodeToScreen(checkBox);   // 实测 (466, 595)
await cocosClick(pos.x, pos.y);
// 验证: findNodeByName(scene, 'on').active === true
```

### Step 2. 点击微信登录

```javascript
const btns = findAllNodes(scene, 'StartBtn_1');
btns.sort((a, b) => b.y - a.y);            // y 大的在上 = 微信
const pos = cocosNodeToScreen(btns[0]);    // 实测 (640, 410)
await cocosClick(pos.x, pos.y);
```

### Step 3. 等二维码 iframe 出现 → 用户扫码

点击后页面会加载微信 OAuth iframe:

```
https://open.weixin.qq.com/connect/qrconnect?appid=wxa13dcbb181b4fa55&redirect_uri=...
```

用户用手机微信扫码完成授权。二维码过期时 `page.click('iframe')` 刷新。

### Step 4. 轮询登录状态

```javascript
// 轮询直到 true
const LoginModel = fdk.getModel('LoginModel');
LoginModel.isLogined();
```

扫码成功后页面自动跳转,URL 带 `?code=xxx&state=fromWX_xxx`,然后进入主场景。

---

## 登录后的导航链(已跑通)

从主场景一路点到「我的棋谱」列表:

```
确定弹窗(Confirm / BtnOK) → 底部「下棋」tab → 象棋入口
   → 我的棋谱 → 最近对局 tab → MyQipuListScene
```

每一步的做法都是:`findAllNodes` 找目标节点 → `cocosNodeToScreen` 算屏幕坐标 → `cocosClick` 派 MouseEvent。关键节点名按实测记录:

| 节点名 | 作用 |
|---|---|
| `Confirm` / `BtnOK` | 登录后各种弹窗(活动、公告等),直接点掉 |
| 底部 tab「下棋」 | `StartSceneForLandscape` 里的 tab,进象棋大厅 |
| `QipuLibraryScene` → 「最近对局」 | 从棋谱库进用户个人对局列表 |
| `MyQipuListScene` | 目标列表场景,用户所有棋谱在这里 |
| `TopLeftOverMenuButton` | 详情页返回按钮,screen 坐标约 (197, 31) |

---

## 数据抓取方案:读 Cocos 内存(已跑通,当前默认)

### 思路

**不抓网络、不解协议**。天天象棋的列表数据和单局 moves 在客户端进入对应场景时已经从后端拉好并解压到 JS 对象里。我们直接遍历 scene tree 找到承载数据的组件,读它的内部字段即可。

### 列表元数据:`MyQipuListScene`

数据在 `MultiListView` 组件的 `fh[1].dataSource` 上,**不是** `fh[0]`(`fh[0]` 是另一个空 tab)。从根节点走:

```
MyQipuListScene
  /content/contentNode/ScrollView/list/content   ← 有 MultiListView 组件
    组件.fh[1].dataSource
      .Hh          ← Array,当前已加载的 N 条(每页 20)
      .yg          ← 总条数,本账号实测 152
      .Ra / .mb    ← 疑似分页加载方法,待验证
```

**重要**: 该列表是**虚拟滚动**,即便 `Hh.length=20`,场景里实际存在的 `MyQipuListItem` 节点只有 7~8 个(屏幕可见数量)。所以"按渲染 item 坐标循环点击"的思路不可行,必须按 `Hh` 索引驱动。

**每条元数据字段**(选关键的):

| 路径 | 字段 |
|---|---|
| `x.qipuId` | 棋谱 ID |
| `x.createTime` | 时间戳 |
| `x.i2a.kc` | 回合数 |
| `x.i2a.sTitle` | 标题 |
| `x.tib.sRedName` / `sBlackName` | 红黑方昵称 |
| `x.tib.sResult` | 结果字符串 |
| `x.i2a.Rd.val[0/1]` | 双方玩家完整信息(uin、iRankPoints 等) |

### 单局 moves:`QipuGameSceneForLandscape`

点进详情页后,核心组件 **`QipuChessBoardControl`** 位于:

```
QipuGameSceneForLandscape
  /.../Panel_BoardContainer      ← 挂 QipuChessBoardControl 组件
```

**关键字段**:

| 字段 | 含义 |
|---|---|
| `C6a` | qipuId |
| `pB` | 玩家 uin |
| `gmd` / `Msd` / `Krb` | 标题 / 短标题 / 类型 |
| `uTb` | 结果字符串 ("1-0" / "0-1" / "1/2-1/2") |
| `Ny` / `Td` | 起始 FEN(同值,双份冗余) |
| **`RPb`** | **压缩 moves 串**,每 4 字符表示一步 `fx fy tx ty`(都是数字字符) |
| `Wg` | `Array(N)` move 对象。⚠️ 顺序偶尔和 `RPb` 有出入,**以 `RPb` 为权威** |
| `Fic` / `MF` | 初始 board 数组 / 展开的 moves |

### 坐标系 → UCI 转换

`RPb` 的 `fx/fy/tx/ty` 和 `src/tools.py` 的坐标系完全一致:

```
col  = 'abcdefghi'[fx]
rank = 9 - fy
```

前 4 步验证通过:`7747/7242/7967/7062` 对应 炮二平五 / 炮 8 平 5 / 马二进三 / 马 8 进 7 ✅。

### dump 单局 JSON(当前跑通)

```javascript
(() => {
  function safeClass(v){if(!v)return null;if(v.__classname__)return v.__classname__;try{if(v.constructor&&v.constructor.name)return v.constructor.name;}catch(e){}return null;}
  function findAll(node,pred,out=[]){if(pred(node))out.push(node);if(node.children)for(const c of node.children)findAll(c,pred,out);return out;}
  const qn = findAll(cc.director.getScene(), n => n.name && n.name.includes('QipuGameSceneForLandscape') && n.active)[0];
  let qcbc = null;
  (function walk(nd){
    for (const c of (nd._components || [])) if (safeClass(c) === 'QipuChessBoardControl') qcbc = c;
    if (nd.children) for (const c of nd.children) walk(c);
  })(qn);
  const r = qcbc.RPb;
  const moves = [];
  for (let i = 0; i < r.length; i += 4) moves.push([+r[i], +r[i+1], +r[i+2], +r[i+3]]);
  return {
    qipuId: qcbc.C6a, uin: qcbc.pB, title: qcbc.gmd, titleShort: qcbc.Msd,
    type: qcbc.Krb, result: qcbc.uTb, startFen: qcbc.Ny,
    totalSteps: qcbc.Wg.length, rpb: qcbc.RPb, moves,
  };
})()
```

evaluate 返回值直接 `Write` 落盘到 `qipu/raw/<qipuId>.json`。

### JSON → FEN txt

`src/qipu2txt.py`(camelCase,中文注释)实现 `applyMoveToFen` + `jsonToFenList`,把每一步 move 作用到起始 FEN 上,输出每行一个 FEN 的 txt 文件,格式与 `qipu/2024-05-11_*.txt` 一致,可直接喂给 `AnaylizeFenFile.py` 的 Pikafish 分析管道。

首局 `74600159056` 端到端验证通过:smoke test 3 步全对,末局 FEN `3R5/4k4/b7b/9/4R4/8P/9/9/5K3/2BA5`(双车对孤老将)符合 `1-0` 结果 ✅。

---

## 数据抓取方案对比

### 路线 A(当前默认,已跑通):点 UI 进详情页读组件内存

见上一节。慢(每局 ~3 秒),但稳。

### 路线 B(**最优,已验证可行**):调 fdk 内部 API + 事件 hook

**结论先行**: 完全绕开 UI、不进详情页、不抓原生网络包,仅通过 `fdk` 单例的内部方法就能拿到完整 moves。

**通讯背景**: 天天象棋 H5 客户端和后端用**自定义 protobuf over 某种长连**(不是 fetch/XHR/原生 WebSocket)。hook 全局 `fetch/XHR/WebSocket` 抓不到数据流(WS 连接在 hook 装之前就已建立)。但完全不需要抓原生包 —— 游戏代码自身暴露了 model 层 API,调用后把响应广播成 JS 事件。

#### 关键路径

```
fdk.getModel('QipuModel').requestGetQipuInfo(qipuId)   ← 触发请求(有缓存直接回调)
           ↓ 若有本地缓存
fdk.getModel('QipuFileSysModel').showQipuWithCacheFileName(qipuId, 99)
           ↓ 统一入口
QipuModel.CNb(resp)
           ↓ 广播
fdk.Joa.ba('NOTIFY_QIPU_DATA', {
  ContextName: '...',
  param: {
    qipuID, playersInfo, Gba,
    collectDataInfo: {
      lDataID: qipuId,
      iDataType: 13,
      sData: "{...完整详情 JSON...}"   ← moveinfo.movelist 就是压缩 moves 串
    },
    stepNum, jumpAnalyse, izd
  }
})
```

#### 完整 JSON payload 示例(`collectDataInfo.sData` 解析后)

```json
{
  "adddate": "2026-05-03 09:49:15",
  "classinfo": { "sevent": "棋力评测", ... },
  "ecco": "D50",
  "iGameoverReason": 13,
  "moveinfo": {
    "movelist": "77471242796772628979...",   ← 就是 RPb
    "commentv2": { ... },
    ...
  },
  "userinfo": { "redname": "...", "blackname": "...", ... },
  "result": "...",
  ...
}
```

`moveinfo.movelist` 和之前读 `QipuChessBoardControl.RPb` 得到的字符串**完全一致**(每 4 字符一步 `fx fy tx ty`)。

#### 列表 API

```
// 正确的列表接口(源码确认)
fdk.getModel('QipuModel').Xj(iDataType, iPageFlag, iReqNum, iDirID=0)
// opcode 85131, 对应 TRequestGetDataList
// iDataType=13  → 最近对局(Wfb)
// iDataType=20  → Ufb
// iDataType=15  → 目录下对局(nja),需要配合 iDirID
// iDataType=18  → Sfb(疑似分享)
// iDataType=19  → Rfb
// iDataType=14  → M0a
// iDataType=16  → mS
// iDataType=61  → hEb

// 响应在 QipuModel.Xmb 里处理,按 iPageFlag==1 重置对应数组,否则 push
// 广播事件: NOTIFY_QIPU_MY_LIST_UPDATE_INFO(非 NOTIFY_QIPU_DATA)
```

**⚠️ 服务器行为坑(2026-05-03 实测)**:

`iDataType=13`(最近对局列表)的 `iPageFlag` **不是 offset-based 分页**,而是"滑动窗口偏移 1 条":

- `page=1` → 返回 id[0..19](最新 20 条)
- `page=2` → 返回 id[1..20]
- `page=N` → 返回 id[N-1..N+18]

每页 20 条里只有最后 1 条是新的。翻完所有 page 后去重,本账号实测**只能拉到 29 条唯一 qipuId**。字段 `yg=152` 是服务器"累计对局数统计"(包括已删除/归档的),**不代表可回溯 152 局棋谱**。

**正确的全量拉取姿势(待验证)**:

1. 要么接受"只有近 29 局可抓",直接对 29 个 id 走路线 B 详情 API
2. 要么换 `iDataType`(15=目录、20=Ufb、14/16/18/19 等),或换接口 `requestQipuWallDataList` / `requestDailyQipuId`,看是否有能拉更多的通道
3. 要么用 `iDirID`(第 4 参数)分组拉

**不要再信 `yg` 字段表示"可拉取局数"。**

#### 最小端到端脚本(已验证)

```javascript
(() => {
  // 1) Hook 事件广播,拦截 NOTIFY_QIPU_DATA
  if (!fdk.Joa.__baHooked) {
    window.__qipuResults = {};
    const orig = fdk.Joa.ba;
    fdk.Joa.ba = function(eventName, payload) {
      try {
        if (eventName === 'NOTIFY_QIPU_DATA' && payload && payload.param) {
          const p = payload.param;
          const cdi = p.collectDataInfo;
          if (cdi && cdi.sData && cdi.iDataType === 13) {
            // 13 = 单局详情
            window.__qipuResults[cdi.lDataID] = {
              qipuID: p.qipuID,
              playersInfo: p.playersInfo,
              sData: cdi.sData,   // 完整 JSON 字符串
              t: Date.now()
            };
          }
        }
      } catch(e){}
      return orig.apply(this, arguments);
    };
    fdk.Joa.__baHooked = true;
  }
})();

// 2) 批量拉
async function fetchAllQipus(qipuIds) {
  const qm = fdk.getModel('QipuModel');
  for (const id of qipuIds) {
    qm.requestGetQipuInfo(String(id));
    // 等待响应到达 __qipuResults
    const t0 = Date.now();
    while (!window.__qipuResults[id] && Date.now() - t0 < 5000) {
      await new Promise(r => setTimeout(r, 50));
    }
  }
  return window.__qipuResults;
}
```

#### 坑

1. **Hook 时机**: `fdk.Joa.ba` 要在已进入过 `MyQipuListScene`(登录完成、game 模块加载)后才 hook,否则 `fdk.Joa` 可能还没就绪
2. **缓存**: `requestGetQipuInfo` 对已查看过的 qipuId 会命中本地缓存(`QipuFileSysModel`),响应速度 <100ms。**缓存和网络走同一个 `CNb` 入口 + 同一个事件,对我们透明**
3. **Network hook 抓不到原生流量**: 天天象棋用自定义长连,不是浏览器可见的 WebSocket。别浪费时间去抓原生包
4. **不是所有 `NOTIFY_QIPU_DATA` 都是详情**: 需要 `collectDataInfo.iDataType === 13` 过滤

### 路线 C(兜底): 手动抓原生协议

如果路线 B 失效(比如游戏版本升级改了 model 名字),可以反解 JCE/protobuf,自己发 85054 查询包。成本极高,**不推荐**。

---

## 坑位清单(不要再踩)

### 1. TouchEvent 在桌面 Chromium 无效 ⚠️

历史文档说"Cocos 不响应 DOM 事件,必须用 cc.Event.EventTouch"是**错的**。真实情况:

- 桌面 Chromium `ontouchstart=false, maxTouchPoints=0`
- Cocos 的 web input 会挂 touch 或 mouse 监听,桌面只挂 mouse
- 发 TouchEvent 直接被忽略(事件进了 canvas 但 Cocos touch 通道没注册)
- **必须用 `MouseEvent`**:`mousedown` + `mouseup` + `click`(三个都发,`click` 保底)

本次实测:`checkBox` 用 TouchEvent 状态不变,换 MouseEvent 立即 `on=true`。

### 2. Cocos Label 的 `★` 有基线偏移

Label 节点的 anchor 是 (0.5, 0.5),但字形本身在字号框内不居中(有 ascent/descent 偏移)。用 `★` 做 Cocos 层标记会比真实世界坐标偏上 10-15px。**DOM 绿点才是权威对照**。

### 3. 重名节点 `StartBtn_1`

微信登录和 QQ 登录同名,必须用 `findAllNodes` + `y` 排序区分。不要用 `findNodeByName` 取第一个,顺序不稳定。

### 4. Token 过期

`src/login_info.json` 里的 `qqchess_webToken_wx` 有效期约 1 周,refresh token 约 1 月。别指望注入 localStorage 跳过扫码。持久化 `chrome_data/` 目录也只是省一段时间。

### 5. 不要自动关浏览器

非 headless 运行时,不要在脚本里 `browser.close()`。用户需要保留窗口手动扫码/观察。

### 6. 截图目录

- 长期截图: `screenSnapshot/`
- 临时调试(会 gitignore 或事后清): `tmp_screenshots/`

### 7. 系统代理会串到 Playwright

macOS 系统代理(networksetup)开了但端口没服务时,Playwright Chromium 读系统代理 → `net::ERR_PROXY_CONNECTION_FAILED`。症状:`curl` 直连通、Playwright 不通。解法:关代理或启代理。

---

## 实测验证过的完整片段

### 一次性完成「勾协议 + 点微信 + 返回二维码 URL」

```javascript
// playwright evaluate 内执行
(async () => {
  function findNodeByName(node, name) {
    if (node.name === name) return node;
    if (node.children) for (const c of node.children) { const r = findNodeByName(c, name); if (r) return r; }
    return null;
  }
  function findAllNodes(node, name, out = []) {
    if (node.name === name) out.push(node);
    if (node.children) for (const c of node.children) findAllNodes(c, name, out);
    return out;
  }
  function cocosNodeToScreen(node) {
    const w = node.convertToWorldSpaceAR(cc.v2(0, 0));
    const v = cc.view;
    return {
      x: w.x * v.getScaleX(),
      y: v.getFrameSize().height - (w.y * v.getScaleY() + v.getViewportRect().y),
    };
  }
  async function click(x, y) {
    const canvas = cc.game.canvas;
    const mk = t => new MouseEvent(t, {
      bubbles: true, cancelable: true, view: window,
      clientX: x, clientY: y, screenX: x, screenY: y,
      button: 0, buttons: t === 'mousedown' ? 1 : 0,
    });
    canvas.dispatchEvent(mk('mousedown'));
    await new Promise(r => setTimeout(r, 80));
    canvas.dispatchEvent(mk('mouseup'));
    canvas.dispatchEvent(mk('click'));
  }
  const scene = cc.director.getScene();
  // 1. 勾协议
  const cb = findNodeByName(scene, 'checkBox');
  let p = cocosNodeToScreen(cb);
  await click(p.x, p.y);
  await new Promise(r => setTimeout(r, 400));
  // 2. 点微信(上面那个 StartBtn_1)
  const btns = findAllNodes(scene, 'StartBtn_1').sort((a, b) => b.y - a.y);
  p = cocosNodeToScreen(btns[0]);
  await click(p.x, p.y);
  return '点击完成,等二维码 iframe';
})();
```

### 验证登录状态

```javascript
(() => {
  const m = fdk.getModel('LoginModel');
  return { logined: m.isLogined(), logining: m.isLogining() };
})();
```

---

## 端到端现状(2026-05-03)

**完整链路已跑通并落盘**:

```
Playwright MCP
  → evaluate: hook fdk.Joa.ba('NOTIFY_QIPU_DATA')
  → evaluate: for id in qipuIds: qm.requestGetQipuInfo(id)
  → evaluate: 按批回读 window.__qipuResults(单次 evaluate 返回 ≤ 43KB 完整,MCP 日志会截断显示但文件不会)
  → Write: qipu/raw/<qipuId>.json  × 29
src/qipu2txt.py (新增 sData.moveinfo.movelist 分支,兼容老 moves 数组格式)
  → qipu/<qipuId>.txt  × 29
src/AnaylizeFenFile.py (已存在,未修改)
  → qipu/<qipuId>.csv (Pikafish depth=10 MultiPV=20, 单局 smoke 已验证)
```

**关键验证**:
- `74600159056` 新格式解析 vs 老格式 `qipu/raw_legacy/74600159056.old.json` 生成的 106 行 FEN **逐字节完全一致**
- `74457796141` (24 步) 完整过 Pikafish,产出 17KB csv,schema 与历史 csv 一致
- 29 个 qipuId 均为标准开局(`moveinfo.binit == STANDARD_BINIT`);非标准起始局面目前会 `raise ValueError`,需要时再加分支

**已知限制**:
- 这 29 局**全是"人机对战"**(`sData.classinfo.sevent`),对训练价值有限
- 列表 API `QipuModel.Xj(13, p, 20, 0)` 的分页是"滑动窗口 +1",实测仅能回溯 29 条唯一 id;字段 `yg=152` 是统计值,不代表可抓数量
- 真·PVP 棋谱来源待探索:`iDataType=14/15/16/18/19/61`、`requestQipuWallDataList`、`requestDailyQipuId`、或 `iDirID` 分组

**新增/修改的代码**:
- `src/qipu2txt.py` 新增 `parseMovelistStr`、`normalizeQipuJson`、常量 `STANDARD_BINIT` / `STANDARD_START_FEN`
- `src/qipu2txt.py::jsonToFenList` 改为走 `normalizeQipuJson`,同时支持新(`sData`)、老(`startFen` + `moves`)两种 JSON shape

---

## 下一步(若要继续扩量)

1. 要更多棋谱 → 探索 `iDataType` 其他值 / `requestQipuWallDataList` / `iDirID` 分组,找到能拉出 PVP 对局的通道
2. 要批量分析 → `cd src && python3 AnaylizeFenFile.py` 会跳过已存在 csv,顺序跑剩余 28 局(粗估 40–90 分钟)
3. 要非标准开局支持 → 在 `qipu2txt.py::normalizeQipuJson` 中把 `binit` 解析为 FEN(每 2 字符 1 个棋子的 `xy`,共 32 枚),而不是 hard fail

---

## 参考

- [Cocos Creator 官方文档](https://docs.cocos.com/creator/manual/zh/)
- [Playwright Python](https://playwright.dev/python/)
- AGENTS.md § "Scraping 天天象棋"
- 同目录 `web_data_extraction_workflow.md`
