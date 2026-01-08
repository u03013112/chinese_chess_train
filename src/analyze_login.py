#!/usr/bin/env python3
"""
分析天天象棋的登录机制

使用方法：
1. 先手动登录天天象棋
2. 运行此脚本
3. 脚本会提取所有登录相关信息
"""

from playwright.sync_api import sync_playwright
import json
import os

def analyze_login():
    print("=" * 60)
    print("天天象棋登录机制分析")
    print("=" * 60)

    with sync_playwright() as p:
        # 使用持久化上下文，保留登录状态
        user_data_dir = os.path.join(os.path.dirname(__file__), 'chrome_data')

        browser = p.chromium.launch_persistent_context(
            user_data_dir=user_data_dir,
            headless=False
        )

        page = browser.pages[0] if browser.pages else browser.new_page()

        # 访问天天象棋
        print("\n[1/3] 访问天天象棋...")
        page.goto('https://h5login.qqchess.qq.com/')

        print("\n请完成登录...")
        input("登录完成后按回车继续...")

        print("\n[2/3] 分析登录信息...")

        # 获取所有 Cookie
        cookies = browser.cookies()
        print("\n===== Cookies =====")
        for cookie in cookies:
            if any(keyword in cookie['name'].lower() for keyword in ['token', 'session', 'auth', 'login', 'user', 'openid', 'uid']):
                print(f"  {cookie['name']}: {cookie['value'][:50]}...")  # 只显示前50个字符
                print(f"    domain: {cookie['domain']}")
                print(f"    expires: {cookie.get('expires', 'session')}")

        # 获取 localStorage
        local_storage = page.evaluate("""
        () => {
            let data = {};
            for (let i = 0; i < localStorage.length; i++) {
                let key = localStorage.key(i);
                data[key] = localStorage.getItem(key);
            }
            return data;
        }
        """)

        print("\n===== localStorage =====")
        for key, value in local_storage.items():
            if any(keyword in key.lower() for keyword in ['token', 'session', 'auth', 'login', 'user', 'openid', 'uid']):
                print(f"  {key}: {value[:100]}...")  # 只显示前100个字符

        # 获取 sessionStorage
        session_storage = page.evaluate("""
        () => {
            let data = {};
            for (let i = 0; i < sessionStorage.length; i++) {
                let key = sessionStorage.key(i);
                data[key] = sessionStorage.getItem(key);
            }
            return data;
        }
        """)

        print("\n===== sessionStorage =====")
        for key, value in session_storage.items():
            if any(keyword in key.lower() for keyword in ['token', 'session', 'auth', 'login', 'user', 'openid', 'uid']):
                print(f"  {key}: {value[:100]}...")

        # 保存完整信息到文件
        output = {
            'cookies': cookies,
            'localStorage': local_storage,
            'sessionStorage': session_storage,
            'url': page.url
        }

        output_file = os.path.join(os.path.dirname(__file__), 'login_info.json')
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output, f, ensure_ascii=False, indent=2)

        print(f"\n[3/3] 完整信息已保存到: {output_file}")

        print("\n" + "=" * 60)
        print("分析完成！")
        print("=" * 60)

        input("\n按回车关闭...")
        browser.close()

if __name__ == '__main__':
    analyze_login()
