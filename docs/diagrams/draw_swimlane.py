"""绘制可用于项目介绍的高分辨率泳道图，同时保留可编辑 SVG。"""
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
import html, math

OUT=Path(__file__).resolve().parent
W,H=1920,3790
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

"""新版绘图主体：与模拟购买、售后、评价闭环一致。"""
def n(id,c,r,lines,kind='normal',num=None):
 N[id]=node(c,r,lines,kind,num,y=360+132*r)

text(52,62,'森屿生活 · 完整电商客服闭环泳道图',43,GREEN,'lm')
text(52,116,'选购下单 → 模拟履约 → 咨询与售后 → 星级评价 → 分类归档',27,MUTED,'lm')
text(52,158,'实线：已验证的本地业务闭环    蓝色虚线：可选模型 / Dify 接入路径',21,MUTED,'lm')
text(52,192,'Docker 已恢复，Dify 1.17.1 运行中；本项目工作流与真实模型端到端仍待验证。',21,BLUE,'lm')
roles=[('消费者','选择商品 / 提问 / 确认 / 评价'),('商城与会话端','商品、订单、操作与结果可见'),('智能客服理解','规则优先 / 可选 API 或 Dify'),('后端业务规则','归属、价格、库存、确认、权限'),('模拟业务与知识库','订单 / 物流 / 售后 / FAISS'),('人工与运营','必要时审核 / 问题分类归档')]
for i,(title,sub) in enumerate(roles):
 x=24+312*i
 rect((x,234,x+312,2285),'#EEF3EC' if i%2==0 else '#F8FAF6',r=0)
 rect((x+6,234,x+306,308),GREEN if i in (0,3) else '#DCE7D9',r=12)
 text(CX[i],260,title,25,'#FFFFFF' if i in (0,3) else INK)
 text(CX[i],290,sub,16,'#E0EBDD' if i in (0,3) else MUTED)
 if i:path([(x,314),(x,2275)],LINE,1,arrow=False)

n('choose',0,0,['选择型号、款式与数量'],'user',1)
n('store',1,0,['商城商品卡','6 款商品 / 各自价格库存'])
n('price',3,1,['服务器核对价格与库存','只接受本人的身份'])
n('buy_confirm',1,1,['L2 · 模拟购买确认','操作 / 金额 / 结果 / 撤销'])
n('accept',0,2,['点击“确认提交”'],'user',2)
n('purchase_guard',3,2,['核验一次性确认凭据','价格复核 / 防重复下单'])
n('create',4,2,['生成本人订单与物流','扣减模拟库存 / 无真实支付'])
n('success',1,3,['模拟购买成功','我的订单 / 物流入口'],'success',3)
n('ask',0,4,['查物流 / 问价格 / 问用法','沿用本轮商品与订单'],'user',4)
n('understand',2,4,['意图识别 + 上下文','本地规则优先'])
n('optional_model',2,5,['可选模型 / Dify 编排','辅助理解，不决定权限'],'ai')
n('readonly_guard',3,5,['L1 · 只读权限校验','核对本人订单与适用型号'])
n('read',4,5,['查订单、物流或 FAISS','知识保留来源与发布版本'])
n('answer',1,6,['展示结果、依据与下一步','价格确定 / 物流透明'])
n('advance_guard',3,6,['模拟履约开关与版本检查','按钮推进，拒绝重复更新'])
n('shipping',4,6,['模拟物流逐步推进','揽收 → 运输 → 派送 → 签收'])
n('thanks',0,7,['“好的，谢谢 / 明白了”'],'user',5)
n('closing_guard',3,7,['仍有待确认操作？','有：回到确认，不代替执行'],'decision')
n('rating',1,8,['展示 1–5 星服务评价','评价意见可填写'],num=6)
n('stars',0,9,['选择星级并提交意见'],'user')
n('rating_guard',3,9,['记录真实选择的星级','评分分流 / 防重复评价'],'decision')
n('archive',5,9,['按订单与主题分类归档','保留诉求、状态与星级'],'success',7)
n('done',1,10,['4–5 星：本轮咨询完成','继续购物 / 查看订单'],'success')
n('unhappy',3,10,['1–3 星 / 普通不满意','先核对并继续解决'],'decision',8)
n('solutions',1,11,['提供自助解决方案','价格 / 物流 / 退货退款'])
n('more',0,12,['补充原因或选择方案','不因低分就被转人工'],'user')
n('intent_again',2,12,['归纳具体问题','知识首次未命中先追问'])
n('can_solve',3,13,['能否在规则内解决？','核对资料、工具与权限'],'decision',9)
n('self_solve',1,14,['可解决：继续自助处理','解决后再次邀请评价'],'success')
n('human',5,13,['必要时转人工','主动要求 / 高风险 / 多次失败'],'human',10)
n('handoff',5,14,['六技能队列 + 完整交接单','普通候接可返回智能客服'],'human')

for a,b in [('choose','store'),('store','price'),('price','buy_confirm'),('buy_confirm','accept'),('accept','purchase_guard'),('purchase_guard','create'),('create','success'),('success','ask'),('ask','understand'),('understand','readonly_guard'),('readonly_guard','read'),('read','answer'),('answer','thanks'),('thanks','closing_guard'),('closing_guard','rating'),('rating','stars'),('stars','rating_guard'),('rating_guard','archive'),('unhappy','solutions'),('solutions','more'),('more','intent_again'),('intent_again','can_solve')]:
 edge(a,b,GREEN)
edge('understand','optional_model',BLUE,dashed=True)
edge('optional_model','readonly_guard',BLUE,dashed=True)
edge('answer','advance_guard',MUTED,'演示按钮')
edge('advance_guard','shipping',MUTED)
edge('rating_guard','done',GREEN,'4–5 星')
edge('rating_guard','unhappy',AMBER,'1–3 星')
edge('can_solve','self_solve',GREEN,'可以自助')
edge('can_solve','human',RED,'确实需要人工')
edge('human','handoff',RED)
text(CX[4],360+132*7,'普通咨询与低分不直接转人工',19,GREEN)

text(52,2350,'售后支线：常规退款先自助，不能处理时才升级',32,GREEN,'lm')
text(52,2393,'未发货可取消退款；已发货按退货、入库、验收与退款流程推进。所有资金流转均为模拟。',22,MUTED,'lm')
for i,(title,_) in enumerate(roles):
 x=24+312*i
 rect((x,2425,x+312,3370),'#EEF3EC' if i%2==0 else '#F8FAF6',r=0)
 text(CX[i],2449,title,20,MUTED)
def sub(id,c,y,lines,kind='normal',num=None):N[id]=node(c,0,lines,kind,num,y=y)
sub('want_refund',0,2525,['“不满意，我要退款”'],'user',11)
sub('refund_check',3,2525,['核对归属、金额与原因','商品状态 / 退货条件'],'decision')
sub('refund_human',5,2525,['高金额或规则例外','转有权限售后人工审核'],'human')
sub('refund_confirm',1,2655,['L2 · 售后四要素确认','未确认不取消、不退货'])
sub('refund_accept',0,2785,['核对后确认提交'],'user',12)
sub('shipped',3,2785,['确认凭据与状态复核','按是否发货分流'],'decision')
sub('cancel_flow',4,2915,['未发货：取消模拟订单','进入模拟退款处理中'])
sub('return_flow',4,3045,['已发货：申请 → 寄回','入库 → 验收 → 退款处理中'])
sub('refund_done',1,3175,['模拟退款完成','未完成前不谎报成功'],'success',13)
sub('refund_thanks',0,3305,['问题解决，继续评价'],'user')
sub('rate_again',1,3305,['再次邀请评价','或继续新的咨询'])
sub('archive_again',5,3305,['更新处理状态与评价','不同订单、主题独立归档'],'success',14)
edge('want_refund','refund_check',GREEN)
edge('refund_check','refund_human',RED,'>500 元等高风险')
edge('refund_check','refund_confirm',GREEN,'符合自动处理规则')
edge('refund_confirm','refund_accept',GREEN)
edge('refund_accept','shipped',GREEN)
edge('shipped','cancel_flow',GREEN,'未发货')
# 两条退款路径分开走线，避免穿过另一条分支节点。
path([(1240,2785),(1274,2785),(1274,3045),(1296,3045)],GREEN)
label(1327,2990,'已发货',GREEN)
path([(1552,2915),(1580,2915),(1580,3110),(1116,3110)],GREEN,arrow=False)
path([(1428,3091),(1428,3110),(1116,3110)],GREEN,arrow=False)
path([(1116,3110),(492,3110),(492,3122)],GREEN)
edge('refund_done','refund_thanks',GREEN)
edge('refund_thanks','rate_again',GREEN)
edge('rate_again','archive_again',GREEN)

text(52,3420,'权限边界与兜底条件',31,GREEN,'lm')
cards=[('L1 · 自动只读查询',['商品价格、知识、本人订单、物流','结果来自数据库或已发布知识'],'#E6EFE7',GREEN),('L2 · 用户确认后写入',['模拟购买、物流催单、常规退货退款','归属复核 + 一次性凭据 + 防重复'],'#F9EFDA',AMBER),('L3 · 有权限人工审核',['高金额退款、赔偿、安全、法律风险','用户确认也不能绕过风险权限'],'#F6E7E3',RED)]
for i,(title,lines,fill,color) in enumerate(cards):
 x=40+i*626;rect((x,3464,x+596,3606),fill,r=16);text(x+24,3498,title,26,color,'lm')
 for j,line in enumerate(lines):text(x+24,3540+j*33,line,22,INK,'lm')
text(52,3658,'首次知识未命中先追问；连续无法理解、知识多次核对无果或工具持续失败，才升级对应人工队列。',22,MUTED,'lm')
text(52,3700,'交接五件套：用户与订单 + 诉求与对话 + 信息状态 + 已执行动作 + 风险与建议。',22,GREEN,'lm')
text(52,3738,'范围说明：本图展示当前模拟业务；Docker/Dify 运行正常不等于项目工作流或真实模型已经联调验收。',19,MUTED,'lm')
svg.append('</svg>')
im.save(OUT/'senyu-agent-swimlane.png')
(OUT/'senyu-agent-swimlane.svg').write_text('\n'.join(svg),encoding='utf-8')
print(str(OUT/'senyu-agent-swimlane.png'))
