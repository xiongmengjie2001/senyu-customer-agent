"""生成可导入 Dify 1.18.0 的 Chatflow；依据官方 DSL fixtures 构造。"""
import sys,json,uuid
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'.runtime'))
import yaml
nodes=[];edges=[]
def add(id,type,title,**data):
 x=len(nodes)*330;nodes.append({'id':id,'type':'custom','position':{'x':x,'y':240},'positionAbsolute':{'x':x,'y':240},'width':244,'height':100,'sourcePosition':'right','targetPosition':'left','data':dict(type=type,title=title,desc='',selected=False,**data)})
 if len(nodes)>1:
  prev=nodes[-2];edges.append({'id':prev['id']+'-'+id,'source':prev['id'],'target':id,'sourceHandle':'source','targetHandle':'target','type':'custom','data':{'sourceType':prev['data']['type'],'targetType':type,'isInIteration':False,'isInLoop':False}})
def code(id,title,source,variables,outputs):
 add(id,'code',title,code_language='python3',code=source,variables=[{'variable':name,'value_selector':sel,'value_type':'string'} for name,sel in variables],outputs={name:{'type':'string','children':None} for name in outputs})
def http(id,title,path,selector):
 add(id,'http-request',title,method='post',url='{{#env.BACKEND_URL#}}'+path,authorization={'type':'no-auth'},headers='Content-Type:application/json\nAuthorization:Bearer {{#env.TOOLS_TOKEN#}}',params='',body={'type':'raw-text','data':[{'id':str(uuid.uuid4()),'key':'','type':'text','value':'{{#'+selector+'#}}'}]},timeout={'connect':3,'read':5,'write':3},retry_config={'retry_enabled':False,'max_retries':1,'retry_interval':100},ssl_verify=True)
add('start','start','开始 · 多轮会话',variables=[{'label':'业务会话 ID','variable':'session_id','type':'text-input','required':True,'max_length':64,'options':[]}])
code('prepare','安全序列化输入','import json\ndef main(query: str):\n    return {"payload":json.dumps({"text":query},ensure_ascii=False)}',[('query',['sys','query'])],['payload'])
http('route','意图识别 / 风险标记','/api/tools/route','prepare.payload')
http('rag','FAISS · 已发布知识检索','/api/tools/knowledge','prepare.payload')
code('serialize','组装受控业务请求','import json\ndef main(query: str, session_id: str, decision: str, sources: str):\n    parsed=json.loads(decision)\n    if "intent" not in parsed: raise ValueError("意图工具失败")\n    if "sources" not in json.loads(sources): raise ValueError("检索工具失败")\n    return {"payload":json.dumps({"session_id":session_id,"text":query,"decision":decision,"sources":sources},ensure_ascii=False)}',[('query',['sys','query']),('session_id',['start','session_id']),('decision',['route','body']),('sources',['rag','body'])],['payload'])
http('process','状态流转 / 规则闸门 / 业务工具','/api/tools/process','serialize.payload')
code('validate','核验结果，禁止谎报成功','import json\ndef main(body: str):\n    data=json.loads(body)\n    if "id" not in data or "state" not in data: raise ValueError("业务工具失败，禁止声称成功")\n    return {"result":body}',[('body',['process','body'])],['result'])
add('answer','answer','返回结构化会话',answer='{{#validate.result#}}',variables=[])
env=[{'id':str(uuid.uuid4()),'name':'BACKEND_URL','value_type':'string','value':'http://host.docker.internal:8000','selector':['env','BACKEND_URL']},{'id':str(uuid.uuid4()),'name':'TOOLS_TOKEN','value_type':'secret','value':'replace-with-local-tool-secret','selector':['env','TOOLS_TOKEN']}]
dsl={'app':{'name':'森屿生活客服 · 受控 Agent','description':'Dify 编排意图、FAISS 检索与受控工具；业务规则/确认/归属校验由后端执行。','mode':'advanced-chat','icon':'🌿','icon_background':'#E6EEDD','use_icon_as_answer_icon':False},'dependencies':[],'kind':'app','version':'0.3.1','workflow':{'conversation_variables':[],'environment_variables':env,'features':{'file_upload':{'enabled':False},'opening_statement':'','retriever_resource':{'enabled':False},'sensitive_word_avoidance':{'enabled':False},'speech_to_text':{'enabled':False},'suggested_questions':[],'suggested_questions_after_answer':{'enabled':False},'text_to_speech':{'enabled':False}},'graph':{'nodes':nodes,'edges':edges,'viewport':{'x':0,'y':0,'zoom':.6}}}}
(ROOT/'dify').mkdir(exist_ok=True);(ROOT/'dify/senyu-chatflow.yml').write_text(yaml.safe_dump(dsl,allow_unicode=True,sort_keys=False),encoding='utf-8')
# 知识库是后端 FAISS，导出 Markdown 供运营审阅，不重复维护另一套 Dify 数据集。
sys.path.insert(0,str(ROOT));from backend.seed import KNOWLEDGE
(ROOT/'data/knowledge').mkdir(parents=True,exist_ok=True)
for k in KNOWLEDGE:(ROOT/'data/knowledge'/f'{k["id"]}.md').write_text(f'# {k["title"]}\n\n状态：{k["status"]} / v{k["version"]} / 负责人：{k["owner"]}\n\n{k["content"]}\n',encoding='utf-8')
print('Generated dify/senyu-chatflow.yml and knowledge documents')
