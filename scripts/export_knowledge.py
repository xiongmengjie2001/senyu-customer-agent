"""导出当前知识种子的可读文档，不改动运营数据库和 Dify DSL。"""
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from backend.seed import KNOWLEDGE
folder=ROOT/'data/knowledge';folder.mkdir(parents=True,exist_ok=True)
for k in KNOWLEDGE:
 (folder/(k['id']+'.md')).write_text(f'# {k["title"]}\n\n状态：{k["status"]} / v{k["version"]} / 负责人：{k["owner"]}\n\n{k["content"]}\n',encoding='utf-8')
print(f'Exported {len(KNOWLEDGE)} seed documents')
