# -*- coding: utf-8 -*-
"""从 ModelScope 下载中文电商客服公开对话数据集（纯 Python，Windows 安全）。

拉取三份 Apache 2.0 可商用的公开语料：
  1. QingshanAI/ecom-customer-service-synthetic  - 通用售前咨询
  2. QingshanAI/ecom-logistics-synthetic         - 物流查询
  3. QingshanAI/ecom-after-sale-synthetic        - 售后维权

输出: data/public/*.json|jsonl
"""
import json
import os
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "public"
OUT.mkdir(parents=True, exist_ok=True)

DATASETS = [
    ("QingshanAI/ecom-customer-service-synthetic", "通用客服"),
    ("QingshanAI/ecom-logistics-synthetic",         "物流查询"),
    ("QingshanAI/ecom-after-sale-synthetic",        "售后维权"),
]


def try_sdk(org_name):
    """优先用 modelscope SDK 下载。"""
    try:
        from modelscope import snapshot_download
    except ImportError:
        return False
    try:
        path = snapshot_download(
            org_name,
            local_dir=str(OUT / org_name.replace("/", "__")),
            local_dir_use_symlinks=False,
        )
    except Exception as e:
        print("  ! SDK 下载失败: %s" % e)
        return False
    found = []
    for ext in ("*.json", "*.jsonl", "*.csv", "*.txt"):
        found.extend(Path(path).rglob(ext))
    for f in found:
        if f.stat().st_size == 0:
            continue
        dest = OUT / (org_name.replace("/", "__") + "__" + f.name)
        shutil.copy(f, dest)
        print("  + %s (%d bytes)" % (dest.name, dest.stat().st_size))
    return bool(found)


def try_requests_direct(org_name):
    """兜底：直接 HTTP GET 常见文件名。"""
    try:
        import requests
    except ImportError:
        print("  ! requests 未安装")
        return False
    candidates = [
        "data.jsonl", "train.jsonl", "data.json",
        "train.json", "clean_data.jsonl", "dialogues.jsonl",
        "dialogues.json", "chat.jsonl", "chat.json",
    ]
    repo = org_name.replace("/", "__")
    got = []
    for fname in candidates:
        url = "https://modelscope.cn/api/v1/repos/%s/resolve/master/%s" % (org_name, fname)
        try:
            r = requests.get(url, timeout=15, headers={"Accept": "*/*"})
            if r.status_code == 200 and len(r.content) > 100:
                dest = OUT / ("%s__%s" % (repo, fname))
                dest.write_bytes(r.content)
                print("  + %s (%d bytes)" % (fname, len(r.content)))
                got.append(fname)
        except Exception as e:
            print("  x %s: %s" % (fname, e))
    if got:
        return True
    print("  ! 自动下载失败")
    print("    手动下载: https://modelscope.cn/datasets/%s/files" % org_name)
    print("    放到: %s" % OUT)
    return False


def preview(path):
    """打印文件首条样本字段。"""
    if not path.exists():
        return
    try:
        raw = path.read_text(encoding="utf-8")
        if path.suffix == ".jsonl":
            first = json.loads(raw.splitlines()[0])
        else:
            arr = json.loads(raw)
            first = arr[0] if isinstance(arr, list) else arr
        print("    字段: %s" % list(first.keys()))
        for k, v in first.items():
            sv = str(v)[:80].replace("\n", " ")
            print("      %s: %s" % (k, sv))
    except Exception as e:
        print("    解析失败: %s" % e)


def main():
    print("目标: %s" % OUT)
    existing = list(OUT.iterdir()) if OUT.exists() else []
    print("已有文件: %s\n" % ([p.name for p in existing] if existing else "(空)"))

    ok = 0
    for org, label in DATASETS:
        print("[%s] %s" % (label, org))
        if try_sdk(org) or try_requests_direct(org):
            ok += 1
        print()

    print("结果: %d/%d 个数据集就绪" % (ok, len(DATASETS)))
    if not ok:
        print("\n安装依赖后重试:")
        print("  pip install requests")
        print("  pip install modelscope   (可选，成功率更高)")
        sys.exit(1)

    print("\n--- 文件预览 ---")
    for f in sorted(OUT.iterdir()):
        if f.suffix in (".json", ".jsonl"):
            preview(f)

    print("\n完成。下一步: python scripts/build_eval_cases_from_public.py")


if __name__ == "__main__":
    main()
