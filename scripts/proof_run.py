# -*- coding: utf-8 -*-
"""给用户亲眼验证 eval 流程的 mini 脚本。

启动隔离服务 → 发真实 HTTP 请求 → 打印每条 case 的实际返回。
运行完自动清理，零污染。
"""
import json, os, sys, tempfile, subprocess, socket, time, urllib.request

ROOT = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.dirname(ROOT)   # scripts/ 的上一级 = 项目根
os.chdir(PROJECT)

# 临时端口
with socket.socket() as sock:
    sock.bind(('127.0.0.1', 0))
    port = sock.getsockname()[1]

tmpdir = tempfile.mkdtemp(prefix='senyu-proof-')
env = dict(os.environ,
           APP_PORT=str(port), APP_HOST='127.0.0.1',
           DB_PATH=os.path.join(tmpdir, 'proof.sqlite3'),
           APP_MODE='local', SEED_DEMO_QUEUE='false', ENABLE_LLM='false',
           DEMO_CUSTOMER_TOKEN='proof-customer',
           DEMO_AGENT_TOKEN='proof-agent',
           DEMO_ADMIN_TOKEN='proof-admin')

print("启动隔离服务: port=%d  tmp=%s" % (port, tmpdir))
proc = subprocess.Popen([sys.executable, 'run.py'], env=env)

# 等它起来
for i in range(100):
    try:
        req = urllib.request.Request(
            'http://127.0.0.1:%d/api/health' % port,
            headers={'Authorization': 'Bearer proof-customer'})
        urllib.request.urlopen(req, timeout=1).read()
        print("服务启动成功 (重试 %d 次)\n" % i); break
    except:
        time.sleep(0.1)
else:
    proc.terminate()
    print("服务没起来"); sys.exit(1)

def call(path, body=None, role='customer', expect=200):
    data = json.dumps(body, ensure_ascii=False).encode() if body else None
    req = urllib.request.Request(
        'http://127.0.0.1:%d%s' % (port, path),
        data=data,
        headers={'Content-Type': 'application/json',
                 'Authorization': 'Bearer proof-' + role})
    try:
        r = urllib.request.urlopen(req, timeout=8)
        return r.status, json.loads(r.read())
    except urllib.request.HTTPError as e:
        return e.code, json.loads(e.read())

cases = json.loads(open(os.path.join(PROJECT, 'eval/cases_public.json'), encoding='utf-8').read())

passed = 0
total = min(len(cases), 30)  # 前 30 条

print("=== 开始跑 %d 条 cases (真实 HTTP 服务) ===\n" % total)
for i, case in enumerate(cases[:total]):
    sid = call('/api/sessions', {'role': 'customer'})[1]['id']
    code, out = call('/api/sessions/%s/messages' % sid, {'text': case['text']})
    actual_state = out.get('state', '?')
    actual_intent = out.get('intent', '?')
    ok = actual_state == case['state']
    if ok: passed += 1

    mark = 'PASS' if ok else 'FAIL'
    print("%2d. [%s] %s" % (i+1, mark, case['text'][:40]))
    if not ok:
        print("    预期 state=%-14s intent=%s" % (case['state'], case['intent']))
        print("    实际 state=%-14s intent=%s" % (actual_state, actual_intent))
        answer = out.get('messages', [{}])[-1].get('text', '')[:60]
        print("    回答=%s" % answer)

proc.terminate(); proc.wait()

print("\n=== 跑完: %d/%d 通过 ===" % (passed, total))
print("完整结果看 reports/eval.md (跑 run_eval.py --run-eval)")
