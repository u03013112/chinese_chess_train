#!/usr/bin/env python3
"""
天天象棋自动导航脚本 - 无头模式

自动完成：
1. 点击"象棋"
2. 点击"我的棋谱"
3. 点击任意一个棋谱
"""

from playwright.sync_api import sync_playwright
import json
import os
import time

class ChessAutoNav:
    def __init__(self, headless=True):
        self.playwright = None
        self.browser = None
        self.page = None
        self.headless = headless

    def _take_screenshot(self, name):
        """截图"""
        screenshot_dir = os.path.join(os.path.dirname(__file__), 'screenshots')
        os.makedirs(screenshot_dir, exist_ok=True)
        filepath = os.path.join(screenshot_dir, f'{name}.png')
        self.page.screenshot(path=filepath)
        print(f"📸 {filepath}")
        return filepath

    def _check_login(self):
        """检查登录状态"""
        has_token = self.page.evaluate("""
            () => {
                let token = localStorage.getItem('qqchess_webToken_wx');
                return token && token !== 'null' && token !== '';
            }
        """)
        return has_token

    def _list_all_text_nodes(self):
        """列出所有包含文本的节点（调试用）"""
        js_code = """
        (function() {
            if (!window.cc) {
                return {success: false, error: 'No Cocos'};
            }

            let scene = cc.director.getScene();
            let results = [];

            function searchNode(node, depth = 0, path = '') {
                if (depth > 15) return;

                let currentPath = path + '/' + node.name;
                let nodeInfo = {
                    name: node.name,
                    path: currentPath,
                    depth: depth,
                    texts: []
                };

                // 检查 Label 组件
                if (node._components) {
                    for (let comp of node._components) {
                        if (!comp) continue;

                        if (comp.string && comp.string.length > 0 && comp.string.length < 20) {
                            nodeInfo.texts.push(comp.string);
                        }
                        if (comp.text && comp.text.length > 0 && comp.text.length < 20) {
                            nodeInfo.texts.push(comp.text);
                        }
                    }
                }

                if (nodeInfo.texts.length > 0) {
                    results.push(nodeInfo);
                }

                // 递归子节点
                if (node.children) {
                    for (let child of node.children) {
                        searchNode(child, depth + 1, currentPath);
                    }
                }
            }

            searchNode(scene);
            return {success: true, results: results};
        })();
        """

        try:
            result = self.page.evaluate(js_code)
            if result['success']:
                print(f"\n找到 {len(result['results'])} 个文本节点：")
                for item in result['results']:  # 显示所有节点
                    texts_str = ', '.join(item['texts'])
                    print(f"  [{item['depth']}] {item['name']}: {texts_str}")
            return result.get('results', [])
        except Exception as e:
            print(f"  ❌ 错误: {e}")
            return []

    def _find_and_click_by_text(self, text, debug=False):
        """通过文本查找 Cocos 节点并模拟点击事件"""
        print(f"  查找包含 '{text}' 的节点...")

        js_code = f"""
        (function() {{
            if (!window.cc) {{
                return {{success: false, error: 'No Cocos'}};
            }}

            let scene = cc.director.getScene();
            let found = null;

            function searchNode(node, depth = 0) {{
                if (depth > 15) return;

                // 检查节点名称
                if (node.name && node.name.includes('{text}')) {{
                    found = node;
                    return;
                }}

                // 检查 Label 组件
                if (node._components) {{
                    for (let comp of node._components) {{
                        if (!comp) continue;

                        // Label 组件
                        if (comp.string && comp.string.includes('{text}')) {{
                            found = node;
                            return;
                        }}

                        // 其他可能的文本属性
                        if (comp.text && comp.text.includes('{text}')) {{
                            found = node;
                            return;
                        }}
                    }}
                }}

                // 递归子节点
                if (node.children) {{
                    for (let child of node.children) {{
                        searchNode(child, depth + 1);
                        if (found) return;
                    }}
                }}
            }}

            searchNode(scene);

            if (!found) {{
                return {{success: false, error: 'Node not found'}};
            }}

            // 直接触发点击事件（Cocos 内部）
            // 尝试触发 touch 事件
            try {{
                // 方法1: 直接调用回调
                if (found._touchListener) {{
                    found._touchListener.onTouchBegan && found._touchListener.onTouchBegan();
                    found._touchListener.onTouchEnded && found._touchListener.onTouchEnded();
                }}

                // 方法2: 发送 Cocos 事件
                let event = new cc.Event.EventTouch([], false);
                event.touch = {{
                    getLocation: () => found.convertToWorldSpaceAR(cc.v2(0, 0))
                }};
                found.emit(cc.Node.EventType.TOUCH_START, event);
                found.emit(cc.Node.EventType.TOUCH_END, event);

                return {{
                    success: true,
                    nodeName: found.name,
                    method: 'cocos_event'
                }};
            }} catch(e) {{
                return {{success: false, error: 'Click failed: ' + e.message}};
            }}
        }})();
        """

        try:
            result = self.page.evaluate(js_code)

            if result['success']:
                print(f"  ✅ 找到并点击节点: {result.get('nodeName', 'unknown')}")
                print(f"     方法: {result.get('method', 'unknown')}")
                time.sleep(2)
                return True
            else:
                print(f"  ⚠️  {result.get('error', 'unknown')}")
                return False
        except Exception as e:
            print(f"  ❌ 错误: {e}")
            return False

    def _click_first_item_in_list(self):
        """点击列表中的第一个项目"""
        print("  查找列表中的第一个项目...")

        js_code = """
        (function() {
            if (!window.cc) {
                return {success: false, error: 'No Cocos'};
            }

            let scene = cc.director.getScene();
            let listItems = [];

            function searchListItems(node, depth = 0, parentPath = '') {
                if (depth > 10) return;

                let currentPath = parentPath + '/' + node.name;

                // 查找对局条目（更精确的判断）
                // 1. 节点名包含 Item/Cell 但不包含 Choose/Type（排除筛选器）
                // 2. 或者节点有多个同名兄弟节点（通常是列表项）
                if (node.name && !node.name.includes('Choose') && !node.name.includes('Type')) {
                    if (node.name.includes('Item') || node.name.includes('Cell') || node.name.includes('Record')) {
                        listItems.push({node: node, path: currentPath});
                    }
                }

                if (node.children && node.children.length > 0) {
                    for (let child of node.children) {
                        searchListItems(child, depth + 1, currentPath);
                    }
                }
            }

            searchListItems(scene);

            // 如果找不到 Item，查找有多个子节点的容器（可能是列表容器）
            if (listItems.length === 0) {
                function findListContainer(node, depth = 0) {
                    if (depth > 8) return;

                    // 如果一个节点有3个以上结构相似的子节点，可能是列表
                    if (node.children && node.children.length >= 3) {
                        let firstChild = node.children[0];
                        // 检查子节点是否结构相似
                        if (firstChild && firstChild.children) {
                            for (let i = 0; i < Math.min(3, node.children.length); i++) {
                                listItems.push({node: node.children[i], path: node.name + '/child' + i});
                            }
                            return;
                        }
                    }

                    if (node.children) {
                        for (let child of node.children) {
                            findListContainer(child, depth + 1);
                            if (listItems.length > 0) return;
                        }
                    }
                }

                findListContainer(scene);
            }

            if (listItems.length === 0) {
                return {success: false, error: 'No list items found'};
            }

            // 按 Y 坐标排序，找最上面的（排除负数或异常坐标）
            listItems = listItems.filter(item => {
                try {
                    let pos = item.node.convertToWorldSpaceAR(cc.v2(0, 0));
                    return pos && Math.abs(pos.y) < 10000;  // 排除异常坐标
                } catch(e) {
                    return false;
                }
            });

            listItems.sort((a, b) => {
                let posA = a.node.convertToWorldSpaceAR(cc.v2(0, 0));
                let posB = b.node.convertToWorldSpaceAR(cc.v2(0, 0));
                return posB.y - posA.y;
            });

            if (listItems.length === 0) {
                return {success: false, error: 'No valid list items found'};
            }

            // 点击第一个
            let firstItem = listItems[0].node;
            let firstItemPath = listItems[0].path;

            try {
                // 触发点击事件
                let event = new cc.Event.EventTouch([], false);
                event.touch = {
                    getLocation: () => firstItem.convertToWorldSpaceAR(cc.v2(0, 0))
                };
                firstItem.emit(cc.Node.EventType.TOUCH_START, event);
                firstItem.emit(cc.Node.EventType.TOUCH_END, event);

                return {
                    success: true,
                    nodeName: firstItem.name,
                    path: firstItemPath,
                    totalItems: listItems.length
                };
            } catch(e) {
                return {success: false, error: 'Click failed: ' + e.message};
            }
        })();
        """

        try:
            result = self.page.evaluate(js_code)

            if result['success']:
                print(f"  ✅ 找到并点击列表项: {result.get('nodeName', 'unknown')}")
                print(f"     总共 {result.get('totalItems', 0)} 个项目")
                time.sleep(2)
                return True
            else:
                print(f"  ⚠️  {result.get('error', 'unknown')}")
                return False
        except Exception as e:
            print(f"  ❌ 错误: {e}")
            return False

    def navigate(self):
        """自动导航"""
        print("=" * 60)
        print("天天象棋自动导航")
        print("=" * 60)

        self.playwright = sync_playwright().start()

        # 启动浏览器
        print("\n[1/5] 启动浏览器...")
        user_data_dir = os.path.join(os.path.dirname(__file__), 'chrome_data')

        self.browser = self.playwright.chromium.launch_persistent_context(
            user_data_dir=user_data_dir,
            headless=self.headless,
            args=['--start-maximized'] if not self.headless else []
        )

        self.page = self.browser.pages[0] if self.browser.pages else self.browser.new_page()
        print("✅ 浏览器已启动" + (" (无头模式)" if self.headless else ""))

        # 访问天天象棋
        print("\n[2/5] 访问天天象棋...")
        self.page.goto('https://h5login.qqchess.qq.com/')
        time.sleep(3)
        self._take_screenshot('01_start')

        # 检查登录
        print("\n[3/5] 检查登录...")
        if not self._check_login():
            print("❌ 未登录，请先手动登录一次")
            self.browser.close()
            return False

        print("✅ 已登录")

        # 自动导航
        print("\n[4/5] 自动导航...")

        # Step 1: 点击"象棋"
        print("\n步骤1: 点击一级菜单 <象棋>")
        time.sleep(2)
        if not self._find_and_click_by_text('象棋'):
            print("  尝试其他文本...")
            self._find_and_click_by_text('chess')

        self._take_screenshot('02_after_chess')

        # 等待子菜单动画完成
        print("  等待子菜单加载...")
        time.sleep(3)

        # 调试：列出所有文本节点
        print("\n[调试] 列出当前页面的所有文本节点：")
        self._list_all_text_nodes()

        # Step 2: 点击"对局"
        print("\n步骤2: 点击二级菜单 <对局>")
        time.sleep(2)
        if not self._find_and_click_by_text('对局'):
            print("  尝试其他文本...")
            self._find_and_click_by_text('game')

        self._take_screenshot('03_after_game')

        # Step 3: 点击"我的棋谱"
        print("\n步骤3: 点击三级菜单 <我的棋谱>")
        time.sleep(2)
        if not self._find_and_click_by_text('我的棋谱'):
            print("  尝试其他文本...")
            self._find_and_click_by_text('棋谱')

        self._take_screenshot('04_qipu_list')

        # Step 4: 点击第一个棋谱
        print("\n步骤4: 点击列表中的第一个棋谱")
        time.sleep(2)
        self._click_first_item_in_list()

        self._take_screenshot('05_qipu_detail')

        print("\n[5/5] 导航完成！")
        print("=" * 60)

        return True

    def close(self):
        """关闭浏览器"""
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()

def main():
    nav = ChessAutoNav(headless=True)  # 无头模式

    try:
        if nav.navigate():
            print("\n✅ 成功！浏览器保持打开以便查看...")
            print("查看截图: src/screenshots/")

            if not nav.headless:
                input("\n按回车关闭...")
        else:
            print("\n❌ 导航失败")
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        nav.close()

if __name__ == '__main__':
    main()
