# 网页数据提取工作流

> ## ⚠️ 部分章节已作废（2026-05-03）
>
> 本文当初作为"通用方法论 + 天天象棋实战"合一写成。实战部分已在 2026-05-03 全面重做,**凡是涉及天天象棋登录、Cocos 点击、棋谱抓取的操作细节,一律以 [`playwright_interactive_exploration.md`](./playwright_interactive_exploration.md) 为准。**
>
> **本文仍然有效的部分**(通用方法论,可复用到其他网站):
> - § 核心需求 / 技术选型对比(方案 A/B/C/D 比较)
> - § 通用化:适配其他网站(React/Vue/Unity/Phaser 探测)
> - § 最佳实践 / 故障排查 / 扩展应用(与具体网站无关的部分)
>
> **本文已作废的部分**(与新文档冲突,见章节内标注):
> - § 实战:天天象棋棋谱提取 → 作废,用新文档
> - 推荐使用 `chess_explorer.py` 的叙述 → 该脚本实际未跑通,已废弃
> - 触摸事件相关片段(本文未直接提,但 §"Cocos 场景树" 历史结论"DOM 事件不被处理"是错的,桌面 Chromium 必须用 `MouseEvent`)
>
> 新文档 `playwright_interactive_exploration.md` 已包含:
> - 实测坐标转换公式 + 双重可视化调试法
> - `MouseEvent` 点击(替代 `TouchEvent`)
> - 当前登录 UI 真实结构(`StartBtn_1` 重名 + y 排序区分微信/QQ)
> - Token 过期、系统代理冲突、Label 基线偏移等踩过的坑

---

## 项目背景

在使用天天象棋等网页应用时，经常遇到官方不提供数据导出功能的情况。例如：
- 棋谱导出
- 对局历史记录
- 统计数据

本文档记录了一套通用的**AI 驱动的网页数据逆向工程工作流**，适用于各类网页数据提取需求。

---

## 核心需求

1. **自然语言驱动** - 通过与 Claude Code 对话，自动分析网页结构
2. **灵活的数据定位** - 支持 JavaScript 执行、DOM 查询、网络抓包等多种方式
3. **支持人工介入** - 在登录、验证码等环节可以人工操作
4. **可复用的工作流** - 形成标准化流程，适用于各类网站
5. **自动生成脚本** - 最终输出油猴插件或 Python 脚本，方便长期使用

---

## 技术选型对比

### 方案A：纯浏览器控制台 ⭐️⭐️⭐️

**适用场景：** 快速验证、一次性使用

**优点：**
- 无需配置，立即可用
- 直接在开发者工具中执行
- 结果可以用 `copy()` 复制或下载

**缺点：**
- 每次都要手动复制粘贴代码
- 输出过多时不便查看
- 不适合迭代调试

**工作流：**
```javascript
// 在控制台运行
(function() {
    // 数据提取代码
    let data = extractData();
    copy(data); // 或下载
})();
```

---

### 方案B：Chrome 远程调试 + Python ⭐️⭐️

**适用场景：** 需要批量处理、自动化

**优点：**
- Python 脚本可复用
- 支持批量操作
- 可以集成到工作流中

**缺点：**
- 需要用特殊方式启动 Chrome（`--remote-debugging-port`）
- 不能使用正常工作的 Chrome
- 配置相对复杂

**工作流：**
```bash
# 1. 启动调试模式 Chrome
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --remote-debugging-port=9222

# 2. 运行 Python 脚本
python extract_data.py
```

---

### 方案C：Playwright 交互式探索 ⭐️⭐️⭐️⭐️⭐️ **推荐**

**适用场景：** AI 驱动的迭代探索，最终生成脚本

**优点：**
- ✅ 支持人工登录、操作
- ✅ 保存登录状态，下次自动登录
- ✅ AI 可以迭代执行 JS 并查看结果
- ✅ 交互式选择要提取的数据
- ✅ 不影响正常使用的 Chrome
- ✅ 跨平台（macOS/Windows/Linux）
- ✅ 可以自动识别页面框架（Cocos/React/Vue）

**缺点：**
- 需要安装 Playwright
- 首次配置稍复杂

**工作流：**
```bash
# 1. 安装依赖（一次性）
pip install playwright
playwright install chromium

# 2. 运行交互式探索脚本
python chess_explorer.py

# 3. 人工登录、进入目标页面
# 4. 脚本自动分析、提取数据
# 5. 选择保存需要的数据
```

---

### 方案D：油猴脚本 ⭐️⭐️⭐️⭐️

**适用场景：** 长期频繁使用，追求最优雅体验

**优点：**
- 安装后永久可用
- 直接在目标页面上添加功能按钮
- 不需要额外工具
- 可以自动执行（监听页面加载）

**缺点：**
- 需要先探索出数据位置
- 调试相对不便
- 需要安装油猴扩展

**工作流：**
1. 先用方案C探索出数据提取方法
2. 将代码转换为油猴脚本
3. 安装到浏览器
4. 以后每次访问自动生效

---

## 推荐工作流：Playwright 交互式探索

### 架构设计

```
正常 Chrome（工作用）
         |
         | 不受影响
         ↓
   继续正常使用

Playwright Chrome（探索用）
         ↓
   自动启动新浏览器
         ↓
   人工登录（扫码/密码）
         ↓
   进入目标页面
         ↓
   AI 接管：执行 JS、分析结构
         ↓
   交互式选择数据
         ↓
   保存到文件
         ↓
  （可选）生成油猴脚本
```

---

## 实战：天天象棋棋谱提取

> **⚠️ 本整章已作废(2026-05-03)**
> 以下操作细节(探索页面结构、`chess_explorer.py` 使用步骤、场景树遍历具体代码)在 2026-05-03 重新验证时发现部分结论错误或已过时,请改用 [`playwright_interactive_exploration.md`](./playwright_interactive_exploration.md) 的最新版本。
>
> **具体问题**:
> - `chess_explorer.py` 本身未跑通,用 `page.locator('text=...')` 找 Canvas 里的文字行不通
> - 登录流程现在直接用 `StartBtn_1`(两个重名,按 y 排序取上面是微信),不走 `NodeQRLogin → btnQRWX`
> - 登录相关的点击必须用 `MouseEvent` 不是 `TouchEvent`
>
> **仍可参考**的只有末尾"第7个数组 `$a.Sg`"这个线索 — UCI moves 数组的疑似位置。

### 第一阶段：探索页面结构

#### 1. 识别页面框架

在控制台运行：
```javascript
console.info({
    title: document.title,
    hasCocos: !!window.cc,
    hasReact: !!document.querySelector('[data-reactroot]'),
    hasVue: !!window.__VUE__
});
```

**结果：** 天天象棋是 Cocos2d 游戏

#### 2. 查看场景树

```javascript
let scene = cc.director.getScene();
console.info(scene);
console.info(scene.children);
```

**发现：**
- 场景名为 `Login` 或 `Canvas`
- 包含多个子节点：`SceneFrame_MainLayer`、`QipuGameSceneForLandscape` 等

#### 3. 遍历查找数组数据

```javascript
(function() {
    let scene = cc.director.getScene();
    let results = [];

    function findArrays(node, depth = 0) {
        if (depth > 8) return;

        if (node._components) {
            node._components.forEach((comp) => {
                if (!comp) return;
                for (let key in comp) {
                    try {
                        if (Array.isArray(comp[key]) && comp[key].length > 5) {
                            results.push({
                                component: comp.constructor.name,
                                key: key,
                                length: comp[key].length
                            });
                        }
                    } catch(e) {}
                }
            });
        }

        if (node.children) {
            node.children.forEach(child => findArrays(child, depth + 1));
        }
    }

    findArrays(scene);
    window.__results = results;
    console.info('找到 ' + results.length + ' 个数组');
    results.forEach((r, i) => {
        console.info(`[${i}] ${r.component}.${r.key} (${r.length})`);
    });
})();
```

**输出：**
```
找到 8 个数组：
[0] pa.UI (长度:6)
[1] CCClass.__eventTargets (长度:18)
[2] CCClass.__eventTargets (长度:18)
[3] Ca.Sy (长度:6)
[4] CCClass.__eventTargets (长度:18)
[5] CCClass.__eventTargets (长度:18)
[6] $a.__eventTargets (长度:17)
[7] $a.Sg (长度:77)  👈 这个最可疑！
```

#### 4. 查看数据内容

```javascript
// 查看第 7 个数组
window.__results[7].ref  // 需要修改代码保存引用

// 或者重新定位
// ... 需要找到具体的组件实例
```

---

### 第二阶段：自动化脚本

使用 `chess_explorer.py` 脚本：

#### 脚本功能

1. **启动浏览器**
   - 使用持久化上下文，保存登录状态
   - 首次使用需要人工登录
   - 后续自动保持登录

2. **人工操作阶段**
   - 脚本暂停，等待用户按回车
   - 用户完成登录、进入目标页面
   - 确认后继续

3. **自动分析**
   - 检测页面框架（Cocos/React/Vue）
   - 根据框架选择不同的数据查找策略
   - 遍历场景树/组件树，查找数组数据

4. **交互式选择**
   - 显示所有找到的数组（带预览）
   - 用户选择要保存的数组编号
   - 自动获取完整数据并保存

5. **数据保存**
   - 保存为 JSON 格式
   - 文件名自动生成：`chess_组件名_属性名.json`
   - 保存到 `qipu/` 目录

---

### 使用步骤

> **⚠️ 作废(2026-05-03)**:下面推荐运行 `chess_explorer.py`,但该脚本实际未跑通。当前可用的做法是直接在 Playwright MCP 中 `evaluate` JS,详见 [`playwright_interactive_exploration.md`](./playwright_interactive_exploration.md)。

#### 安装依赖（一次性）

```bash
cd /Users/u03013112/Documents/git/chinese_chess_train/src

# 安装 Playwright
pip install playwright

# 安装浏览器驱动
playwright install chromium
```

#### 运行脚本

```bash
python chess_explorer.py
```

#### 操作流程

1. **脚本启动浏览器**
   ```
   ======================================
   天天象棋数据探索器
   ======================================

   [1/4] 启动浏览器...
   ✅ 浏览器已启动

   [2/4] 访问天天象棋...
   ```

2. **人工操作**
   ```
   ======================================
   请在浏览器中完成以下操作：
   1. 微信扫码登录
   2. 进入【我的对局】或【棋谱回顾】
   3. 打开某一局棋的回顾页面
   ======================================

   ✅ 完成后按回车继续...
   ```

3. **脚本分析**
   ```
   [3/4] 分析页面结构...
   页面标题: 天天象棋
   URL: https://txqp.qq.com/...
   框架: Cocos2d ✓

   查找 Cocos 游戏中的数据...
   ```

4. **显示结果**
   ```
   [4/4] 提取数据...

   找到 8 个可能的数组：

   [0] pa.UI
       长度: 6, 类型: object
       预览: ['prop1', 'prop2', 'prop3']

   [1] CCClass.__eventTargets
       长度: 18, 类型: object

   ...

   [7] $a.Sg
       长度: 77, 类型: string
       预览: ['h2e2', 'b9c7', 'h0g2']
   ```

5. **交互式操作**
   ```
   ======================================
   选择操作：
   1. 保存某个数组（输入编号）
   2. 保存所有数组
   3. 重新分析页面
   4. 退出
   ======================================
   请选择: 7

   重新获取完整数据...
   ✅ 数据已保存到: ../qipu/chess_$a_Sg.json
   数据长度: 77
   第一个元素: h2e2
   ```

---

## 数据格式分析

### 天天象棋棋谱格式

根据提取的数据 `$a.Sg`：

```json
[
  "h2e2",
  "b9c7",
  "h0g2",
  "h9g7",
  ...
]
```

**格式：** UCI 坐标系的走法序列
- 每个元素是一步棋
- 格式：`起点终点`，例如 `h2e2` 表示从 h2 走到 e2
- 坐标系：a-i 为列（从左到右），1-10 为行（从下到上）

### 转换为 FEN 格式

可以使用项目中已有的工具：

```python
from tools import lastFenAndMove2Qp

# 将 UCI 走法序列转换为 FEN 序列
moves = ['h2e2', 'b9c7', 'h0g2', ...]
fen_list = convert_moves_to_fen(moves)
```

---

## 进阶：生成油猴脚本

### 从探索到生产

探索完成后，可以将提取逻辑转换为油猴脚本，实现一键导出：

```javascript
// ==UserScript==
// @name         天天象棋棋谱一键导出
// @namespace    http://tampermonkey.net/
// @version      1.0
// @description  在棋谱回顾页面添加导出按钮
// @author       You
// @match        https://txqp.qq.com/*
// @grant        none
// ==/UserScript==

(function() {
    'use strict';

    // 等待 Cocos 加载完成
    function waitForCocos() {
        if (!window.cc) {
            setTimeout(waitForCocos, 100);
            return;
        }

        // 检查是否在棋谱回顾页面
        let scene = cc.director.getScene();
        if (scene.name.includes('Qipu') || scene.name.includes('Game')) {
            addExportButton();
        }
    }

    // 添加导出按钮
    function addExportButton() {
        let btn = document.createElement('button');
        btn.innerText = '导出棋谱';
        btn.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 9999;
            padding: 10px 20px;
            background: #4CAF50;
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 14px;
        `;

        btn.onclick = exportChessRecord;
        document.body.appendChild(btn);
    }

    // 导出棋谱
    function exportChessRecord() {
        let scene = cc.director.getScene();

        // 查找棋谱数据（根据之前探索的结果）
        function findData(node) {
            if (node._components) {
                for (let comp of node._components) {
                    if (comp && comp.constructor.name === '$a' && comp.Sg) {
                        return comp.Sg;
                    }
                }
            }

            if (node.children) {
                for (let child of node.children) {
                    let result = findData(child);
                    if (result) return result;
                }
            }

            return null;
        }

        let moves = findData(scene);

        if (!moves) {
            alert('未找到棋谱数据');
            return;
        }

        // 下载为 JSON
        let filename = 'chess_' + new Date().getTime() + '.json';
        let blob = new Blob([JSON.stringify(moves, null, 2)], {type: 'application/json'});
        let url = URL.createObjectURL(blob);
        let a = document.createElement('a');
        a.href = url;
        a.download = filename;
        a.click();
        URL.revokeObjectURL(url);

        alert('棋谱已导出：' + filename);
    }

    // 启动
    waitForCocos();
})();
```

### 安装油猴脚本

1. 安装 Tampermonkey 扩展（Chrome/Edge/Firefox）
2. 点击扩展图标 → 添加新脚本
3. 粘贴上面的代码
4. 保存
5. 刷新天天象棋页面，右上角会出现"导出棋谱"按钮

---

## 通用化：适配其他网站

### 框架识别策略

```javascript
function detectFramework() {
    return {
        // 游戏引擎
        cocos: !!window.cc,
        unity: !!window.UnityLoader,
        phaser: !!window.Phaser,

        // 前端框架
        react: !!document.querySelector('[data-reactroot]') || !!window.React,
        vue: !!window.__VUE__ || !!window.Vue,
        angular: !!window.angular || !!window.ng,

        // jQuery
        jquery: !!window.jQuery || !!window.$,

        // 其他
        webpack: !!window.webpackJsonp,
    };
}
```

### React 应用数据查找

```javascript
function findReactData() {
    // 查找 React 根节点
    let root = document.querySelector('[data-reactroot]');
    if (!root) return null;

    // 获取 React Fiber 节点
    let fiberKey = Object.keys(root).find(key => key.startsWith('__reactFiber'));
    if (!fiberKey) return null;

    let fiber = root[fiberKey];

    // 遍历 Fiber 树查找 state/props
    function traverse(node, depth = 0) {
        if (depth > 20) return;

        // 检查 state
        if (node.memoizedState) {
            console.log('State:', node.memoizedState);
        }

        // 检查 props
        if (node.memoizedProps) {
            console.log('Props:', node.memoizedProps);
        }

        // 遍历子节点
        if (node.child) traverse(node.child, depth + 1);
        if (node.sibling) traverse(node.sibling, depth + 1);
    }

    traverse(fiber);
}
```

### Vue 应用数据查找

```javascript
function findVueData() {
    // Vue 2.x
    if (window.__VUE_DEVTOOLS_GLOBAL_HOOK__) {
        let hook = window.__VUE_DEVTOOLS_GLOBAL_HOOK__;
        let apps = hook.apps || [];

        apps.forEach(app => {
            console.log('Vue App:', app);
            console.log('Data:', app.$data);
        });
    }

    // Vue 3.x
    let app = document.querySelector('[data-v-app]');
    if (app && app.__vue_app__) {
        console.log('Vue 3 App:', app.__vue_app__);
    }
}
```

---

## 故障排查

### 问题1：找不到数据

**可能原因：**
1. 数据还未加载完成
2. 数据在不同的节点/组件中
3. 数据被混淆/加密

**解决方案：**
```javascript
// 等待数据加载
setTimeout(() => {
    // 再次执行查找
}, 2000);

// 或者监听网络请求
let originalFetch = window.fetch;
window.fetch = function(...args) {
    return originalFetch.apply(this, args).then(response => {
        response.clone().json().then(data => {
            console.log('API 返回:', data);
        });
        return response;
    });
};
```

### 问题2：数据格式无法解析

**解决方案：**
1. 查看原始数据结构
2. 尝试不同的解析方式
3. 查找官方 API 文档或逆向工程

### 问题3：Playwright 无法连接

**解决方案：**
```bash
# 检查 Playwright 安装
playwright --version

# 重新安装浏览器
playwright install --force chromium

# 使用系统浏览器
browser = p.chromium.launch(channel="chrome")
```

---

## 最佳实践

### 1. 渐进式探索

不要一开始就写完整脚本，而是：
1. 先在控制台手动探索
2. 找到数据位置后，写简单脚本验证
3. 确认无误后，编写完整自动化脚本

### 2. 保存探索历史

```javascript
// 将探索过程保存到 localStorage
localStorage.setItem('exploration_log', JSON.stringify({
    timestamp: Date.now(),
    framework: 'cocos',
    dataPath: 'scene.node.component.$a.Sg',
    sampleData: [...]
}));
```

### 3. 错误处理

```javascript
function safeExtract() {
    try {
        // 提取逻辑
        return extractData();
    } catch (e) {
        console.error('提取失败:', e);
        return null;
    }
}
```

### 4. 数据验证

```javascript
function validateChessData(moves) {
    // 检查是否是合法的走法序列
    if (!Array.isArray(moves)) return false;
    if (moves.length < 10) return false;

    // 检查格式：a-i + 1-10
    let pattern = /^[a-i][0-9][a-i][0-9]$/;
    return moves.every(move => pattern.test(move));
}
```

---

## 扩展应用

### 场景1：批量导出历史对局

```python
# 在对局列表页面
games = page.evaluate("""
    // 获取所有对局链接
    Array.from(document.querySelectorAll('.game-item'))
        .map(item => item.href)
""")

# 遍历每局棋
for game_url in games:
    page.goto(game_url)
    data = extract_chess_data(page)
    save_to_file(data, f'game_{game_id}.json')
```

### 场景2：实时对局记录

```javascript
// 监听棋盘变化
let observer = new MutationObserver(() => {
    let currentState = getBoardState();
    recordMove(currentState);
});

observer.observe(boardElement, {
    childList: true,
    subtree: true
});
```

### 场景3：数据分析

```python
# 分析棋谱，找出常见开局
from collections import Counter

all_openings = []
for file in os.listdir('qipu/'):
    with open(file) as f:
        moves = json.load(f)
        opening = ' '.join(moves[:6])  # 前3个回合
        all_openings.append(opening)

most_common = Counter(all_openings).most_common(10)
print('最常见的开局：', most_common)
```

---

## 总结

### 工作流总结

1. **探索阶段** - 使用 Playwright 交互式脚本
2. **验证阶段** - 确认数据正确性
3. **自动化阶段** - 编写可复用脚本
4. **生产阶段** - 转换为油猴脚本或命令行工具

### 技术选型总结

| 场景 | 推荐方案 | 理由 |
|------|---------|------|
| 快速验证 | 控制台脚本 | 最快 |
| AI 驱动探索 | Playwright | 最灵活 |
| 长期使用 | 油猴脚本 | 最方便 |
| 批量处理 | Python 脚本 | 最强大 |

### 关键要点

- ✅ **支持人工介入** - 登录、验证等环节必不可少
- ✅ **迭代式探索** - 不要期望一次成功
- ✅ **保存状态** - 登录状态、探索历史都要保存
- ✅ **数据验证** - 提取后一定要验证格式
- ✅ **通用化设计** - 代码要易于适配其他网站

---

## 附录：相关文件

### 项目文件结构

```
chinese_chess_train/
├── src/
│   ├── chess_explorer.py          # 交互式探索脚本（主要工具）
│   ├── extract_chess_data.py      # 远程调试版本（备用）
│   └── chrome_debug.py             # CDP 连接脚本（备用）
├── docs/
│   └── web_data_extraction_workflow.md  # 本文档
├── qipu/                           # 导出的棋谱数据
│   └── chess_*.json
└── start_chess_chrome.sh           # Chrome 启动脚本（可选）
```

### 相关命令速查

```bash
# 安装依赖
pip install playwright
playwright install chromium

# 运行探索脚本
python src/chess_explorer.py

# 查看提取的数据
cat qipu/chess_*.json | jq

# 分析棋谱
python src/AnaylizeFenFile.py qipu/chess_data.json
```

---

## 参考资料

- [Playwright 官方文档](https://playwright.dev/python/)
- [Cocos2d-JS 文档](https://docs.cocos.com/cocos2d-x/v3/manual/)
- [Tampermonkey 文档](https://www.tampermonkey.net/documentation.php)
- [Chrome DevTools Protocol](https://chromedevtools.github.io/devtools-protocol/)

---

*文档版本：v1.0（实战章节已于 v1.1 标注作废,通用方法论部分仍有效）*
*最后更新：2026-05-03（追加作废标注,实战内容迁移到 playwright_interactive_exploration.md）*
*作者：通过 Claude Code 生成*
