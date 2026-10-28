"""模拟购买、物流、售后、评价与问题归档；不接触真实支付或承运商。"""
import hashlib, json, os, re, secrets, time, uuid
from collections import Counter
from fastapi import Depends, HTTPException
from pydantic import BaseModel, Field
import httpx

class Checkout(BaseModel):
    product_id: str
    quantity: int = Field(default=1, ge=1, le=5)
    scenario: str = Field(default='normal', pattern='^(normal|stalled)$')

class Advance(BaseModel):
    expected_version: int = Field(ge=0)

class RefundRequest(BaseModel):
    order_id: str
    reason: str = Field(default='不想要了', min_length=1, max_length=300)
    intact: bool = True

class Rating(BaseModel):
    evaluation_id: str
    stars: int = Field(ge=1, le=5)
    comment: str = Field(default='', max_length=500)

class Service:
    def __init__(self, runtime):
        self.g = runtime

    def read(self, kind, identity):
        return self.g['get'](kind, identity)

    def rows(self, kind):
        return self.g['allof'](kind)

    def save(self, kind, row):
        self.g['save'](kind, row)

    def answer(self, s, state, text, card=None):
        return self.g['result'](s, state, text, card)

    def log(self, event, data):
        self.g['audit'](event, data)

    def active_ai(self, s):
        if s.get('risk_locked'):
            raise HTTPException(409, '此会话仍需有权限人工审核，不能绕过审核执行')
        if s.get('handoff'):
            raise HTTPException(409, '请先点击“返回智能客服”，避免人工与系统同时操作')

    def resume(self, s):
        if s.get('risk_locked'):
            raise HTTPException(409, '高风险审核不能撤回为自动执行，请由对应人工处理')
        if s.get('handoff'):
            old = s['handoff']; old['status'] = '用户撤回'
            s.setdefault('handoff_history', []).append(old)
        s['handoff'] = None; s['pending'] = None; s['unresolved'] = 0
        self.log('resume_ai', {'session_id': s['id']})
        return self.answer(s, '智能服务中', '已返回智能客服。我会继续保留当前商品、订单和历史诉求，为您处理。')

    def draft(self, s, operation, **fields):
        self.active_ai(s)
        p = {'id': secrets.token_urlsafe(24), 'type': 'confirm', 'operation': operation,
             'order_id': '即将生成新订单', 'expires': time.time()+600, **fields}
        s['pending'] = p; s['trace'] = ['理解用户','查询数据','判断确认']
        return self.answer(s, '等待用户确认', '请核对操作与结果，确认后才会写入模拟业务系统。', p)

    def checkout(self, s, body):
        p = self.read('product', body.product_id)
        if p.get('stock', 30) < body.quantity:
            raise HTTPException(409, '当前模拟库存不足，请调整数量或选择其他商品')
        if s.get('rating'):
            s['service_cycle']=s.get('service_cycle',1)+1;s['rating']=None;s['evaluation_id']=None
        previous_order=s.get('order_id');s['order_id']=None
        s['intent'] = 'buy'; s['product_id'] = p['id']
        self.g['msg'](s, 'user', f"准备模拟购买 {p['name']} × {body.quantity}")
        return self.draft(s, '模拟购买', product_id=p['id'], quantity=body.quantity,
            scenario=body.scenario, unit_price=p['price'], amount=p['price']*body.quantity,previous_order_id=previous_order,
            effect=f"生成 {p['name']} × {body.quantity} 的模拟订单，金额 ¥{p['price']*body.quantity:.2f}；不会真实扣款。",
            reversible='发货前可申请取消并模拟退款；发货后按退货流程处理。')

    def atomic(self, records):
        with self.g['db']() as c:
            for kind, row in records:
                c.execute('INSERT OR REPLACE INTO records VALUES(?,?,?)',
                          (kind, row['id'], json.dumps(row, ensure_ascii=False)))

    def confirm(self, s, p, accept):
        if p['operation'] not in ('模拟购买','模拟取消退款','模拟退货申请'):
            return None
        self.active_ai(s)
        self.g['msg'](s, 'user', '确认提交' if accept else '取消操作')
        if not accept:
            s['pending'] = None
            if p['operation']=='模拟购买':s['order_id']=p.get('previous_order_id')
            return self.answer(s, '查询成功', '已取消，没有执行本次购买或退款操作。')
        if p['operation'] == '模拟购买':
            product = self.read('product', p['product_id'])
            if product['price'] != p['unit_price'] or product.get('stock',30) < p['quantity']:
                raise HTTPException(409, '价格或库存已变化，请重新确认购买')
            prefix = 'S'+time.strftime('%Y%m%d')
            nums = [int(o['id'][-3:]) for o in self.rows('order') if o['id'].startswith(prefix)]
            number = max(nums, default=0)+1
            if number > 999: raise HTTPException(409, '本日模拟订单数量已达演示上限')
            stalled = p['scenario'] == 'stalled'
            order = {'id':prefix+str(number).zfill(3),'user_id':s['user_id'],
                'product_id':product['id'],'product':product['name'],'color':product['color'],
                'style':product['style'],'amount':p['amount'],'quantity':p['quantity'],
                'status':'运输中' if stalled else '待发货','shipped':stalled,
                'tracking':'MOCK-SF-'+str(number).zfill(8), 'stale_hours':49 if stalled else 0,
                'eta':'承运记录为模拟数据，当前暂无可靠送达时间','created_at':time.time(),
                'events':[{'time':time.strftime('%m-%d %H:%M'),'text':'模拟购买成功，商家已接单'}],
                'version':1,'mock':True,'shipping_step':2 if stalled else 0,
                'paid_simulated':True,'confirmation_id':p['id']}
            if stalled: order['events'].append({'time':'模拟 49 小时前','text':'模拟转运中，此后未更新'})
            product['stock'] = product.get('stock',30)-p['quantity']
            s['pending']=None; s['order_id']=order['id']; s['product_id']=product['id']
            s['actions'].append({'tool':'mock.purchase','order_id':order['id'],'confirmed':True,'amount':order['amount']})
            self.atomic([('product',product),('order',order),('session',s)])
            self.log('mock_purchase',{'order_id':order['id'],'user_id':s['user_id']})
            return self.answer(s,'模拟购买成功','模拟购买成功！订单和物流记录已生成，没有发生真实支付。可以继续查看物流、咨询使用方法或申请售后。',{'type':'order_created','order':order})
        order = self.g['owned_order'](p['order_id'],s['user_id'])
        if order.get('version',0) != p['order_version']:
            raise HTTPException(409,'订单状态已变化，请重新申请并确认')
        if order['amount'] > self.g['value']('R-RISK-001'):
            return self.g['handoff'](s,'退款金额超过自动处理权限，需人工审核','售后客服',locked=True)
        if order['status'] in ('已退款','模拟退款完成'):
            raise HTTPException(409,'该订单已经完成退款，不能重复申请')
        refund={'id':'RF'+uuid.uuid4().hex[:12].upper(),'user_id':s['user_id'],'order_id':order['id'],
            'amount':order['amount'],'reason':p['reason'],'status':'退款处理中' if not order['shipped'] else '退货申请已受理',
            'step':3 if not order['shipped'] else 0,'version':1,'mock':True,'created_at':time.time(),
            'events':[{'text':'用户确认，模拟售后已受理','time':time.strftime('%m-%d %H:%M')}]}
        order['status']='已取消，模拟退款处理中' if not order['shipped'] else '退货处理中'
        order['refund_id']=refund['id'];order['version']=order.get('version',0)+1
        s['pending']=None;s['refund_id']=refund['id']
        s['actions'].append({'tool':'mock.refund_request','refund_id':refund['id'],'confirmed':True})
        self.atomic([('refund',refund),('order',order),('session',s)])
        return self.answer(s,'售后处理中','申请已写入模拟售后系统。退款尚未完成，可查看进度并推进模拟履约。',{'type':'refund','refund':refund})

    def refund_form(self, s, reason='用户申请售后'):
        s['intent']='refund';s['refund_reason']=reason
        if not s.get('order_id'):
            s['deferred_intent']='refund'
            return self.answer(s,'多订单待选择','请先选择需要处理的订单，我会核对能否取消、退货及退款。',{'type':'orders','orders':self.g['orders'](s['user_id'])})
        order=self.g['owned_order'](s['order_id'],s['user_id'])
        existing=next((r for r in self.rows('refund') if r['order_id']==order['id']),None)
        if existing:
            s['refund_id']=existing['id']
            return self.answer(s,'售后处理中' if existing['step']<4 else '模拟退款完成','已找到这笔订单的售后进度，不会重复提交。',{'type':'refund','refund':existing})
        if order['amount']>self.g['value']('R-RISK-001'):
            return self.g['handoff'](s,'高金额退款需有权限人工审核','售后客服',locked=True)
        return self.answer(s,'等待补充信息','可以先由我处理常规售后。请补充原因与商品状态，提交后还会向您确认。',{'type':'refund_form','order':order,'reason':reason})

    def draft_refund(self,s,body):
        self.active_ai(s)
        for message in s['messages']:
            card=message.get('card',{})
            if card.get('type')=='refund_form' and card['order']['id']==body.order_id:
                card.update(submitted_reason=body.reason,submitted_intact=body.intact)
        order=self.g['owned_order'](body.order_id,s['user_id']);s['order_id']=order['id'];s['intent']='refund'
        existing=next((r for r in self.rows('refund') if r['order_id']==order['id']),None)
        if existing:return self.answer(s,'售后处理中','已有售后申请，请查看进度。',{'type':'refund','refund':existing})
        if order['amount']>self.g['value']('R-RISK-001'):
            return self.g['handoff'](s,'高金额退款需人工审核','售后客服',locked=True)
        if order.get('days_since_delivery',1)>7 and order['status']=='已签收':
            return self.answer(s,'等待补充信息','这笔订单超出演示规则的 7 天无理由退货期。若有质量问题，可补充材料申请核查；也可以要求人工处理。',self.choices([('补充质量问题','商品有质量问题'),('联系售后人工','我要售后人工')]))
        if order['shipped'] and not body.intact and body.reason!='质量问题':
            return self.answer(s,'等待补充信息','商品状态不满足当前无理由退货规则。若属于质量问题，可以改选质量问题继续核查；暂不承诺退款。',self.choices([('重新填写售后','我要退款'),('联系售后人工','我要售后人工')]))
        operation='模拟退货申请' if order['shipped'] else '模拟取消退款'
        return self.draft(s,operation,order_id=order['id'],order_version=order.get('version',0),reason=body.reason,
            effect=f"{'提交退货申请，待模拟退货及验收后退款' if order['shipped'] else '取消未发货模拟订单并进入退款处理'}，金额 ¥{order['amount']:.2f}。不会发生真实资金流转。",
            reversible='取消订单后不能恢复，可重新模拟购买；退货申请可联系人工核查撤销条件。')

    def mock_allowed(self):
        if os.getenv('ALLOW_MOCK_ADVANCE','true').lower()!='true':
            raise HTTPException(403,'模拟履约推进已关闭')

    def advance_order(self,s,oid,version):
        self.active_ai(s);self.mock_allowed();o=self.g['owned_order'](oid,s['user_id'])
        if o.get('version',0)!=version:raise HTTPException(409,'物流已更新，请刷新后重试')
        if o.get('refund_id') or '退款' in o['status'] or '退货' in o['status']:
            raise HTTPException(409,'订单已进入售后，不能继续正向发货')
        stages=['待发货','已揽收','运输中','派送中','已签收']
        step=o.get('shipping_step',stages.index(o['status']) if o['status'] in stages else (2 if o['shipped'] else 0))
        if step>=4:return self.answer(s,'查询成功','这笔订单已模拟签收。',{'type':'logistics','order':o})
        step+=1;o.update(shipping_step=step,status=stages[step],shipped=True,stale_hours=0,version=version+1,mock=True)
        o['tracking']=o.get('tracking') or 'MOCK-SF-'+uuid.uuid4().hex[:10].upper()
        o['events'].append({'time':time.strftime('%m-%d %H:%M'),'text':'[模拟物流] '+stages[step]})
        o['eta']='订单已模拟签收' if step==4 else '正在模拟配送，非真实承运商时效承诺'
        if step==4:o['delivered_at']=time.time();o['days_since_delivery']=0
        s['order_id']=o['id'];s['product_id']=o['product_id'];s['intent']='logistics'
        s['actions'].append({'tool':'mock.advance_shipping','order_id':oid,'status':o['status']})
        self.atomic([('order',o),('session',s)])
        return self.answer(s,'查询成功','模拟物流已更新：'+o['status']+'。',{'type':'logistics','order':o})

    def advance_refund(self,s,rid,version):
        self.active_ai(s);self.mock_allowed();r=self.read('refund',rid)
        if r['user_id']!=s['user_id']:raise HTTPException(403,'无权访问此售后记录')
        if r['version']!=version:raise HTTPException(409,'售后进度已变化，请刷新后重试')
        if r['step']>=4:return self.answer(s,'模拟退款完成','模拟退款已经完成。',{'type':'refund','refund':r})
        statuses=['退货申请已受理','退货运输中','仓库待验收','退款处理中','模拟退款完成']
        r['step']+=1;r['version']+=1;r['status']=statuses[r['step']]
        r['events'].append({'time':time.strftime('%m-%d %H:%M'),'text':'[模拟售后] '+r['status']})
        o=self.g['owned_order'](r['order_id'],s['user_id']);o['version']=o.get('version',0)+1
        records=[('refund',r),('order',o)]
        if r['step']==4:
            o['status']='已退款';o['refunded_at']=time.time()
            if o.get('paid_simulated'):
                p=self.read('product',o['product_id']);p['stock']=p.get('stock',30)+o.get('quantity',1);records.append(('product',p))
        s['refund_id']=r['id'];s['order_id']=o['id'];s['intent']='refund_progress'
        s['actions'].append({'tool':'mock.advance_refund','refund_id':rid,'status':r['status']})
        self.atomic(records+[('session',s)])
        return self.answer(s,'模拟退款完成' if r['step']==4 else '售后处理中','售后记录已更新为：'+r['status']+'。这只是数据库模拟，不涉及真实退款。',{'type':'refund','refund':r})

    def choices(self,items):
        return {'type':'resolution','actions':[{'label':label,'text':text} for label,text in items]}

    def finish(self,s):
        if s.get('pending'):
            return self.answer(s,'等待用户确认','不客气。目前还有一项待确认操作，您可以确认或取消；不会因为“好的”而自动执行。',s['pending'])
        if s.get('risk_locked'):
            return self.answer(s,'已转人工','不客气。该事项仍需人工审核，当前并未获批或完成。',{'type':'handoff','queue':s['handoff']['queue']})
        if s.get('rating'):
            return self.answer(s,'会话已完成' if s['rating']['stars']>=4 else '待继续处理','本轮评价已记录。您可以继续购物或提出尚未解决的问题，不会重复计入评价。',self.choices([('继续购物','我想买商品'),('还有问题','我还有问题没解决')]))
        evaluation=s.get('evaluation_id')
        if not evaluation or s.get('rating'):
            evaluation=secrets.token_urlsafe(20);s['evaluation_id']=evaluation
        return self.answer(s,'等待服务评价','不客气，很高兴为您服务！请为本次咨询打个分。评价针对服务体验，未完成的物流或售后仍可继续查看。',{'type':'rating','evaluation_id':evaluation})

    def rate(self,s,body):
        if not s.get('evaluation_id') or not secrets.compare_digest(body.evaluation_id,s['evaluation_id']):
            raise HTTPException(409,'评价凭据无效，请重新发起评价')
        old=next((r for r in self.rows('rating') if r['id']==body.evaluation_id),None)
        if old:return s
        rating={'id':body.evaluation_id,'session_id':s['id'],'user_id':s['user_id'],'stars':body.stars,
                'comment':body.comment,'category':s.get('issue_category','其他咨询'),'created_at':time.time()}
        s['rating']=rating;self.save('rating',rating)
        for message in s['messages']:
            card=message.get('card',{})
            if card.get('type')=='rating' and card.get('evaluation_id')==body.evaluation_id:
                card.update(submitted_stars=body.stars,submitted_comment=body.comment)
        if body.stars<=3:
            s['needs_followup']=True;s['unresolved']=0
            return self.answer(s,'待继续处理','收到您的评价，我会先继续帮您处理。您可以说明哪里不满意，或选择退款、物流核查；需要时再找人工。',self.choices([('继续说明问题','我还有问题没解决'),('申请退款','我要退款'),('查看物流','查物流'),('我需要人工','我要人工客服')]))
        s['needs_followup']=False
        return self.answer(s,'会话已完成','感谢您的评价！本轮咨询已结束。您仍可继续购物、查订单或提出新的问题。',self.choices([('继续选购','我想买商品'),('查看我的订单','我的订单')]))

    async def handle(self,s,text,fault=''):
        s.pop('model_intent',None)
        intent=self.g['classify'](text)
        if intent=='unknown' and os.getenv('ENABLE_LLM','false').lower()=='true':
            try:
                context='\n'.join(m['role']+': '+m['text'] for m in s['messages'][-7:])
                decision=await self.g['tool_route'](self.g['Chat'](text=text))
                intent=decision['intent'];s['model_intent']=intent;s['model_used']=True
            except Exception as e:
                self.log('model_degraded',{'session_id':s['id'],'reason':type(e).__name__})
                s['model_degraded']=True
                self.g['msg'](s,'assistant','模型接口暂不可用，已切换本地规则继续核对；不会据此假称操作成功。')
        # 普通候接会话允许继续自助；高风险审核与已接管会话不自动抢占。
        h=s.get('handoff')
        if h and h['status']=='待接管' and not s.get('risk_locked') and intent not in ('handoff','unknown'):
            h['status']='智能客服继续处理';s.setdefault('handoff_history',[]).append(h);s['handoff']=None
            self.g['msg'](s,'assistant','先由智能客服继续为您处理，历史信息已保留；仍可随时要求人工。')
        if s.get('handoff'):return None
        if s.get('pending') and intent=='price' and s['pending']['operation']=='模拟购买':
            pending=s['pending'];product=self.g['identify_product'](text) or self.read('product',pending['product_id'])
            self.g['price_answer'](s,text,product)
            return self.answer(s,'等待用户确认','以上为商品价格；当前模拟购买尚未执行。请继续核对本次购买的数量与合计金额。',pending)
        if s.get('rating') and intent not in ('rating','smalltalk'):
            s['service_cycle']=s.get('service_cycle',1)+1;s['rating']=None;s['evaluation_id']=None
        if intent=='rating':return self.finish(s)
        if intent=='smalltalk':
            s['unresolved']=0
            return self.answer(s,'智能服务中','您好，我在。可以陪您从选商品、模拟购买，到查物流、售后处理。您现在想做哪一步？',self.choices([('选购商品','我想买商品'),('查询订单','我的订单'),('申请售后','我要退款')]))
        if intent in ('browse','buy'):
            s['intent']=intent;product=self.g['identify_product'](text)
            if intent=='buy' and product:return self.checkout(s,Checkout(product_id=product['id']))
            return self.answer(s,'选购商品','可以的，请选择商品型号；购买前会显示模拟金额并请您确认，不会真实扣款。',{'type':'catalog','products':self.rows('product')})
        if intent=='order_list':
            s['intent']='logistics';s['deferred_intent']='logistics'
            return self.answer(s,'多订单待选择','这是您账户下的订单，可以查看物流或继续售后。',{'type':'orders','orders':self.g['orders'](s['user_id'])})
        if intent in ('refund','refund_progress','aftersale'):
            oid=re.search(r'S\d{11}',text)
            if oid:
                try:o=self.g['owned_order'](oid.group(),s['user_id']);s['order_id']=o['id'];s['product_id']=o['product_id']
                except HTTPException:return self.g['handoff'](s,'订单不属于当前用户，无法办理','安全风险',locked=True)
            if intent in ('refund','aftersale'):return self.refund_form(s,text)
            rr=[r for r in self.rows('refund') if r['user_id']==s['user_id'] and (not s.get('order_id') or r['order_id']==s['order_id'])]
            if rr:return self.answer(s,'售后处理中' if rr[-1]['step']<4 else '模拟退款完成','已查询到模拟售后记录。',{'type':'refund','refund':rr[-1]})
            return self.answer(s,'等待补充信息','目前未找到这笔订单的退款申请。可以先选择订单申请售后。',self.choices([('申请退款','我要退款'),('查看订单','我的订单')]))
        if intent in ('dissatisfaction','complaint'):
            s['intent']=intent;s['needs_followup']=True;s.setdefault('issue_tags',[])
            if '不满意' not in s['issue_tags']:s['issue_tags'].append('不满意')
            return self.answer(s,'待继续处理','理解您的不满意，我会先帮您核对和处理，不直接把您推给人工。具体是商品使用、物流、价格，还是退款问题？',self.choices([('价格不符','请核对当前订单价格'),('物流太慢','查物流'),('退货或退款','我要退款'),('产品怎么使用','产品怎么使用'),('仍需人工','我要人工客服')]))
        return None

    def observe(self,s):
        if s.get('demo_seed'):return
        intent=s.get('intent');category={'buy':'购买与订单','browse':'商品咨询','logistics':'订单物流','urge':'订单物流',
            'price':'商品价格','knowledge':'商品咨询','aftersale':'退货退款','refund':'退货退款',
            'refund_progress':'退货退款','complaint':'服务投诉','dissatisfaction':'服务投诉'}.get(intent)
        if s.get('risk_locked'):category='安全风险' if s.get('handoff',{}).get('queue')=='安全风险' else '退款与风险审核'
        if category:s['issue_category']=category
        if not s.get('issue_category'):s['issue_category']='其他咨询'
        category_key=hashlib.sha1(s['issue_category'].encode()).hexdigest()[:8]
        identity='ISS-'+s['id']+'-'+str(s.get('service_cycle',1))+'-'+category_key+'-'+(s.get('order_id') or 'no-order');s['issue_id']=identity
        state=s['state'];status='待人工' if s.get('handoff') else ('已解决' if state=='会话已完成' else ('待跟进' if s.get('needs_followup') else state))
        self.save('issue',{'id':identity,'session_id':s['id'],'user_id':s['user_id'],'category':s['issue_category'],
            'status':status,'order_id':s.get('order_id'),'product_id':s.get('product_id'),'tags':s.get('issue_tags',[]),
            'summary':'；'.join(m['text'] for m in s['messages'] if m['role']=='user')[-1000:],
            'queue':s['handoff']['queue'] if s.get('handoff') else None,'updated_at':time.time()})

    def overview(self):
        issues=self.rows('issue');ratings=self.rows('rating')
        for issue in issues:issue['user']=self.read('user',issue['user_id'])
        return {'issues':issues,'categories':dict(Counter(x['category'] for x in issues)),
            'ratings':len(ratings),'average_stars':round(sum(x['stars'] for x in ratings)/len(ratings),2) if ratings else None,
            'low_ratings':sum(x['stars']<=3 for x in ratings),'refunds':len(self.rows('refund')),
            'simulated_purchases':sum(bool(o.get('paid_simulated')) for o in self.rows('order'))}

    def install(self,app):
        auth=self.g['auth'];staff=self.g['staff'];lock=self.g['LOCK']
        @app.post('/api/sessions/{sid}/checkout')
        def checkout(sid:str,body:Checkout,role=Depends(auth)):
            with lock:return self.checkout(self.g['owned_session'](sid),body)
        @app.post('/api/sessions/{sid}/shipping/{oid}/advance')
        def shipping(sid:str,oid:str,body:Advance,role=Depends(auth)):
            with lock:return self.advance_order(self.g['owned_session'](sid),oid,body.expected_version)
        @app.post('/api/sessions/{sid}/refund')
        def refund(sid:str,body:RefundRequest,role=Depends(auth)):
            with lock:return self.draft_refund(self.g['owned_session'](sid),body)
        @app.post('/api/sessions/{sid}/refund/{rid}/advance')
        def refund_advance(sid:str,rid:str,body:Advance,role=Depends(auth)):
            with lock:return self.advance_refund(self.g['owned_session'](sid),rid,body.expected_version)
        @app.post('/api/sessions/{sid}/finish')
        def finish(sid:str,role=Depends(auth)):
            with lock:return self.finish(self.g['owned_session'](sid))
        @app.post('/api/sessions/{sid}/rating')
        def rating(sid:str,body:Rating,role=Depends(auth)):
            with lock:return self.rate(self.g['owned_session'](sid),body)
        @app.post('/api/sessions/{sid}/resume')
        def resume(sid:str,role=Depends(auth)):
            with lock:return self.resume(self.g['owned_session'](sid))
        @app.get('/api/admin/service-report')
        def report(role=Depends(staff)):return self.overview()
        @app.get('/api/admin/model-status')
        def model_status(role=Depends(self.g['admin'])):
            return {'enabled':os.getenv('ENABLE_LLM','false').lower()=='true','configured':bool(os.getenv('LLM_API_KEY')),
                'model':os.getenv('LLM_MODEL','deepseek-chat'),'base_url':os.getenv('LLM_BASE_URL','https://api.deepseek.com/v1'),
                'mode':os.getenv('APP_MODE','local'),'key_visible':False}
        @app.post('/api/admin/model-test')
        async def model_test(role=Depends(self.g['admin'])):
            if not os.getenv('LLM_API_KEY'):raise HTTPException(409,'请先在服务器 .env 中配置 LLM_API_KEY 并重启服务')
            try:
                async with httpx.AsyncClient(timeout=8) as c:
                    r=await c.post(os.getenv('LLM_BASE_URL','https://api.deepseek.com/v1').rstrip('/')+'/chat/completions',
                        headers={'Authorization':'Bearer '+os.environ['LLM_API_KEY']},json={'model':os.getenv('LLM_MODEL','deepseek-chat'),
                        'max_tokens':8,'messages':[{'role':'user','content':'仅回复 OK'}]})
                    r.raise_for_status();r.json()['choices'][0]['message']['content']
                return {'connected':True,'model':os.getenv('LLM_MODEL','deepseek-chat')}
            except Exception as e:
                self.log('model_connection_failure',{'reason':type(e).__name__})
                raise HTTPException(502,'模型连接失败，请检查地址、模型名和服务端密钥；详细类型已记录审计')
