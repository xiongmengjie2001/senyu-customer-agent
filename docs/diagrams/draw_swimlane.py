"""绘制可用于项目介绍的高分辨率泳道图，同时保留可编辑 SVG。"""
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
import html, math

OUT=Path(__file__).resolve().parent
W,H=1920,3040
im=Image.new('RGB',(W,H),'#F7F9F5');d=ImageDraw.Draw(im)
svg=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}"><rect width="100%" height="100%" fill="#F7F9F5"/>']
FONT='C:/Windows/Fonts/msyh.ttc'
GREEN='#245B48';INK='#213E34';MUTED='#6C8175';LINE='#D9E3D8';BLUE='#32688C';AMBER='#A97822';RED='#A8524E'
def rect(box,fill,outline=None,r=18,width=2,dashed=False):
 d.rounded_rectangle(box,r,fill=fill,outline=outline,width=width)
 x,y,x2,y2=box
 svg.append(f'<rect x="{x}" y="{y}" width="{x2-x}" height="{y2-y}" rx="{r}" fill="{fill}" stroke="{outline or "none"}" stroke-width="{width}"'+(' stroke-dasharray="8 6"' if dashed else '')+'/>')
def text(x,y,s,size=24,fill=INK,anchor='mm'):
 font=ImageFont.truetype(FONT,size)
 d.text((x,y),s,font=font,fill=fill,anchor=anchor)
 align='middle' if anchor.startswith('m') else 'start'
 svg.append(f'<text x="{x}" y="{y}" font-family="Microsoft YaHei,Noto Sans CJK SC,sans-serif" font-size="{size}" text-anchor="{align}" dominant-baseline="middle" fill="{fill}">{html.escape(s)}</text>')
def path(points,color=MUTED,width=3,dashed=False,arrow=True):
 if dashed:
  for a,b in zip(points,points[1:]):
   length=math.dist(a,b)
   for start in range(0,int(length),16):
    end=min(start+9,length);p=(a[0]+(b[0]-a[0])*start/max(length,1),a[1]+(b[1]-a[1])*start/max(length,1));q=(a[0]+(b[0]-a[0])*end/max(length,1),a[1]+(b[1]-a[1])*end/max(length,1));d.line((p,q),fill=color,width=width)
 else:d.line(points,fill=color,width=width,joint='curve')
 svg.append('<polyline points="'+' '.join(f'{x},{y}' for x,y in points)+f'" fill="none" stroke="{color}" stroke-width="{width}" stroke-linejoin="round"'+(' stroke-dasharray="9 7"' if dashed else '')+'/>')
 if arrow:
  a,b=points[-2:];ang=math.atan2(b[1]-a[1],b[0]-a[0]);tri=[b,(b[0]-13*math.cos(ang-.45),b[1]-13*math.sin(ang-.45)),(b[0]-13*math.cos(ang+.45),b[1]-13*math.sin(ang+.45))];d.polygon(tri,fill=color);svg.append('<polygon points="'+' '.join(f'{x},{y}' for x,y in tri)+f'" fill="{color}"/>')
def label(x,y,s,color=MUTED):
 width=d.textlength(s,font=ImageFont.truetype(FONT,20))+18
 rect((x-width/2,y-17,x+width/2,y+17),'#F7F9F5',r=5);text(x,y,s,20,color)
CX=[180+312*i for i in range(6)]
def node(col,row,lines,kind='normal',num=None,y=None):
 x=CX[col];y=330+148*row if y is None else y
 fill,stroke={'normal':('#FFFFFF',LINE),'user':('#EDF3E7','#CADAC3'),'ai':('#EDF1F8','#B9CADD'),'decision':('#FCF2DC','#D6B36A'),'human':('#F8EAE7','#D6AFAB'),'success':('#DFEDE4','#8EB69F')}[kind]
 rect((x-124,y-46,x+124,y+46),fill,stroke,r=22 if kind=='user' else 12,dashed=kind=='ai')
 for i,line in enumerate(lines):
  size=24
  while size>18 and d.textlength(line,font=ImageFont.truetype(FONT,size))>228:size-=1
  text(x,y+(i-(len(lines)-1)/2)*30,line,size,INK)
 if num is not None:
  rect((x-136,y-58,x-98,y-20),GREEN,r=19);text(x-117,y-39,str(num),21,'#FFFFFF')
 return x,y
N={}
def n(id,c,r,lines,kind='normal',num=None):N[id]=node(c,r,lines,kind,num)
def edge(a,b,color=MUTED,labeltext=None,dashed=False):
 ax,ay=N[a];bx,by=N[b]
 if ay==by:
  sign=1 if bx>ax else -1;p=[(ax+124*sign,ay),(bx-132*sign,by)]
 elif ax==bx:p=[(ax,ay+46),(bx,by-53)]
 else:
  mid=(ay+by)/2;p=[(ax,ay+46),(ax,mid),(bx,mid),(bx,by-53)]
 path(p,color,dashed=dashed)
 if labeltext:
  if ay==by:label((p[0][0]+p[-1][0])/2,ay-22,labeltext,color)
  elif ax==bx:label(ax+79,(ay+by)/2,labeltext,color)
  else:label((ax+bx)/2,(ay+by)/2-21,labeltext,color)

text(52,64,'森屿生活 · 电商客服 Agent 泳道图',44,GREEN,'lm')
text(52,120,'一位消费者的完整旅程：查物流 → 确认催单 → 工单反馈 → 人工接管',26,MUTED,'lm')
text(52,165,'实线：本地闭环已验证    虚线：Dify 目标编排 / 条件分支    当前 Dify 与模型接入待实测',21,MUTED,'lm')
roles=[('消费者','提出诉求 / 补充 / 确认'),('三端前端','让过程与结果看得见'),('Dify / AI 编排','理解意图，调用受控工具'),('后端规则闸门','身份 / 条件 / 权限 / 状态'),('业务工具与知识库','查数据 / 检索 / 写工单'),('人工客服','审核高风险 / 处理例外')]
for i,(title,sub) in enumerate(roles):
 x=24+312*i;rect((x,212,x+312,2200),'#EEF3EC' if i%2==0 else '#F8FAF6',r=0)
 rect((x+6,212,x+306,286),GREEN if i in (0,3) else '#DCE7D9',r=12)
 text(CX[i],238,title,25,'#FFFFFF' if i in (0,3) else INK)
 text(CX[i],268,sub,17,'#E0EBDD' if i in (0,3) else MUTED)
 if i:path([(x,292),(x,2190)],LINE,1,arrow=False)

n('ask',0,0,['“我的包裹到哪了？”'],'user',1);n('loading',1,0,['显示正在查询','接收用户问题'])
n('intent',2,1,['意图识别：查物流','提取订单等信息'],'ai',2);n('risk',3,1,['先查风险与权限','是否属于 L3？'],'decision');n('riskhuman',5,1,['禁止自动执行','转有权限人工审核'],'human')
n('ownership',3,2,['校验当前用户','只允许查询本人订单'],num=3);n('orders',4,2,['查询订单列表','返回两个候选订单'])
n('multiple',3,3,['多订单消歧规则','候选订单 ≥ 2？'],'decision');n('choosecard',1,3,['展示订单选择卡片','运输中 / 待发货'])
n('select',0,4,['选择运输中订单','S20260817001'],'user',4);n('bind',3,4,['再次校验归属','绑定本轮关联订单'])
n('logtool',4,5,['L1 · 自动只读查询','顺丰轨迹 / 49h 未更新']);n('logui',1,5,['展示预估送达 + 轨迹','提供催单 / 转人工入口'],num=5)
n('urge',0,6,['“帮我催一下物流”'],'user');n('threshold',3,6,['是否已发货且','轨迹 ≥ 48h 未更新？'],'decision',6)
n('confirmcard',1,7,['L2 · 四要素确认卡','操作 / 订单 / 结果 / 撤销'])
n('confirm',0,8,['核对内容','点击“确认提交”'],'user',7);n('token',3,8,['校验一次性确认凭据','复核条件 / 防止重复执行'])
n('tickettool',4,9,['创建物流催单工单','记录审计与操作结果'],num=8);n('ticketui',1,9,['成功卡 + 进度入口','WL20260819008'],'success')
n('transfer',0,10,['“我想联系人工”'],'user',9);n('pack',3,10,['生成完整交接单','保留对话、订单和动作'])
n('take',5,11,['分配物流客服队列','阅读摘要并接管会话'],'human',10)
n('reply',5,12,['人工核查并回复','无需重复询问订单'],'human');n('replyui',1,12,['同步人工回复','展示已接管状态']);n('receive',0,12,['继续沟通 / 等待反馈'],'user')
for a,b in [('ask','loading'),('loading','intent'),('intent','risk'),('risk','ownership'),('ownership','orders'),('orders','multiple'),('multiple','choosecard'),('choosecard','select'),('select','bind'),('bind','logtool'),('logtool','logui'),('logui','urge'),('urge','threshold'),('threshold','confirmcard'),('confirmcard','confirm'),('confirm','token'),('token','tickettool'),('tickettool','ticketui'),('ticketui','transfer'),('transfer','pack'),('pack','take'),('take','reply'),('reply','replyui'),('replyui','receive')]:
 edge(a,b,BLUE if a in ('loading','intent') else GREEN,labeltext='需人工' if a=='ticketui' else None,dashed=a in ('loading','intent'))
edge('risk','riskhuman',RED,'是 · L3 高风险')
# 无需模型时，前端直接进入后端本地状态机。
path([(492,376),(492,406),(1116,406),(1116,432)],AMBER,2,True);label(820,406,'本地规则演示：跳过 Dify',AMBER)
# 一个可确定候选订单时，省略用户选单步骤。
path([(1240,774),(1274,774),(1274,1018),(1428,1018),(1428,1016)],MUTED,2,True);label(1397,945,'仅 1 个可确定订单',MUTED)
text(CX[3],1348,'不满足条件 → 说明原因，不建工单',19,AMBER)
text(CX[2],1496,'取消确认 → 不执行；凭据过期 → 重新确认',19,AMBER)

text(52,2256,'另一条业务支线：商品问答与知识兜底',32,GREEN,'lm')
text(52,2301,'知识只取“已发布”版本；未命中或冲突时交给人工，不编造答案。',23,MUTED,'lm')
for i in range(6):rect((24+312*i,2340,336+312*i,2640),'#EEF3EC' if i%2==0 else '#F8FAF6',r=0)
N['kask']=node(0,0,['“空气炸锅怎么洗？”'],'user',y=2400)
N['kintent']=node(2,0,['识别商品问答','触发知识检索'],'ai',y=2400)
N['krag']=node(4,0,['FAISS 检索发布知识','保留来源与版本'],y=2400)
N['kcheck']=node(3,0,['核验命中与适用范围','知识不确定则转人工'],'decision',y=2570)
N['kui']=node(1,0,['回答 + 来源 + 版本','主机不可浸水'],y=2570)
N['khuman']=node(5,0,['未命中 / 知识冲突','进入售前或售后队列'],'human',y=2570)
edge('kask','kintent',BLUE,dashed=True);edge('kintent','krag',BLUE,dashed=True);edge('krag','kcheck',GREEN);edge('kcheck','kui',GREEN,'可靠命中');edge('kcheck','khuman',RED,'未命中 / 冲突')

text(52,2700,'三道权限边界，让系统知道“什么可以做，什么必须停”',30,GREEN,'lm')
cards=[('L1 · 可自动查询',['商品、本人订单、物流、售后政策','只读操作；不需要用户确认'],'#E6EFE7',GREEN),('L2 · 必须先确认',['创建物流催单、提交常规售后申请','一次性凭据 + 归属复核 + 防重复执行'],'#F9EFDA',AMBER),('L3 · 必须转人工',['高金额退款、赔偿、支付安全、法律风险','用户确认也不能让 Agent 自动执行'],'#F6E7E3',RED)]
for i,(title,lines,fill,color) in enumerate(cards):
 x=40+i*626;rect((x,2745,x+596,2892),fill,r=16);text(x+24,2780,title,27,color,'lm')
 for j,line in enumerate(lines):text(x+24,2822+j*34,line,22,INK,'lm')
text(52,2944,'异常出口：理解不清 → 追问｜工具失败 → 重试并说明原因｜连续失败 / 5 轮未解决 → 转人工',22,MUTED,'lm')
text(52,2988,'交接五件套：用户与订单 + 诉求与对话 + 信息状态 + 系统动作 + 风险与建议',22,GREEN,'lm')
svg.append('</svg>')
im.save(OUT/'senyu-agent-swimlane.png')
(OUT/'senyu-agent-swimlane.svg').write_text('\n'.join(svg),encoding='utf-8')
print(str(OUT/'senyu-agent-swimlane.png'))
