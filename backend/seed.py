"""课程演示数据，日期固定在 2026-08-19，避免随系统日期改变。"""
USER = {'id':'u1','name':'李晓燕','display_name':'李女士','level':'黄金会员','phone':'138****6721'}
USERS = [USER, {'id':'u2','name':'张明远','display_name':'张先生','level':'白银会员','phone':'139****2816'}, {'id':'u3','name':'王雨晴','display_name':'王女士','level':'钻石会员','phone':'137****9032'}]
PRODUCTS = [
 {'id':'AF-35','name':'空气炸锅 AF-35','color':'白色','style':'轻巧经典款','price':398,'capacity':'3.5L','power':'1400W','category':'空气炸锅'},
 {'id':'AF-45','name':'空气炸锅 AF-45','color':'奶油白','style':'可视升级款','price':469,'capacity':'4.5L','power':'1500W','category':'空气炸锅'},
 {'id':'AF-55','name':'空气炸锅 AF-55','color':'苔藓绿','style':'家庭大容量款','price':598,'capacity':'5.5L','power':'1700W','category':'空气炸锅'},
 {'id':'AF-65','name':'空气炸锅 AF-65','color':'曜石黑','style':'双区旗舰款','price':799,'capacity':'6.5L','power':'1800W','category':'空气炸锅'},
 {'id':'EK-17','name':'电热水壶 EK-17','color':'雾灰色','style':'恒温款','price':199,'capacity':'1.7L','power':'1500W','category':'电热水壶'},
 {'id':'TO-20','name':'多士炉 TO-20','color':'复古红','style':'双槽复古款','price':269,'capacity':'双槽','power':'800W','category':'多士炉'}
]
ORDERS = [
 {'id':'S20260817001','user_id':'u1','product':'空气炸锅 AF-35','color':'白色','amount':398,'status':'运输中','shipped':True,'tracking':'SF138*****6721','stale_hours':49,'eta':'2026-08-20（承运商预估，非到达承诺）','events':[{'time':'08-17 16:30','text':'商家已发货'},{'time':'08-17 20:00','text':'顺丰已揽收'},{'time':'08-17 23:00','text':'到达杭州转运中心，之后 49 小时未更新'}]},
 {'id':'S20260818002','user_id':'u1','product':'空气炸锅 AF-45','color':'奶油白','amount':469,'status':'待发货','shipped':False,'tracking':None,'stale_hours':0,'eta':'尚未发货，暂无预计送达时间','events':[]},
 {'id':'S20260816003','user_id':'u2','product':'电热水壶 EK-17','color':'雾灰色','amount':199,'status':'已签收','shipped':True,'tracking':'SF139*****2816','events':[{'time':'08-18 10:20','text':'用户已签收'}],'stale_hours':0,'eta':'订单已签收'},
 {'id':'S20260819004','user_id':'u2','product':'空气炸锅 AF-55','color':'苔藓绿','amount':598,'status':'运输中','shipped':True,'tracking':'SF139*****3104','events':[{'time':'08-19 09:00','text':'到达上海转运中心，物流正常更新'}],'stale_hours':6,'eta':'2026-08-21（承运商预估，非到达承诺）'},
 {'id':'S20260818005','user_id':'u3','product':'空气炸锅 AF-65','color':'曜石黑','amount':799,'status':'待发货','shipped':False,'tracking':None,'events':[],'stale_hours':0,'eta':'尚未发货，暂无预计送达时间'},
 {'id':'S20260817006','user_id':'u3','product':'多士炉 TO-20','color':'复古红','amount':269,'status':'运输中','shipped':True,'tracking':'SF137*****9032','events':[{'time':'08-17 18:00','text':'已揽收，之后 50 小时未更新'}],'stale_hours':50,'eta':'2026-08-20（承运商预估，非到达承诺）'}
]
for order in ORDERS:
 product=next(p for p in PRODUCTS if p['name']==order['product'])
 order.update(product_id=product['id'],style=product['style'])
KNOWLEDGE = [
 {'id':'K-001','title':'AF-35 商品参数','category':'商品知识','content':'空气炸锅 AF-35，白色，售价 398 元，容量 3.5L，额定功率 1400W，温度 80–200℃。适合 1–3 人使用。','keywords':'空气炸锅 AF35 AF-35 参数 容量 功率 价格 几人 温度 多少钱','status':'发布','version':1,'owner':'商品运营 王宁'},
 {'id':'K-002','title':'AF-35 使用与清洗','category':'商品知识','content':'初次使用请清洗炸篮并擦干。清洗前断电并待冷却，炸篮用温水和中性清洁剂清洗，主机不可浸水，不可使用金属刷。烹饪时间请参照随箱说明书。','keywords':'使用 清洗 怎么洗 主机 炸篮 金属刷 第一次','status':'发布','version':1,'owner':'商品运营 王宁'},
 {'id':'K-003','title':'常规退换货政策','category':'售后政策','content':'签收后 7 天内，商品完好、不影响二次销售可申请无理由退货；质量问题须提交凭证审核。无理由退货运费由用户承担，质量问题核实后由商家承担。审核通过且仓库验收后原路退款，一般 3–7 个工作日到账，以支付渠道为准。申请不代表退款获批。','keywords':'退货 换货 退款 运费 售后 几天 到账 七天 7天','status':'发布','version':2,'owner':'售后主管 陈静'},
 {'id':'K-004','title':'物流异常处理 SOP','category':'物流 SOP','content':'物流轨迹 48 小时未更新，可在用户确认后创建物流催单。受理后预计 24 小时内反馈核查进度，不保证送达日期。连续查询失败或责任不清转物流客服。','keywords':'物流 快递 催单 轨迹 48小时 多久 更新','status':'发布','version':1,'owner':'物流主管 周明'},
 {'id':'K-005','title':'八月会员活动','category':'活动规则','content':'演示活动有效期为 2026-08-01 至 2026-08-31，黄金会员可领取指定商品 20 元优惠券，不与其他优惠叠加，是否适用以结算页为准。活动过期后不适用。','keywords':'活动 优惠 优惠券 叠加 八月','status':'发布','version':1,'owner':'营销运营 赵悦'},
 {'id':'K-006','title':'黄金会员权益','category':'会员规则','content':'黄金会员享专属客服与会员活动提醒。积分不直接抵扣现金，不承诺永久折扣。会员等级与积分以会员中心为准。','keywords':'会员 黄金 积分 权益 等级','status':'发布','version':1,'owner':'会员运营 刘佳'},
 {'id':'K-007','title':'九月活动草案','category':'活动规则','content':'草稿不能用于客服回答。','keywords':'九月 活动','status':'草稿','version':1,'owner':'营销运营 赵悦'}
]
for product in PRODUCTS[1:]:
 KNOWLEDGE.append({'id':'K-P-'+product['id'],'title':product['id']+' 商品参数','category':'商品知识','content':f"{product['name']}，{product['color']}，{product['style']}，演示售价 {product['price']} 元，容量 {product['capacity']}，额定功率 {product['power']}。实际购买价格以结算页为准。",'keywords':f"{product['id']} {product['id'].replace('-','')} {product['category']} 参数 容量 功率 价格 多少钱 型号 款式",'status':'发布','version':1,'owner':'商品运营 王宁'})
KNOWLEDGE.append({'id':'K-P-CLEAN','title':'空气炸锅通用清洗','category':'商品知识','content':'空气炸锅清洗前请断电冷却，炸篮用温水与中性清洁剂清洗，主机不可浸水，不使用金属刷。具体可拆卸部件以对应型号说明书为准。','keywords':'空气炸锅 AF-45 AF-55 AF-65 清洗 怎么洗 炸篮 主机','status':'发布','version':1,'owner':'商品运营 王宁'})
for p in PRODUCTS:
 guide=('食材放入炸篮时不超过容量标线，选择合适的温度与时间后启动，中途翻面时避免烫伤。清洁前断电冷却，主机不可浸水。' if p['id'].startswith('AF-') else ('放入吐司、选择烘烤档位后启动，结束后取出。清洁前断电冷却，不将金属餐具伸入通电的烤槽。' if p['id']=='TO-20' else '按水位标线加水，不超过 MAX，盖好壶盖后加热。清洁前断电冷却，底座与电气部分不可浸水。'))
 KNOWLEDGE.append({'id':'K-GUIDE-'+p['id'],'title':p['id']+' 使用指南','category':'商品知识','content':p['name']+' 演示使用指南：'+guide+'具体操作以对应型号说明书为准。','keywords':p['id']+' '+p['id'].replace('-','')+' 产品 使用 怎么用 怎么使用 使用方法 指南 说明书 教程','status':'发布','version':1,'owner':'商品运营 王宁'})
def rule(id,name,scenario,condition,basis,action,priority,value=None):
 return dict(id=id,name=name,scenario=scenario,condition=condition,basis=basis,action=action,priority=priority,exceptions='高风险优先转人工；不得越权',failure='记录原因并转对应技能队列',owner='客服运营负责人',version=1,enabled=True,value=value)
RULES = [rule('R-LOG-002','多个候选订单处理','订单与物流','候选订单数量 >= 2','当前用户的订单列表','展示选择卡片',50,2),rule('R-LOG-003','物流催单门槛','物流催单','轨迹未更新小时数 >= 48','物流最后更新时间','L2 四要素确认后创建催单',60,48),rule('R-RISK-001','高金额退款','退款','金额 > 500 元','订单与用户输入金额','转售后人工审核',100,500),rule('R-AUTH-001','订单归属校验','所有订单工具','订单不属于当前用户','服务端身份与订单归属','拒绝并转安全风险',110),rule('R-L2-001','写操作确认','创建工单','服务端确认凭据有效且未消费','会话绑定的一次性确认卡','创建工单并记录审计',90),rule('R-HAND-001','连续未解决转人工','多轮对话','连续未解决 >= 5','服务端计数','转订单客服',80,5),rule('R-TOOL-001','连续工具失败','工具异常','连续失败 >= 2','失败计数','重试一次后转物流客服',85,2)]
