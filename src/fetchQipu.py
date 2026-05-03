
# \u5b9e\u7528\u5de5\u5177:\u4ece\u5929\u5929\u8c61\u68cb H5 \u62c9\u53d6\u6700\u8fd1\u7684"\u6211\u7684\u68cb\u8c31"\u5230 qipu/raw/<qipuId>.json\u3002
#
# \u884c\u4e3a:
#   1. \u542f\u52a8 persistent Chromium(src/chrome_data),\u5f53\u524d\u56fa\u5b9a\u4e0d\u652f\u6301 headless(\u9996\u6b21\u8981\u626b\u7801)
#   2. \u6253\u5f00 https://h5login.qqchess.qq.com/;\u8f6e\u8be2 fdk.getModel('LoginModel').isLogined()
#      - \u5df2\u767b\u5f55 \u2192 \u8df3\u8fc7\u767b\u5f55\u6b65\u9aa4
#      - \u672a\u767b\u5f55 \u2192 \u81ea\u52a8\u70b9"\u52fe\u534f\u8bae + \u5fae\u4fe1\u767b\u5f55\u6309\u94ae",\u7528\u6237\u624b\u673a\u626b\u7801\u540e\u5728\u7ec8\u7aef\u6572\u56de\u8f66
#   3. hook fdk.Joa.ba('NOTIFY_QIPU_DATA') + 'NOTIFY_QIPU_MY_LIST_UPDATE_INFO';\u8f6e\u8be2 QipuModel.Xj(13, page, 20, 0) \u62c9\u5168\u91cf idlist
#   4. \u7528 qipu/raw/<qipuId>.json \u505a diff,\u53ea\u4e0b\u8f7d\u7f3a\u5931\u7684;\u9006\u5411\u4e00\u4e2a\u4e2a\u8c03 QipuModel.requestGetQipuInfo(id),\u7b49 NOTIFY_QIPU_DATA \u56de\u8c03
#   5. \u6253\u5370\u65b0\u589e/\u7f3a\u5931\u603b\u7ed3,\u5173\u95ed\u6d4f\u89c8\u5668\u9000\u51fa
#
# \u65e0\u4efb\u4f55 LLM / \u4ea4\u4e92\u5f0f\u63a8\u7406,\u6240\u6709\u8def\u5f84\u5199\u6b7b\u3002

import os
import sys
import json
import time
from pathlib import Path

from playwright.sync_api import sync_playwright, TimeoutError as PwTimeoutError


# ---------- \u8def\u5f84\u5e38\u91cf ----------
SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
PROFILE_DIR = SCRIPT_DIR / 'chrome_data'
RAW_DIR = REPO_ROOT / 'qipu' / 'raw'
TARGET_URL = 'https://h5login.qqchess.qq.com/'
VIEWPORT = {'width': 1280, 'height': 720}

# ---------- \u8d85\u65f6\u5e38\u91cf(\u79d2) ----------
PAGE_LOAD_TIMEOUT = 60
FDK_READY_TIMEOUT = 60
LOGIN_WAIT_TIMEOUT = 600         # \u626b\u7801\u6700\u957f\u7b49 10 \u5206\u949f(\u7528\u6237\u518d\u6162\u4e5f\u591f)
LIST_PAGE_TIMEOUT = 15           # \u5355\u9875\u7b49\u5f85
SINGLE_QIPU_TIMEOUT = 10         # \u5355\u5c40\u8be6\u60c5\u7b49\u5f85


# ---------- JS \u7247\u6bb5(\u5199\u6b7b) ----------

JS_FDK_READY = r"""
() => {
  try {
    return !!(window.fdk && fdk.getModel && fdk.Joa && fdk.getModel('LoginModel'));
  } catch (e) { return false; }
}
"""

JS_IS_LOGINED = r"""
() => {
  try {
    const m = fdk.getModel('LoginModel');
    return m && m.isLogined();
  } catch (e) { return false; }
}
"""

# \u767b\u5f55\u9875\u81ea\u52a8\u64cd\u4f5c:\u5148\u68c0\u6d4b checkBox \u5f53\u524d\u72b6\u6001(Cocos Toggle \u7ec4\u4ef6 isChecked,
# \u5907\u9009:\u5b50\u8282\u70b9 checkmark/\u62d8\u4e00\u4e2a active \u7684\u5b50\u8282\u70b9);\u672a\u52fe\u9009\u624d\u70b9,\u907f\u514d\u628a\u9ed8\u8ba4\u5df2\u52fe\u7ed9\u53d6\u6d88\u3002
# \u7136\u540e\u70b9 y \u6700\u5927\u7684 StartBtn_1(\u5fae\u4fe1)\u3002
JS_AUTO_LOGIN_CLICKS = r"""
async () => {
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
  // \u5224\u65ad checkBox \u662f\u5426\u5df2\u7ecf\u52fe\u9009
  function isCheckBoxChecked(cb) {
    if (!cb) return null;
    // 1. Cocos Toggle \u7ec4\u4ef6
    try {
      if (cb.getComponent) {
        const toggle = cb.getComponent('cc.Toggle');
        if (toggle && typeof toggle.isChecked !== 'undefined') return !!toggle.isChecked;
      }
    } catch (e) {}
    // 2. \u904d\u5386\u5b50\u8282\u70b9:\u540d\u5b57\u542b check/mark/on/sel \u4e14 active=true \u89c6\u4e3a\u5df2\u9009
    try {
      if (cb.children) {
        for (const c of cb.children) {
          const n = (c.name || '').toLowerCase();
          if (/(check|mark|sel|on|gou|\u52fe)/.test(n) && c.active) return true;
        }
      }
    } catch (e) {}
    return null; // \u65e0\u6cd5\u63a8\u65ad
  }
  const scene = cc.director.getScene();
  const checkBox = findNodeByName(scene, 'checkBox');
  if (!checkBox) return { ok: false, reason: 'checkBox \u672a\u627e\u5230' };
  const checked = isCheckBoxChecked(checkBox);
  const childrenDebug = (checkBox.children || []).map(c => ({ name: c.name, active: c.active }));
  if (checked === true) {
    // \u5df2\u9ed8\u8ba4\u52fe\u9009,\u8df3\u8fc7\u70b9\u51fb
  } else {
    // \u672a\u9009\u6216\u4e0d\u786e\u5b9a \u2192 \u70b9\u4e00\u4e0b(\u4e0d\u786e\u5b9a\u7684\u60c5\u51b5\u7528\u6237\u53ef\u770b\u5230\u72b6\u6001\u624b\u52a8\u8c03\u6574)
    const pos = cocosNodeToScreen(checkBox);
    await click(pos.x, pos.y);
    await new Promise(r => setTimeout(r, 400));
  }
  const btns = findAllNodes(scene, 'StartBtn_1').sort((a, b) => b.y - a.y);
  if (!btns.length) return { ok: false, reason: 'StartBtn_1 \u672a\u627e\u5230', checked, childrenDebug };
  const pos = cocosNodeToScreen(btns[0]);
  await click(pos.x, pos.y);
  return { ok: true, checked, childrenDebug };
}
"""

# \u5b89\u88c5\u4e8b\u4ef6 hook + \u672c\u5730\u7f13\u5b58\u3002\u5e42\u7b49(\u91cd\u590d\u8c03\u65e0\u526f\u4f5c\u7528)\u3002
# NOTIFY_QIPU_DATA       \u2192 \u5355\u5c40\u8be6\u60c5(iDataType=13)
# NOTIFY_QIPU_MY_LIST_UPDATE_INFO \u2192 \u5217\u8868\u5206\u9875\u8fd4\u56de
JS_INSTALL_HOOK = r"""
() => {
  if (window.__qipuHookInstalled) return { alreadyInstalled: true };
  window.__qipuResults = window.__qipuResults || {};
  window.__qipuListUpdates = window.__qipuListUpdates || [];
  window.__qipuAllEvents = window.__qipuAllEvents || [];
  const orig = fdk.Joa.ba;
  fdk.Joa.ba = function(eventName, payload) {
    try {
      window.__qipuAllEvents.push({ t: Date.now(), eventName });
      if (window.__qipuAllEvents.length > 500) window.__qipuAllEvents.shift();
      if (eventName === 'NOTIFY_QIPU_DATA' && payload && payload.param) {
        const p = payload.param;
        const cdi = p.collectDataInfo;
        if (cdi && cdi.sData && cdi.iDataType === 13) {
          window.__qipuResults[String(cdi.lDataID)] = {
            qipuID: p.qipuID,
            lDataID: cdi.lDataID,
            playersInfo: p.playersInfo,
            sData: cdi.sData,
            t: Date.now(),
          };
        }
      } else if (eventName === 'NOTIFY_QIPU_MY_LIST_UPDATE_INFO') {
        window.__qipuListUpdates.push({ t: Date.now(), payload });
      }
    } catch (e) {}
    return orig.apply(this, arguments);
  };
  window.__qipuHookInstalled = true;
  return { installed: true };
}
"""

# \u8bca\u65ad QipuModel \u5f53\u524d\u72b6\u6001:\u5217\u51fa\u6240\u6709\u5c5e\u6027\u540d\u3001\u6570\u7ec4\u5c5e\u6027\u957f\u5ea6\u3001\u51fd\u6570\u5c5e\u6027\u540d\u3002
# \u7528\u4e8e\u5728\u5b57\u6bb5\u540d\u6df7\u6dc6\u53d8\u5316\u65f6\u5b9a\u4f4d\u65b0\u7684 idlist \u5b58\u653e\u70b9 + \u5206\u9875\u51fd\u6570\u540d\u3002
JS_INTROSPECT_QIPU_MODEL = r"""
() => {
  try {
    const qm = fdk.getModel('QipuModel');
    if (!qm) return { ok: false, reason: 'QipuModel null' };
    const own = Object.getOwnPropertyNames(qm);
    const proto = Object.getOwnPropertyNames(Object.getPrototypeOf(qm) || {});
    const fields = {};
    for (const k of own) {
      try {
        const v = qm[k];
        if (Array.isArray(v)) {
          fields[k] = { type: 'array', len: v.length, sample: v.length ? Object.keys(v[0] || {}).slice(0, 20) : [] };
        } else if (typeof v === 'function') {
          fields[k] = { type: 'function', argc: v.length };
        } else if (v && typeof v === 'object') {
          fields[k] = { type: 'object', keys: Object.keys(v).slice(0, 15) };
        } else {
          fields[k] = { type: typeof v, value: v };
        }
      } catch (e) { fields[k] = { type: 'err', e: String(e) }; }
    }
    const protoFns = proto.filter(k => {
      try { return typeof Object.getPrototypeOf(qm)[k] === 'function'; } catch (e) { return false; }
    });
    return { ok: true, own, protoFns, fields };
  } catch (e) { return { ok: false, reason: String(e) }; }
}
"""

# \u62c9\u4e00\u9875\u5217\u8868(\u6ed1\u52a8\u7a97\u53e3\u5206\u9875: iPageFlag=page, iReqNum=20, iDataType=13, iDirID=0)\u3002
# \u8fd4\u56de\u8be5\u9875\u65b0\u589e\u7684 qipuId \u6570\u7ec4(\u672c\u9875\u8fd4\u56de\u4e2d\u6b64\u524d idlist \u672a\u6536\u5165\u8fc7\u7684\u90e8\u5206)\u3002
JS_FETCH_ONE_LIST_PAGE = r"""
async (page) => {
  const qm = fdk.getModel('QipuModel');
  // Xj \u4f1a\u91cd\u65b0\u586b\u5145 Wfb\u3002\u4e3a\u4e86\u53ef\u9760\u5224\u65ad "\u672c\u9875\u7684\u7ed3\u679c\u5230\u4e86",
  // \u5148\u624b\u52a8\u6e05\u7a7a Wfb,\u7136\u540e\u8f6e\u8be2 Wfb.length > 0(\u6216\u903e\u65f6)\u3002
  try { if (Array.isArray(qm.Wfb)) qm.Wfb.length = 0; } catch (e) {}
  try {
    qm.Xj(13, page, 20, 0);
  } catch (e) {
    return { ok: false, reason: 'Xj\u629b\u51fa: ' + String(e) };
  }
  const t0 = Date.now();
  let Wfb = qm.Wfb || [];
  while (Wfb.length === 0 && Date.now() - t0 < 8000) {
    await new Promise(r => setTimeout(r, 30));
    Wfb = qm.Wfb || [];
  }
  // \u518d\u8ffd\u52a0\u7b49\u5f85,\u5bb9\u5fcd\u540e\u7eed\u8865\u5145(\u89c4\u907f\u53ea\u8bfb\u5230 1 \u6761\u7684\u65a9\u65ad\u573a\u666f)
  await new Promise(r => setTimeout(r, 150));
  Wfb = qm.Wfb || [];
  const ids = Wfb.map(x => String(x && (x.qipuId || x.lDataID || x.qipuID || x.lQipuID) || '')).filter(Boolean);
  return { ok: true, ids, rawCount: Wfb.length, waitedMs: Date.now() - t0 };
}
"""

# \u8c03\u5355\u5c40\u8be6\u60c5 API\u3002\u7f13\u5b58\u547d\u4e2d\u65f6\u8fd4\u56de\u5f88\u5feb(<100ms);\u6ca1\u547d\u4e2d\u4e5f\u4f1a\u53d1\u7f51\u7edc\u8bf7\u6c42,\u6b63\u5e38\u6570\u79d2\u5185\u5230\u3002
# qipuId \u4f20 String;\u4e0d\u6253 sData \u683c\u5f0f,\u4fdd\u7559\u539f\u672c\u3002
JS_REQUEST_ONE_QIPU = r"""
async (qipuId) => {
  try {
    delete window.__qipuResults[qipuId];
    const qm = fdk.getModel('QipuModel');
    qm.requestGetQipuInfo(String(qipuId));
    const t0 = Date.now();
    while (!window.__qipuResults[qipuId] && Date.now() - t0 < 10000) {
      await new Promise(r => setTimeout(r, 50));
    }
    if (!window.__qipuResults[qipuId]) return { ok: false, reason: 'timeout' };
    return { ok: true, payload: window.__qipuResults[qipuId] };
  } catch (e) {
    return { ok: false, reason: String(e) };
  }
}
"""


# ---------- Python \u8fb9\u7684\u7eaf\u51fd\u6570 ----------

def loadExistingIds():
    # \u8bfb\u672c\u5730 qipu/raw/*.json,\u8fd4\u56de\u5df2\u5b58\u5728\u7684 qipuId \u96c6\u5408
    if not RAW_DIR.exists():
        return set()
    ids = set()
    for name in os.listdir(RAW_DIR):
        if not name.endswith('.json') or name.startswith('_'):
            continue
        ids.add(name[:-len('.json')])
    return ids


def writePayload(qipuId, payload):
    # \u5199 qipu/raw/<qipuId>.json(pretty, ensure_ascii=False);\u5df2\u5b58\u5728\u65f6\u8986\u76d6
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    outPath = RAW_DIR / f'{qipuId}.json'
    with open(outPath, 'w', encoding='utf-8') as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    return outPath


# ---------- \u6d41\u7a0b\u6b65\u9aa4 ----------

def waitForFdk(page):
    # \u8f6e\u8be2 fdk \u5c31\u7eea(\u767b\u5f55\u9875\u5982\u6b64,\u8fdb\u5165 game \u540e\u4ecd\u7136\u6709 fdk)
    deadline = time.time() + FDK_READY_TIMEOUT
    while time.time() < deadline:
        try:
            if page.evaluate(JS_FDK_READY):
                return
        except Exception:
            pass
        time.sleep(0.5)
    raise RuntimeError(f"fdk \u672a\u5728 {FDK_READY_TIMEOUT}s \u5185\u5c31\u7eea")


def ensureLogined(page):
    # \u8fd4\u56de True=\u5df2\u767b\u5f55(\u76f4\u63a5\u7528 profile cookie);False=\u521a\u626b\u7801\u767b\u5165
    page.goto(TARGET_URL, wait_until='networkidle', timeout=PAGE_LOAD_TIMEOUT * 1000)
    waitForFdk(page)

    if page.evaluate(JS_IS_LOGINED):
        print('[login] profile \u6709\u6548 token,\u5df2\u767b\u5f55,\u8df3\u8fc7\u626b\u7801')
        return True

    print('[login] \u672a\u767b\u5f55,\u81ea\u52a8\u70b9\u4e0b "\u52fe\u534f\u8bae + \u5fae\u4fe1\u767b\u5f55"')
    result = page.evaluate(JS_AUTO_LOGIN_CLICKS)
    if not result or not result.get('ok'):
        raise RuntimeError(f"\u81ea\u52a8\u70b9\u51fb\u5931\u8d25: {result}")

    print('[login] \u8bf7\u5728\u5f39\u51fa\u7684\u4e8c\u7ef4\u7801\u91cc\u7528\u5fae\u4fe1\u626b\u7801,\u6388\u6743\u5b8c\u6210\u540e\u56de\u8f66\u7ee7\u7eed...')
    try:
        input()
    except EOFError:
        pass

    deadline = time.time() + LOGIN_WAIT_TIMEOUT
    while time.time() < deadline:
        try:
            if page.evaluate(JS_IS_LOGINED):
                print('[login] \u68c0\u6d4b\u5230\u767b\u5f55\u6210\u529f')
                return False
        except Exception:
            pass
        time.sleep(1.0)
    raise RuntimeError(f"\u626b\u7801\u540e {LOGIN_WAIT_TIMEOUT}s \u5185\u4ecd\u672a\u767b\u5f55")


def waitForQipuModel(page):
    # \u8fdb\u5165 game \u573a\u666f\u540e fdk.getModel('QipuModel') \u624d\u53ef\u7528\u3002
    # \u767b\u5f55\u5b8c\u5f80\u5f80\u4f1a\u81ea\u52a8\u8df3\u8f6c\u5230\u4e3b\u573a\u666f,\u7b49\u4e00\u4e0b\u5373\u53ef\u3002
    deadline = time.time() + 60
    while time.time() < deadline:
        try:
            ok = page.evaluate("""() => {
                try {
                    const q = fdk.getModel('QipuModel');
                    return !!(q && typeof q.Xj === 'function' && typeof q.requestGetQipuInfo === 'function');
                } catch (e) { return false; }
            }""")
            if ok:
                return
        except Exception:
            pass
        time.sleep(1.0)
    raise RuntimeError("QipuModel \u672a\u5728 60s \u5185\u5c31\u7eea(\u767b\u5f55\u540e\u53ef\u80fd\u8fd8\u5728\u52a0\u8f7d\u4e3b\u573a\u666f)")


def installHook(page):
    r = page.evaluate(JS_INSTALL_HOOK)
    print(f'[hook] {r}')


def fetchIdList(page):
    # \u6ed1\u52a8\u5206\u9875\u62c9 idlist,\u81ea\u52a8\u5224\u65ad\u65e0\u65b0\u589e\u5373\u505c
    # iDataType=13 \u7684\u5206\u9875\u89c4\u5219(\u5b9e\u6d4b): page=1 \u8fd4\u56de id[0..19],page=2 \u8fd4\u56de id[1..20],...
    # \u56e0\u6b64\u4ee5 QipuModel.Wfb \u548c\u4e0a\u4e00\u8f6e\u5b8c\u5168\u76f8\u540c \u2192 \u6ca1\u65b0\u7684\u4e86 \u2192 \u505c
    seenIds = []
    seenSet = set()
    page_idx = 1
    prev_tuple = None
    while True:
        r = page.evaluate(JS_FETCH_ONE_LIST_PAGE, page_idx)
        if not r.get('ok'):
            print(f'[list] page={page_idx} \u5931\u8d25: {json.dumps(r, ensure_ascii=False)}')
            break
        ids = r.get('ids', [])
        tup = tuple(ids)
        newly = [i for i in ids if i not in seenSet]
        for i in newly:
            seenSet.add(i)
            seenIds.append(i)
        print(f'[list] page={page_idx} \u62c9\u5230 {len(ids)} \u6761,\u7d2f\u8ba1\u552f\u4e00 {len(seenIds)} \u4e2a(\u672c\u9875\u65b0\u589e {len(newly)})')
        if prev_tuple is not None and tup == prev_tuple:
            print('[list] \u672c\u9875\u4e0e\u4e0a\u4e00\u9875\u5b8c\u5168\u76f8\u540c,\u505c\u6b62')
            break
        if newly == [] and prev_tuple is not None:
            print('[list] \u672c\u9875\u65e0\u65b0\u589e id,\u505c\u6b62')
            break
        prev_tuple = tup
        page_idx += 1
        # \u5b89\u5168\u7eff\u5730(\u9632\u6b62\u4e0d\u6536\u655b)
        if page_idx > 200:
            print('[list] \u9875\u7801\u8d85\u8fc7 200,\u5f3a\u5236\u505c\u6b62')
            break
        time.sleep(0.2)
    return seenIds


def downloadMissing(page, missingIds):
    # \u4f9d\u6b21\u4e0b\u8f7d;\u6210\u529f\u843d\u76d8,\u5931\u8d25\u7d2f\u8ba1
    ok, fail = [], []
    total = len(missingIds)
    for idx, qid in enumerate(missingIds, start=1):
        r = page.evaluate(JS_REQUEST_ONE_QIPU, qid)
        if r.get('ok'):
            writePayload(qid, r['payload'])
            ok.append(qid)
            print(f'[fetch {idx}/{total}] {qid} OK')
        else:
            fail.append((qid, r.get('reason')))
            print(f'[fetch {idx}/{total}] {qid} FAIL: {r.get("reason")}')
    return ok, fail


def main():
    print(f'[boot] profile = {PROFILE_DIR}')
    print(f'[boot] raw dir = {RAW_DIR}')

    existingIds = loadExistingIds()
    print(f'[boot] \u672c\u5730\u5df2\u6709 {len(existingIds)} \u5c40')

    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            user_data_dir=str(PROFILE_DIR),
            headless=False,
            viewport=VIEWPORT,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--no-first-run',
            ],
        )
        try:
            page = context.pages[0] if context.pages else context.new_page()
            page.set_default_timeout(PAGE_LOAD_TIMEOUT * 1000)

            ensureLogined(page)
            waitForQipuModel(page)
            installHook(page)

            introspect = page.evaluate(JS_INTROSPECT_QIPU_MODEL)
            print('[introspect] QipuModel =')
            print(json.dumps(introspect, ensure_ascii=False, indent=2))

            remoteIds = fetchIdList(page)
            print(f'[list] \u8fdc\u7aef\u53ef\u62c9 {len(remoteIds)} \u4e2a\u552f\u4e00 qipuId')

            remoteSet = set(remoteIds)
            missing = [i for i in remoteIds if i not in existingIds]
            extraLocal = existingIds - remoteSet
            print(f'[diff] \u672c\u5730\u7f3a {len(missing)} \u5c40 | \u8fdc\u7aef\u6ca1\u7684\u672c\u5730\u72ec\u6709 {len(extraLocal)} \u5c40(\u5df2\u843d\u76d8,\u4fdd\u7559)')

            if not missing:
                print('[fetch] \u65e0\u9700\u4e0b\u8f7d')
                okList, failList = [], []
            else:
                okList, failList = downloadMissing(page, missing)

            print('========================================')
            print(f'\u65b0\u589e {len(okList)} \u5c40,\u5931\u8d25 {len(failList)} \u5c40,\u672c\u5730\u73b0\u5171 {len(existingIds) + len(okList)} \u5c40')
            if failList:
                for qid, reason in failList:
                    print(f'  FAIL {qid}: {reason}')
        finally:
            context.close()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('\n\u4e2d\u65ad')
        sys.exit(130)
