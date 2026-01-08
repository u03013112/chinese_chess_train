#!/usr/bin/env python3
"""
连接到现有的 Chrome 实例，执行 JS 并获取棋谱数据
使用前先启动 Chrome:
  /Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --remote-debugging-port=9222
"""

from playwright.sync_api import sync_playwright
import json

def connect_to_chrome():
    """连接到已打开的 Chrome 浏览器"""
    with sync_playwright() as p:
        # 连接到现有的 Chrome 实例
        browser = p.chromium.connect_over_cdp("http://localhost:9222")

        # 获取所有页面
        contexts = browser.contexts
        if not contexts:
            print("没有找到打开的页面")
            return

        # 列出所有标签页
        print("所有打开的标签页：")
        for idx, context in enumerate(contexts):
            pages = context.pages
            for page_idx, page in enumerate(pages):
                print(f"{idx}-{page_idx}: {page.title()} - {page.url}")

        # 让用户选择或自动选择包含天天象棋的页面
        target_page = None
        for context in contexts:
            for page in context.pages:
                if '象棋' in page.title() or 'chess' in page.url.lower():
                    target_page = page
                    print(f"\n找到天天象棋页面: {page.title()}")
                    break
            if target_page:
                break

        if not target_page:
            # 如果没找到，使用第一个页面
            target_page = contexts[0].pages[0]
            print(f"\n使用当前页面: {target_page.title()}")

        # 执行 JS 查找数组数据
        print("\n开始查找棋谱数据...")

        js_code = """
        (function() {
            let scene = cc.director.getScene();
            let results = [];

            function findArrays(node, path = '', depth = 0) {
                if (depth > 8) return;

                let currentPath = path + '/' + node.name;

                // 检查节点属性
                for (let key in node) {
                    try {
                        if (Array.isArray(node[key]) && node[key].length > 5) {
                            results.push({
                                type: 'node',
                                path: currentPath,
                                key: key,
                                length: node[key].length,
                                data: node[key].slice(0, 3)  // 只取前3个元素预览
                            });
                        }
                    } catch(e) {}
                }

                // 检查组件属性
                if (node._components) {
                    node._components.forEach((comp, idx) => {
                        if (!comp) return;
                        let compName = comp.constructor ? comp.constructor.name : 'Unknown';

                        for (let key in comp) {
                            try {
                                if (Array.isArray(comp[key]) && comp[key].length > 5) {
                                    results.push({
                                        type: 'component',
                                        path: currentPath,
                                        componentIndex: idx,
                                        componentName: compName,
                                        key: key,
                                        length: comp[key].length,
                                        data: comp[key].slice(0, 3)  // 只取前3个元素预览
                                    });
                                }
                            } catch(e) {}
                        }
                    });
                }

                // 递归子节点
                if (node.children) {
                    node.children.forEach(child => {
                        findArrays(child, currentPath, depth + 1);
                    });
                }
            }

            findArrays(scene);
            return results;
        })();
        """

        result = target_page.evaluate(js_code)

        print(f"\n找到 {len(result)} 个可能的数组数据：\n")

        for idx, item in enumerate(result):
            if item['type'] == 'node':
                print(f"{idx}. 节点: {item['path']}.{item['key']}")
            else:
                print(f"{idx}. 组件: {item['path']}._components[{item['componentIndex']}]({item['componentName']}).{item['key']}")

            print(f"   长度: {item['length']}")
            print(f"   预览: {item['data']}")
            print()

        # 如果找到数据，让用户选择要导出哪个
        if result:
            print("\n请选择要导出的数据编号（输入编号，如 0）：")
            choice = input().strip()

            try:
                choice_idx = int(choice)
                if 0 <= choice_idx < len(result):
                    selected = result[choice_idx]

                    # 获取完整数据
                    if selected['type'] == 'node':
                        js_get_data = f"""
                        (function() {{
                            let scene = cc.director.getScene();
                            function findNode(node, targetPath, currentPath = '') {{
                                let path = currentPath + '/' + node.name;
                                if (path === '{selected['path']}') {{
                                    return node['{selected['key']}'];
                                }}
                                if (node.children) {{
                                    for (let child of node.children) {{
                                        let result = findNode(child, targetPath, path);
                                        if (result) return result;
                                    }}
                                }}
                                return null;
                            }}
                            return findNode(scene, '{selected['path']}');
                        }})();
                        """
                    else:
                        js_get_data = f"""
                        (function() {{
                            let scene = cc.director.getScene();
                            function findNode(node, targetPath, currentPath = '') {{
                                let path = currentPath + '/' + node.name;
                                if (path === '{selected['path']}') {{
                                    let comp = node._components[{selected['componentIndex']}];
                                    return comp ? comp['{selected['key']}'] : null;
                                }}
                                if (node.children) {{
                                    for (let child of node.children) {{
                                        let result = findNode(child, targetPath, path);
                                        if (result) return result;
                                    }}
                                }}
                                return null;
                            }}
                            return findNode(scene, '{selected['path']}');
                        }})();
                        """

                    full_data = target_page.evaluate(js_get_data)

                    if full_data:
                        # 保存到文件
                        output_file = '/Users/u03013112/Documents/git/chinese_chess_train/qipu/chess_data_raw.json'
                        with open(output_file, 'w', encoding='utf-8') as f:
                            json.dump(full_data, f, ensure_ascii=False, indent=2)
                        print(f"\n✅ 数据已保存到: {output_file}")
                        print(f"数据长度: {len(full_data)}")
                        print(f"前3个元素: {full_data[:3]}")
                    else:
                        print("\n❌ 无法获取完整数据")
            except (ValueError, IndexError):
                print("无效的选择")

        print("\n完成！浏览器保持打开状态。")
        # browser.close()  # 不关闭浏览器

if __name__ == '__main__':
    try:
        connect_to_chrome()
    except Exception as e:
        print(f"错误: {e}")
        print("\n请确保：")
        print("1. Chrome 已用远程调试模式启动")
        print("2. 已安装 playwright: pip install playwright")
        print("3. 已安装浏览器: playwright install chromium")
