"""本地伪提供方验证 OpenAI 兼容协议；绝不冒充真实模型效果验收。"""
import os,sys,json,tempfile,threading,socket,time,subprocess
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'.runtime'))
import httpx

def main():
 calls=[]
 class Provider(BaseHTTPRequestHandler):
  def do_POST(self):
   payload=json.loads(self.rfile.read(int(self.headers['Content-Length'])));calls.append({'path':self.path,'model':payload['model']})
   content='OK' if payload['messages'][-1]['content']=='仅回复 OK' else json.dumps({'intent':'price'})
   out=json.dumps({'choices':[{'message':{'role':'assistant','content':content}}]}).encode()
   self.send_response(200);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(out)));self.end_headers();self.wfile.write(out)
  def log_message(self,*args):pass
 provider=ThreadingHTTPServer(('127.0.0.1',0),Provider);threading.Thread(target=provider.serve_forever,daemon=True).start()
 with socket.socket() as sock:sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
 report={'provider':'本地协议测试桩，非真实模型','passed':False}
 with tempfile.TemporaryDirectory(prefix='model-contract-',dir=ROOT/'reports') as folder:
  env=dict(os.environ,APP_MODE='local',APP_PORT=str(port),APP_HOST='127.0.0.1',DB_PATH=str(Path(folder)/'model.sqlite3'),
   ENABLE_LLM='true',PYTHONUTF8='1',LLM_API_KEY='contract-test-placeholder',LLM_BASE_URL=f'http://127.0.0.1:{provider.server_port}/v1',LLM_MODEL='contract-test-model',
   DEMO_CUSTOMER_TOKEN='contract-customer',DEMO_ADMIN_TOKEN='contract-admin',SEED_DEMO_QUEUE='false')
  with open(Path(folder)/'server.log','w',encoding='utf-8') as log:
   proc=subprocess.Popen([sys.executable,str(ROOT/'run.py')],cwd=ROOT,env=env,stdout=log,stderr=log)
   try:
    with httpx.Client(base_url=f'http://127.0.0.1:{port}/api',headers={'Authorization':'Bearer contract-customer'},timeout=10) as c:
     for _ in range(100):
      try:
       if c.get('/health').status_code==200:break
      except httpx.TransportError:time.sleep(.15)
     def post(path,body=None):
      r=c.post(path,json=body);r.raise_for_status();return r.json()
     s=post('/sessions');sid=s['id'];post('/sessions/'+sid+'/product',{'product_id':'AF-35'})
     s=post('/sessions/'+sid+'/messages',{'text':'再帮我估个预算呢'})
     assert s['intent']=='price' and '398.00' in s['messages'][-1]['text'] and s['model_used']
     r=c.post('/admin/model-test',headers={'Authorization':'Bearer contract-admin'});r.raise_for_status();assert r.json()['connected']
     assert len(calls)>=2 and all(x['path']=='/v1/chat/completions' for x in calls)
     report.update(passed=True,calls=calls,validated=['环境变量注入','本地模式可接兼容模型','模型只分类，价格从业务数据读取','管理端连接测试'])
   except Exception as e:report['error']=str(e)
   finally:proc.terminate();proc.wait(timeout=10);log.flush();(ROOT/'reports/model-contract.log').write_text(Path(folder,'server.log').read_text(encoding='utf-8',errors='replace'),encoding='utf-8')
 provider.shutdown();provider.server_close()
 (ROOT/'reports/model-contract.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(report,ensure_ascii=False));return 0 if report['passed'] else 1
if __name__=='__main__':sys.exit(main())
