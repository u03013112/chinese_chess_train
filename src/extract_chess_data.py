#!/usr/bin/env python3
"""
从天天象棋浏览器页面自动提取棋谱数据

使用方法：
1. 正常打开 Chrome 浏览器
2. 访问天天象棋，进入棋谱回顾页面
3. 在终端运行: python extract_chess_data.py

脚本会自动：
- 连接到你的 Chrome
- 找到天天象棋页面
- 提取所有可能的棋谱数据
- 保存到文件
"""

import json
import os
import sys
import subprocess
import time
import requests

def get_chrome_tabs():
    """获取所有打开的 Chrome 标签页"""
    try:
        # 尝试连接到 Chrome 调试端口
        response = requests.get('http://localhost:9222/json', timeout=2)
        tabs = response.json()
        return tabs
    except:
        return None

def find_chess_tab(tabs):
    """找到天天象棋的标签页"""
    for tab in tabs:
        if '象棋' in tab.get('title', '') or 'chess' in tab.get('url', '').lower():
            return tab
    return None

def extract_data_from_tab(ws_url):
    """从标签页提取数据"""
    import websocket

    results = []

    def on_message(ws, message):
        data = json.loads(message)
        if 'result' in data and data.get('id') == 1:
            results.append(data['result'])

    def on_open(ws):
        # 执行 JS 代码
        js_code = """
        (function() {
            let scene = cc.director.getScene();
            let results = [];

            function findArrays(node, path = '', depth = 0) {
                if (depth > 8) return;
                let currentPath = path + '/' + node.name;

                if (node._components) {
                    node._components.forEach((comp) => {
                        if (!comp) return;
                        let compName = comp.constructor ? comp.constructor.name : 'Unknown';

                        for (let key in comp) {
                            try {
                                if (Array.isArray(comp[key]) && comp[key].length > 5) {
                                    results.push({
                                        component: compName,
                                        key: key,
                                        length: comp[key].length,
                                        data: comp[key]
                                    });
                                }
                            } catch(e) {}
                        }
                    });
                }

                if (node.children) {
                    node.children.forEach(child => findArrays(child, currentPath, depth + 1));
                }
            }

            findArrays(scene);
            return results;
        })();
        """

        command = {
            "id": 1,
            "method": "Runtime.evaluate",
            "params": {
                "expression": js_code,
                "returnByValue": True
            }
        }
        ws.send(json.dumps(command))

    ws = websocket.WebSocketApp(ws_url,
                                 on_message=on_message,
                                 on_open=on_open)

    # 运行并等待结果
    import threading
    ws_thread = threading.Thread(target=ws.run_forever)
    ws_thread.daemon = True
    ws_thread.start()

    # 等待结果
    time.sleep(2)
    ws.close()

    return results

def main():
    print("=" * 60)
    print("天天象棋棋谱自动提取工具")
    print("=" * 60)

    # 检查 Chrome 是否开启了调试端口
    print("\n[1/4] 检查 Chrome 调试端口...")
    tabs = get_chrome_tabs()

    if not tabs:
        print("❌ Chrome 调试端口未开启")
        print("\n请按以下步骤操作：")
        print("1. 关闭所有 Chrome 窗口")
        print("2. 在终端运行：")
        print("   /Applications/Google\\ Chrome.app/Contents/MacOS/Google\\ Chrome --remote-debugging-port=9222")
        print("3. 在打开的 Chrome 中访问天天象棋")
        print("4. 重新运行此脚本")
        return

    print(f"✅ 找到 {len(tabs)} 个标签页")

    # 查找天天象棋页面
    print("\n[2/4] 查找天天象棋页面...")
    chess_tab = find_chess_tab(tabs)

    if not chess_tab:
        print("❌ 未找到天天象棋页面")
        print("\n可用的标签页：")
        for i, tab in enumerate(tabs):
            print(f"  {i}. {tab.get('title', 'Unknown')}")

        choice = input("\n请输入要使用的标签页编号: ").strip()
        try:
            chess_tab = tabs[int(choice)]
        except:
            print("❌ 无效的选择")
            return

    print(f"✅ 找到页面: {chess_tab.get('title', 'Unknown')}")

    # 提取数据
    print("\n[3/4] 提取棋谱数据...")

    try:
        import websocket
    except ImportError:
        print("❌ 需要安装 websocket-client")
        print("运行: pip install websocket-client")
        return

    ws_url = chess_tab.get('webSocketDebuggerUrl')
    if not ws_url:
        print("❌ 无法获取 WebSocket URL")
        return

    results = extract_data_from_tab(ws_url)

    if not results:
        print("❌ 未能提取数据")
        return

    # 保存数据
    print("\n[4/4] 保存数据...")

    output_dir = os.path.join(os.path.dirname(__file__), '..', 'qipu')
    os.makedirs(output_dir, exist_ok=True)

    if results and 'value' in results[0]:
        arrays = results[0]['value']

        print(f"\n找到 {len(arrays)} 个数组：")
        for i, arr in enumerate(arrays):
            component = arr.get('component', 'Unknown')
            key = arr.get('key', 'Unknown')
            length = arr.get('length', 0)
            print(f"  [{i}] {component}.{key} (长度: {length})")

            # 保存长度合理的数组
            if 20 <= length <= 200:
                filename = f"chess_{component}_{key}.json"
                filepath = os.path.join(output_dir, filename)

                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(arr.get('data', []), f, ensure_ascii=False, indent=2)

                print(f"       ✅ 已保存: {filename}")

    print("\n" + "=" * 60)
    print("✅ 完成！数据已保存到 qipu/ 目录")
    print("=" * 60)

if __name__ == '__main__':
    main()
