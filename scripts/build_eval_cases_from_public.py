# -*- coding: utf-8 -*-
"""把公开客服日志自动转成 eval/cases.json 格式的测试用例。

工作流:
  1. 读取 data/public/ 下的 json/jsonl 文件
  2. 提取所有用户 utterance (兼容 user/question/query/input/customer 等字段)
  3. 用项目 classify() 逻辑自动标注 intent (复制自 backend/main.py, 避免 import DB)
  4. 启发式预测 state (多订单待选择 / 等待补充信息 / 查询成功 / 已转人工)
  5. 输出 eval/cases_public.json (不覆盖原文件)

可选:
  --merge-old    与原 cases.json 合并为 cases_merged.json
  --run-eval     生成后自动跑 run_eval.py (临时替换, 跑完恢复)
  --max N        最多生成 N 条
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

PUBLIC_DIR = ROOT / "data" / "public"
OLD_CASES = ROOT / "eval" / "cases.json"
NEW_CASES = ROOT / "eval" / "cases_public.json"
MERGED_CASES = ROOT / "eval" / "cases_merged.json"

# ---- 复制自 backend/main.py 的 intent 识别逻辑 ----
INTENT_RULES = [
    ("refund_progress", re.compile(r"退款进度|退款到哪|退款到账|退到哪|售后进度")),
    ("refund",          re.compile(r"退款|退货|取消订单|换货")),
    ("handoff",         re.compile(r"人工|真人|客服接管")),
    ("complaint",       re.compile(r"不满意|气死|生气|太差|忽悠|欺骗|投诉|没解决|还有问题")),
    ("rating",          re.compile(r"谢谢|感谢|解决了|没有问题了|好哒|收到啦|明白了|知道了")),
    ("smalltalk",       re.compile(r"(你好|您好|在吗|嗨|hello|hi)[！!，,。？? ]*", re.I)),
    ("order_list",      re.compile(r"我的订单|查看订单|订单列表")),
    ("urge",            re.compile(r"催|没更新|未更新")),
    ("logistics",       re.compile(r"物流|快递|到哪|什么时候到|啥时候到|啥时到|几时到|何时到|几天到|多久到|什么时候送|包裹|查订单|订单状态|查单|发货|配送")),
    ("aftersale",       re.compile(r"申请售后|申请退|我要退|我要换")),
    ("price",           re.compile(r"多少钱|多少[元块]|价格|售价|价钱|怎么卖|贵不贵")),
    ("browse",          re.compile(r"购买|选购|下单|想买|我要买|买一|买个|商城|逛逛")),
]

# 兜底 knowledge 关键词 (主流程靠 classify 判断, 这里简化)
KNOWLEDGE_PAT = re.compile(
    r"空气炸锅|AF-?\d+|EK-?\d+|TO-?\d+|水壶|多士炉|清洗|容量|功率|使用|会员|积分|活动|优惠"
    r"|退货|退款|运费|换货|售后|参数|温度|款式|型号|规则|政策|到账", re.I
)

RISK_PATTERNS = [
    (re.compile(r"他人|别人|朋友|其他用户|别人的|泄露|手机号|身份证|密码|支付安全|盗号|被盗|银行卡|账号安全"), "安全风险"),
    (re.compile(r"赔偿|赔钱|起诉|律师|法律|烧伤|着火|爆炸|漏电|受伤|媒体|曝光|承诺.*退款|保证.*退款|忽略.*规则|绕过|系统提示|system prompt", re.I), "投诉专席"),
]


def classify(text):
    """与 backend/main.py classify() 逻辑一致, 避免 import DB。"""
    # 先检查 refund_progress (在 refund 之前, 防止 refund 提前命中)
    if INTENT_RULES[0][1].search(text):
        return "refund_progress"
    # 普通关键词规则
    for intent, pat in INTENT_RULES[1:]:
        if pat.search(text):
            return intent
    # 兜底
    if KNOWLEDGE_PAT.search(text):
        return "knowledge"
    return "unknown"


def assess_state(text, intent):
    """启发式预测项目本地规则下会返回的 state。
    逻辑对齐 backend/main.py 的 run() 主流程和 commerce.handle()。"""

    # 1) 先做 full risk 检测 (含金额 > 500)
    for pat, _ in RISK_PATTERNS:
        if pat.search(text):
            return "已转人工"
    amounts = re.findall(r"(\d+(?:\.\d+)?)\s*(?:元|块)", text) + re.findall(r"退(?:款)?\s*(\d+(?:\.\d+)?)", text)
    if intent in ("refund", "aftersale") and any(float(x) > 500 for x in amounts):
        return "已转人工"

    order_no = re.search(r"S\d{11}", text)

    # 2) 投诉/不满意 → 待继续处理
    if intent in ("complaint", "dissatisfaction"):
        return "待继续处理"

    # 3) 打招呼 smalltalk → 智能服务中
    if intent == "smalltalk":
        return "智能服务中"

    # 4) 购买选品 → 选购商品
    if intent in ("buy", "browse"):
        return "选购商品" if not intent else ("选购商品" if intent in ("buy", "browse") else "选购商品")

    # 5) 已知订单号 + 物流/退款类 → 查询成功
    if order_no and intent in ("logistics", "urge", "refund", "aftersale", "refund_progress"):
        return "查询成功"
    if order_no and intent == "price":
        return "查询成功"

    # 6) 物流/催单但没订单号 → 多订单待选择
    if intent in ("logistics", "urge") and not order_no:
        return "多订单待选择"

    # 7) 退款/售后但没订单号 → 等待补充信息
    if intent in ("refund", "aftersale") and not order_no:
        return "等待补充信息"

    # 8) 价格但没商品 → 等待补充信息 (服务端会要求选商品)
    if intent == "price" and not re.search(r"AF-?\d+|EK-?\d+|TO-?\d+|空气炸锅|水壶|多士炉", text, re.I):
        return "等待补充信息"

    # 9) unknown → 等待补充信息
    if intent == "unknown":
        return "等待补充信息"

    # 10) 默认 knowledge / 已知型号 price / rating → 查询成功
    if intent in ("knowledge", "price", "rating", "order_list", "refund_progress"):
        return "查询成功"

    return "查询成功"


def load_public_rows():
    """读取 data/public/ 下所有 json/jsonl, 统一成 {user, bot, scene, source}。"""
    rows = []
    if not PUBLIC_DIR.exists():
        print("! public 目录不存在, 请先运行 scripts/download_public_data.py")
        return rows

    for f in sorted(PUBLIC_DIR.iterdir()):
        if f.suffix not in (".json", ".jsonl"):
            continue
        try:
            raw = f.read_text(encoding="utf-8")
            if f.suffix == ".jsonl":
                arr = [json.loads(l) for l in raw.splitlines() if l.strip()]
            else:
                arr = json.loads(raw)
                if not isinstance(arr, list):
                    arr = [arr]
        except Exception as e:
            print("  x 解析 %s: %s" % (f.name, e))
            continue

        for obj in arr:
            user_text = (
                obj.get("user") or obj.get("question") or obj.get("query")
                or obj.get("input") or obj.get("customer") or obj.get("user_text") or ""
            )
            bot_text = (
                obj.get("bot") or obj.get("answer") or obj.get("response")
                or obj.get("assistant") or obj.get("bot_text") or ""
            )
            scene = obj.get("scene") or obj.get("category") or obj.get("type") or obj.get("scenario") or ""
            if user_text and isinstance(user_text, str) and len(user_text.strip()) >= 2:
                rows.append({"user": user_text.strip(), "bot": bot_text, "scene": scene, "source": f.name})

    print("公开数据总行数: %d" % len(rows))
    return rows


def dedup(rows):
    """按用户 utterance 去重 (空白归一化后)。"""
    seen = {}
    for r in rows:
        key = re.sub(r"\s+", "", r["user"])
        prev = seen.get(key)
        if prev is None or len(r["user"]) > len(prev["user"]):
            seen[key] = r
    print("去重后: %d" % len(seen))
    return list(seen.values())


def build_cases(rows):
    """每行用户 utterance → cases.json 风格的测试用例。"""
    cases = []
    intent_counter = Counter()
    state_counter = Counter()

    for i, r in enumerate(rows):
        text = r["user"]
        intent = classify(text)
        state = assess_state(text, intent)

        # group: 按意图和风险归类
        if state == "已转人工":
            group = "高风险"
        elif intent == "unknown":
            group = "边界"
        elif re.search(r"故障|失败|超时", text):
            group = "异常"
        else:
            group = "正常"

        case = {
            "id": "P%03d" % (i + 1),
            "group": group,
            "text": text,
            "state": state,
            "intent": intent,
            "source_scene": r.get("scene") or intent,
            "source_file": r.get("source", ""),
            "bot": r.get("bot", "")[:300],
        }

        m = re.search(r"S\d{11}", text)
        if m:
            case["order_id"] = m.group()

        cases.append(case)
        intent_counter[intent] += 1
        state_counter[state] += 1

    print("生成 cases: %d" % len(cases))
    print("  intent: %s" % dict(intent_counter))
    print("  state:  %s" % dict(state_counter))
    return cases


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-eval", action="store_true", help="生成后自动跑 eval (临时替换后恢复)")
    ap.add_argument("--max", type=int, default=0, help="最多生成 N 条, 0=全部")
    ap.add_argument("--merge-old", action="store_true", help="与原 cases.json 合并")
    args = ap.parse_args()

    rows = dedup(load_public_rows())
    if args.max:
        rows = rows[:args.max]

    cases = build_cases(rows)

    NEW_CASES.parent.mkdir(parents=True, exist_ok=True)
    NEW_CASES.write_text(json.dumps(cases, ensure_ascii=False, indent=2), encoding="utf-8")
    print("\n已写入: %s" % NEW_CASES)

    if args.merge_old and OLD_CASES.exists():
        old = json.loads(OLD_CASES.read_text(encoding="utf-8"))
        merged = old + cases
        MERGED_CASES.write_text(json.dumps(merged, ensure_ascii=False, indent=2), encoding="utf-8")
        print("已合并: %s (原 %d + 公开 %d = %d)" % (MERGED_CASES, len(old), len(cases), len(merged)))

    if args.run_eval:
        print("\n=== 运行 eval (临时用 cases_public.json) ===")
        backup = OLD_CASES.with_suffix(".json.bak")
        shutil.copy(OLD_CASES, backup)
        shutil.copy(NEW_CASES, OLD_CASES)
        try:
            result = subprocess.run(
                [sys.executable, str(ROOT / "eval" / "run_eval.py")],
                cwd=ROOT
            )
            sys.exit(result.returncode)
        finally:
            shutil.copy(backup, OLD_CASES)
            backup.unlink()
            print("\n已恢复原 cases.json")


if __name__ == "__main__":
    main()
