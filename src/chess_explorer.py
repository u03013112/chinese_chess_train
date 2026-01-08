#!/usr/bin/env python3
"""
天天象棋数据探索器 - 交互式版本

使用流程：
1. 运行脚本，会打开浏览器
2. 手动登录天天象棋
3. 进入棋谱回顾页面
4. 脚本自动分析并提取数据
"""

from playwright.sync_api import sync_playwright
import json
import os
import subprocess
import time

class ChessExplorer:
    def __init__(self):
        self.playwright = None
        self.browser = None
        self.page = None
        self.login_file = os.path.join(os.path.dirname(__file__), 'login_info.json')

    def _load_login_info(self):
        """加载保存的登录信息"""
        if os.path.exists(self.login_file):
            with open(self.login_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return None

    def _inject_login_info(self, page, login_info):
        """注入登录信息到页面"""
        if not login_info or 'localStorage' not in login_info:
            return False

        print("注入登录信息...")

        # 注入 localStorage
        for key, value in login_info['localStorage'].items():
            page.evaluate(f"localStorage.setItem('{key}', {json.dumps(value)})")

        # 注入 sessionStorage（如果有）
        if 'sessionStorage' in login_info:
            for key, value in login_info['sessionStorage'].items():
                if value:  # 只注入非空值
                    page.evaluate(f"sessionStorage.setItem('{key}', {json.dumps(value)})")

        return True

    def _take_screenshot(self, name):
        """截图保存"""
        screenshot_dir = os.path.join(os.path.dirname(__file__), 'screenshots')
        os.makedirs(screenshot_dir, exist_ok=True)

        filepath = os.path.join(screenshot_dir, f'{name}.png')
        self.page.screenshot(path=filepath)
        print(f"📸 截图: {filepath}")
        return filepath

    def _check_login(self):
        """检查是否已登录"""
        # 检查 localStorage 中是否有登录 token
        has_token = self.page.evaluate("""
            () => {
                let token = localStorage.getItem('qqchess_webToken_wx');
                return token && token !== 'null' && token !== '';
            }
        """)
        return has_token

    def _wait_for_login(self):
        """等待用户登录"""
        print("\n等待登录...")
        print("请在浏览器中扫码登录")

        # 轮询检查登录状态
        max_wait = 120  # 最多等待2分钟
        for i in range(max_wait):
            time.sleep(1)
            if self._check_login():
                print("✅ 检测到登录成功")
                return True

        print("❌ 登录超时")
        return False

    def _auto_navigate(self):
        """自动导航到棋谱页面"""
        print("\n[自动导航] 开始...")

        try:
            # 等待页面加载
            time.sleep(2)
            self._take_screenshot('01_login_page')

            # 1. 关闭广告（如果有）
            print("  检查广告...")
            try:
                # 常见的广告关闭按钮
                close_selectors = [
                    'text=关闭',
                    'text=跳过',
                    '[class*=close]',
                    '[class*=skip]',
                    '.ad-close'
                ]

                for selector in close_selectors:
                    try:
                        if self.page.locator(selector).count() > 0:
                            self.page.locator(selector).first.click(timeout=1000)
                            print("  ✅ 关闭广告")
                            time.sleep(1)
                            break
                    except:
                        pass
            except Exception as e:
                print(f"  ⚠️  关闭广告失败: {e}")

            self._take_screenshot('02_after_close_ad')

            # 2. 查找并点击"象棋"或相关按钮
            print("  查找'象棋'入口...")
            try:
                # 尝试多种可能的选择器
                selectors = [
                    'text=象棋',
                    'text=天天象棋',
                    'text=进入游戏',
                    '[class*=chess]',
                    '[id*=chess]'
                ]

                clicked = False
                for selector in selectors:
                    try:
                        if self.page.locator(selector).count() > 0:
                            self.page.locator(selector).first.click(timeout=2000)
                            print(f"  ✅ 点击: {selector}")
                            clicked = True
                            time.sleep(2)
                            break
                    except:
                        pass

                if not clicked:
                    print("  ⚠️  未找到'象棋'入口，可能已在游戏页面")
            except Exception as e:
                print(f"  ⚠️  点击失败: {e}")

            self._take_screenshot('03_enter_game')

            # 3. 点击"我的棋谱"
            print("  查找'我的棋谱'...")
            try:
                selectors = [
                    'text=我的棋谱',
                    'text=棋谱',
                    'text=我的对局',
                    '[class*=qipu]',
                    '[class*=record]'
                ]

                for selector in selectors:
                    try:
                        if self.page.locator(selector).count() > 0:
                            self.page.locator(selector).first.click(timeout=2000)
                            print(f"  ✅ 点击: {selector}")
                            time.sleep(2)
                            break
                    except:
                        pass
            except Exception as e:
                print(f"  ⚠️  点击失败: {e}")

            self._take_screenshot('04_qipu_list')

            # 4. 点击第一个棋谱
            print("  点击第一个棋谱...")
            try:
                # 等待 Canvas 加载
                time.sleep(3)

                # 根据截图分析，对局列表在右侧
                # 第一个对局大概在右侧中间偏上
                viewport = self.page.viewport_size

                # 尝试多个可能的位置
                positions = [
                    (viewport['width'] * 2 // 3, viewport['height'] // 3),    # 右侧上部
                    (viewport['width'] * 3 // 4, viewport['height'] * 2 // 5),  # 更靠右
                    (viewport['width'] * 2 // 3, viewport['height'] // 2),    # 右侧中部
                ]

                for x, y in positions:
                    print(f"  尝试点击坐标: ({x}, {y})")
                    self.page.mouse.click(x, y)
                    time.sleep(3)  # 等待跳转

                    # 检查是否跳转成功（URL 或页面内容变化）
                    self._take_screenshot(f'05_after_click_{x}_{y}')

                    # 如果找到棋盘，说明成功了
                    has_board = self.page.evaluate("""
                        () => {
                            if (!window.cc) return false;
                            let scene = cc.director.getScene();
                            return scene && scene.children && scene.children.length > 0;
                        }
                    """)

                    if has_board:
                        print("  ✅ 成功进入棋谱详情页")
                        break
                    else:
                        print(f"  ⚠️  位置 ({x}, {y}) 无效，尝试下一个...")

            except Exception as e:
                print(f"  ⚠️  点击失败: {e}")

            self._take_screenshot('05_qipu_detail')

            print("\n✅ 自动导航完成")
            return True

        except Exception as e:
            print(f"\n❌ 自动导航失败: {e}")
            import traceback
            traceback.print_exc()
            return False

    def start(self):
        """启动浏览器并自动导航"""
        print("=" * 60)
        print("天天象棋数据探索器")
        print("=" * 60)

        self.playwright = sync_playwright().start()

        # 启动浏览器
        print("\n[1/5] 启动浏览器...")
        user_data_dir = os.path.join(os.path.dirname(__file__), 'chrome_data')

        self.browser = self.playwright.chromium.launch_persistent_context(
            user_data_dir=user_data_dir,
            headless=False,
            args=['--start-maximized'],
            slow_mo=100  # 放慢操作，便于观察
        )

        self.page = self.browser.pages[0] if self.browser.pages else self.browser.new_page()
        print("✅ 浏览器已启动")

        # 访问天天象棋
        print("\n[2/5] 访问天天象棋...")
        self.page.goto('https://h5login.qqchess.qq.com/')
        time.sleep(2)

        # 检查登录状态
        print("\n[3/5] 检查登录状态...")
        if not self._check_login():
            print("⚠️  未登录")
            self._take_screenshot('00_need_login')

            if not self._wait_for_login():
                print("请手动登录后重新运行脚本")
                return self
        else:
            print("✅ 已登录")

        # 自动导航
        print("\n[4/5] 自动导航...")
        self._auto_navigate()

        print("\n[5/5] 准备分析数据...")
        return self

    def analyze_page(self):
        """分析页面结构"""
        print("\n[3/4] 分析页面结构...")

        # 检测页面类型
        page_info = self.page.evaluate("""
        ({
            title: document.title,
            url: window.location.href,
            hasCocos: !!window.cc,
            hasReact: !!document.querySelector('[data-reactroot]'),
            hasVue: !!window.__VUE__
        })
        """)

        print(f"页面标题: {page_info['title']}")
        print(f"URL: {page_info['url']}")
        print(f"框架: ", end='')

        if page_info['hasCocos']:
            print("Cocos2d ✓")
            return 'cocos'
        elif page_info['hasReact']:
            print("React ✓")
            return 'react'
        elif page_info['hasVue']:
            print("Vue ✓")
            return 'vue'
        else:
            print("未知")
            return 'unknown'

    def find_cocos_data(self):
        """在 Cocos 页面中查找数据"""
        print("\n查找 Cocos 游戏中的数据...")

        js_code = """
        (function() {
            let scene = cc.director.getScene();
            let results = [];

            function findArrays(node, path = '', depth = 0) {
                if (depth > 8) return;
                let currentPath = path + '/' + node.name;

                // 检查组件
                if (node._components) {
                    node._components.forEach((comp, idx) => {
                        if (!comp) return;
                        let compName = comp.constructor ? comp.constructor.name : 'Unknown';

                        for (let key in comp) {
                            try {
                                if (Array.isArray(comp[key]) && comp[key].length > 5) {
                                    // 取样本分析类型
                                    let sample = comp[key][0];
                                    let sampleType = typeof sample;
                                    let preview = null;

                                    if (typeof sample === 'string') {
                                        preview = comp[key].slice(0, 3);
                                    } else if (typeof sample === 'object' && sample !== null) {
                                        preview = Object.keys(sample).slice(0, 5);
                                    }

                                    results.push({
                                        path: currentPath,
                                        component: compName,
                                        key: key,
                                        length: comp[key].length,
                                        type: sampleType,
                                        preview: preview,
                                        // 只保存较小的数组，避免传输过大
                                        data: comp[key].length < 100 ? comp[key] : comp[key].slice(0, 10)
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

        results = self.page.evaluate(js_code)
        return results

    def extract_data(self):
        """提取数据"""
        print("\n[4/4] 提取数据...")

        # 等待页面稳定（避免 context destroyed 错误）
        print("等待页面加载完成...")
        time.sleep(5)

        # 再次确认页面有 Cocos
        try:
            has_cocos = self.page.evaluate("() => !!window.cc")
            if not has_cocos:
                print("⚠️  当前页面不是 Cocos 游戏页面")
                self._take_screenshot('error_not_cocos_page')
                return None
        except Exception as e:
            print(f"⚠️  无法检查页面: {e}")
            return None

        framework = self.analyze_page()

        if framework == 'cocos':
            results = self.find_cocos_data()
        else:
            print("暂不支持此类型页面")
            return None

        # 显示结果
        print(f"\n找到 {len(results)} 个可能的数组：\n")

        for idx, item in enumerate(results):
            print(f"[{idx}] {item['component']}.{item['key']}")
            print(f"    长度: {item['length']}, 类型: {item['type']}")
            if item['preview']:
                print(f"    预览: {item['preview']}")
            print()

        return results

    def save_data(self, results, index):
        """保存指定的数据"""
        if not results or index >= len(results):
            print("无效的索引")
            return

        item = results[index]

        # 如果数据被截断了，重新获取完整数据
        if item['length'] >= 100:
            print(f"\n重新获取完整数据...")

            js_get_full = f"""
            (function() {{
                let scene = cc.director.getScene();

                function findData(node, targetPath, targetComp, targetKey, path = '') {{
                    let currentPath = path + '/' + node.name;

                    if (currentPath === '{item['path']}') {{
                        if (node._components) {{
                            for (let comp of node._components) {{
                                if (!comp) continue;
                                let compName = comp.constructor ? comp.constructor.name : 'Unknown';
                                if (compName === '{item['component']}' && comp['{item['key']}']) {{
                                    return comp['{item['key']}'];
                                }}
                            }}
                        }}
                    }}

                    if (node.children) {{
                        for (let child of node.children) {{
                            let result = findData(child, targetPath, targetComp, targetKey, currentPath);
                            if (result) return result;
                        }}
                    }}

                    return null;
                }}

                return findData(scene, '{item['path']}', '{item['component']}', '{item['key']}');
            }})();
            """

            full_data = self.page.evaluate(js_get_full)
            if full_data:
                item['data'] = full_data

        # 保存到文件
        output_dir = os.path.join(os.path.dirname(__file__), '..', 'qipu')
        os.makedirs(output_dir, exist_ok=True)

        filename = f"chess_{item['component']}_{item['key']}.json"
        filepath = os.path.join(output_dir, filename)

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(item['data'], f, ensure_ascii=False, indent=2)

        print(f"\n✅ 数据已保存到: {filepath}")
        print(f"数据长度: {len(item['data'])}")

        if item['data'] and len(item['data']) > 0:
            print(f"第一个元素: {item['data'][0]}")

    def interactive_mode(self):
        """交互式模式"""
        results = self.extract_data()

        if not results:
            return

        while True:
            print("\n" + "=" * 60)
            print("选择操作：")
            print("1. 保存某个数组（输入编号）")
            print("2. 保存所有数组")
            print("3. 重新分析页面")
            print("4. 退出")
            print("=" * 60)

            choice = input("请选择: ").strip()

            if choice == '4':
                break
            elif choice == '3':
                results = self.extract_data()
            elif choice == '2':
                for idx in range(len(results)):
                    self.save_data(results, idx)
                print("\n✅ 所有数据已保存")
            else:
                try:
                    idx = int(choice)
                    self.save_data(results, idx)
                except ValueError:
                    print("无效的输入")

    def close(self):
        """关闭浏览器"""
        if self.browser:
            try:
                print("\n是否关闭浏览器？(y/n): ", end='', flush=True)
                choice = input().strip().lower()
                if choice == 'y':
                    self.browser.close()
                    self.playwright.stop()
                    # 删除 CDP endpoint 文件
                    if os.path.exists(self.cdp_endpoint_file):
                        os.remove(self.cdp_endpoint_file)
                    print("✅ 浏览器已关闭")
                else:
                    print("✅ 浏览器保持打开状态")
                    print("   下次运行脚本时会自动连接到此浏览器")
                    print("   （浏览器不会随脚本退出而关闭）")

                    # 不调用 close()，让浏览器保持运行
                    # CDP 连接会断开，但浏览器继续运行
                    if self.playwright:
                        self.playwright.stop()
            except (EOFError, KeyboardInterrupt):
                print("\n⚠️  浏览器保持打开状态")

def main():
    explorer = ChessExplorer()

    try:
        explorer.start()
        explorer.interactive_mode()
    except KeyboardInterrupt:
        print("\n\n用户中断")
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        explorer.close()

if __name__ == '__main__':
    main()
