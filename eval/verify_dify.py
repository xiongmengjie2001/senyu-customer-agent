"""仅验证真实已配置的 Dify，不允许规则模式冒充。"""
import sys,json,os,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'.runtime'))
import httpx
from dotenv import load_dotenv
load_dotenv(ROOT/'.env')
def main():
 base='http://127.0.0.1:'+os.getenv('APP_PORT','8000')+'/api';headers={'Authorization':'Bearer '+os.getenv('DEMO_CUSTOMER_TOKEN','senyu-demo-customer')}
 report={'time':time.strftime('%Y-%m-%d %H:%M:%S'),'passed':False}
 try:
  with httpx.Client(base_url=base,headers=headers,timeout=12) as c:
   assert c.get('/health').json()['mode']=='dify','必须 APP_MODE=dify，不接受规则模式替代'
   def post(path,body=None):
    r=c.post(path,json=body);r.raise_for_status();return r.json()
   s=post('/sessions');sid=s['id'];s=post('/sessions/'+sid+'/messages',{'text':'查物流'});assert s['state']=='多订单待选择'
   assert any(a['tool']=='dify.workflow' for a in s['actions']),'未观察到真实 Dify 工具执行'
   s=post('/sessions/'+sid+'/select',{'order_id':'S20260817001'});assert s['state']=='查询成功'
   s=post('/sessions/'+sid+'/messages',{'text':'帮我催单'})
   if s['state']=='等待用户确认':s=post('/sessions/'+sid+'/confirm',{'confirmation_id':s['pending']['id']})
   assert s['state']=='工单已创建';s=post('/sessions/'+sid+'/handoff');assert s['handoff']['dialogue'] and s['handoff']['actions']
   report.update(passed=True,session_id=sid,state=s['state'])
 except Exception as e:report['error']=str(e)
 (ROOT/'reports').mkdir(exist_ok=True);(ROOT/'reports/dify-live.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(report,ensure_ascii=False));return 0 if report['passed'] else 1
if __name__=='__main__':sys.exit(main())
