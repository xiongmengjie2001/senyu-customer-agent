import React,{useState,useEffect,useRef} from 'react';
import './commerce.css';

export function ProductVisual({product}){const id=product.product_id||product.id;return <div className={'product-visual model-'+id}><div className="appliance"><i/><b/></div><small>{id}</small></div>}

export function Catalog({products,busy,onCheckout,onAsk}){
 const[chosen,Choose]=useState(null),[quantity,Quantity]=useState(1),[scenario,Scenario]=useState('normal');
 const checkoutRef=useRef();useEffect(()=>{if(chosen)checkoutRef.current?.scrollIntoView({block:'center'})},[chosen]);
 return <div className="catalog-view"><div className="commerce-intro"><small>SENYU MOCK STORE</small><h1>选一件好物，服务一直在。</h1><p>从选购、模拟购买，到物流、售后、服务评价，全部可在这里完成。</p><span className="simulation-badge">模拟商城 · 不会真实扣款或发货</span></div><div className="catalog-grid">{products.map(p=><article className={'catalog-product '+(chosen?.id===p.id?'chosen':'')} key={p.id}><div className="product-stage"><ProductVisual product={p}/><span>{p.style}</span></div><h3>{p.name}</h3><p>{p.color} · {p.capacity} · {p.power}</p><div className="catalog-price">¥{p.price.toFixed(2)}<small>模拟库存 {p.stock??30} 件</small></div><div className="buttons"><button disabled={busy||(p.stock??30)<1} onClick={()=>{Choose(p);Quantity(1)}}>模拟购买</button><button className="secondary" disabled={busy} onClick={()=>onAsk(p.id+' 使用方法')}>咨询商品</button></div></article>)}</div>{chosen&&<form ref={checkoutRef} className="checkout-box" onSubmit={e=>{e.preventDefault();onCheckout({product_id:chosen.id,quantity:Number(quantity),scenario})}}><div><h3>确认模拟购买意向</h3><p>{chosen.name} · {chosen.color} · 单价 ¥{chosen.price.toFixed(2)}</p></div><label>数量<select aria-label="购买数量" value={quantity} onChange={e=>Quantity(e.target.value)}>{[1,2,3,4,5].map(n=><option key={n}>{n}</option>)}</select></label><label>模拟物流场景<select aria-label="模拟物流场景" value={scenario} onChange={e=>Scenario(e.target.value)}><option value="normal">正常发货配送</option><option value="stalled">已发货但 49 小时未更新</option></select></label><strong>合计 ¥{(chosen.price*quantity).toFixed(2)}</strong><small>下一步只生成确认卡，您再次确认后才创建订单。</small><div className="buttons"><button disabled={busy}>生成购买确认</button><button type="button" className="secondary" onClick={()=>Choose(null)}>暂不购买</button></div></form>}</div>
}

export function Orders({orders,busy,onView,onRefund,onShop}){
 return <div className="orders-view"><div className="commerce-intro"><small>MY ORDERS</small><h1>每笔订单，都有后续。</h1><p>物流和售后来自当前账户的模拟数据库，更新后会持久保存。</p></div>{!orders.length&&<div className="panel"><p>还没有订单，先去选择一件商品吧。</p><button onClick={onShop}>前往商城</button></div>}{orders.map(o=><article className="my-order" key={o.id}><div className="my-order-top"><small>{o.id}</small><span className="pill">{o.status}</span></div><div className="my-order-detail"><ProductVisual product={o}/><div><h3>{o.product} · {o.color}</h3><p>{o.style} · 数量 {o.quantity||1}</p><small>{o.mock?'本次模拟购买订单':'历史演示种子订单'} · {o.tracking||'待发货'}</small></div><strong>¥{o.amount.toFixed(2)}</strong></div><div className="buttons"><button disabled={busy} onClick={()=>onView(o)}>查看物流</button><button className="secondary" disabled={busy} onClick={()=>onRefund(o)}>退款 / 售后</button></div></article>)}</div>
}

function RatingForm({card,current,busy,onSubmit}){
 const[stars,Stars]=useState(card.submitted_stars||5),[comment,Comment]=useState(card.submitted_comment||'');
 return <div className="card rating-form"><div className="card-title">本次服务，您满意吗？</div><div className="stars" role="group" aria-label="选择星级">{[1,2,3,4,5].map(n=><button type="button" key={n} disabled={busy||!current} aria-label={n+'星'} aria-pressed={stars===n} onClick={()=>Stars(n)}>{n<=stars?'★':'☆'}</button>)}</div><p>{['','很不满意','不满意','一般','满意','非常满意'][stars]} · {stars} 星</p><label>评价或需要改进的地方<textarea aria-label="评价意见" value={comment} maxLength={500} onChange={e=>Comment(e.target.value)} disabled={!current}/></label><button disabled={busy||!current} onClick={()=>onSubmit({evaluation_id:card.evaluation_id,stars,comment})}>提交评价</button><small>低分后会继续提供解决方案，不自动强制转人工。</small></div>
}

function RefundForm({card,current,busy,onSubmit}){
 const[reason,Reason]=useState(card.submitted_reason||'不想要了'),[intact,Intact]=useState(card.submitted_intact??true);
 return <form className="card" onSubmit={e=>{e.preventDefault();onSubmit({order_id:card.order.id,reason,intact})}}><div className="card-title">售后申请信息<span className="pill">先核对，再确认</span></div><p>{card.order.product} · {card.order.id}<br/>商品金额 ¥{card.order.amount.toFixed(2)}</p><label>申请原因<select aria-label="退款原因" value={reason} disabled={!current} onChange={e=>Reason(e.target.value)}>{['不想要了','质量问题','商品不符','物流太慢','其他'].map(x=><option key={x}>{x}</option>)}</select></label><label className="inline-check"><input type="checkbox" checked={intact} disabled={!current} onChange={e=>Intact(e.target.checked)}/>商品完好，不影响二次销售（已发货退货适用）</label><button disabled={busy||!current}>核对条件并生成确认</button><small>未发货按取消退款流程；已发货按退货验收流程。全部为模拟业务。</small></form>
}

export function LifecycleCard({card:c,session,current,busy,mutate,send,shop,myOrders}){
 if(c.type==='catalog')return <div className="card"><Catalog products={c.products} busy={busy||!current} onAsk={send} onCheckout={body=>mutate('/checkout',body)}/></div>;
 if(c.type==='order_created')return <div className="card"><div className="card-title">✓ 模拟购买成功<span className="pill">未发生真实支付</span></div><p>{c.order.product} · {c.order.color} × {c.order.quantity}<br/>订单 {c.order.id}<br/>模拟金额 ¥{c.order.amount.toFixed(2)}</p><div className="buttons"><button disabled={busy||!current} onClick={()=>send(c.order.id+' 查物流')}>查看本单物流</button><button className="secondary" onClick={myOrders}>我的订单</button><button className="secondary" onClick={shop}>继续购物</button></div></div>;
 if(c.type==='resolution')return <div className="resolution-actions">{c.actions.map(a=><button key={a.text} className="secondary" disabled={busy||!current} onClick={()=>send(a.text)}>{a.label}</button>)}</div>;
 if(c.type==='refund_form')return <RefundForm card={c} current={current} busy={busy} onSubmit={body=>mutate('/refund',body)}/>;
 if(c.type==='refund')return <div className="card"><div className="card-title">售后与退款进度<span className="pill">模拟售后</span></div><h3>{c.refund.status}</h3><p>{c.refund.id}<br/>关联订单 {c.refund.order_id}<br/>模拟退款金额 ¥{c.refund.amount.toFixed(2)}</p><div className="timeline">{c.refund.events.map((e,i)=><div key={i}><i/><small>{e.time}</small><p>{e.text}</p></div>)}</div><div className="buttons">{c.refund.step<4?<button disabled={busy||!current} onClick={()=>mutate('/refund/'+c.refund.id+'/advance',{expected_version:c.refund.version})}>{['模拟寄回商品','模拟包裹入库','模拟验收通过','模拟退款到账'][c.refund.step]}</button>:<button disabled={busy||!current} onClick={()=>mutate('/finish')}>问题已解决，评价服务</button>}<button className="secondary" onClick={myOrders}>查看订单</button></div><small>每一步写入本地数据库，不会真实寄件、验收或退款。</small></div>;
 if(c.type==='rating')return <RatingForm card={c} current={current} busy={busy} onSubmit={body=>mutate('/rating',body)}/>;
 return null
}

export function ServiceReport({api}){
 const[data,Data]=useState(null),[category,Category]=useState('全部'),[error,Error]=useState('');
 async function load(){try{Data(await api('/admin/service-report','admin'))}catch(e){Error(e.message)}}
 useEffect(()=>{load()},[]);
 return <div><div className="toolbar"><h3>问题归档与服务评价</h3><button onClick={load}>刷新归档</button></div>{error&&<p role="alert">{error}</p>}<div className="stats">{[['模拟购买订单',data?.simulated_purchases],['售后申请',data?.refunds],['平均服务星级',data?.average_stars??'暂无评价'],['低分待跟进',data?.low_ratings]].map(([label,value])=><div key={label}><small>{label}</small><strong>{value??0}</strong></div>)}</div><label>问题分类<select aria-label="问题分类筛选" value={category} onChange={e=>Category(e.target.value)}>{['全部',...Object.keys(data?.categories||{})].map(c=><option key={c}>{c}</option>)}</select></label><div className="table-wrap"><table><thead><tr><th>分类 / 状态</th><th>用户 / 订单</th><th>用户诉求</th><th>处理去向</th></tr></thead><tbody>{data?.issues.filter(i=>category==='全部'||i.category===category).map(i=><tr key={i.id}><td><strong>{i.category}</strong><small>{i.status}</small></td><td>{i.user?.display_name||i.user_id}<small>{i.order_id||'未关联订单'}</small></td><td>{i.summary}</td><td>{i.queue||'智能客服自助处理'}</td></tr>)}</tbody></table></div></div>
}

export function ModelSettings({api}){
 const[status,Status]=useState(null),[result,Result]=useState(''),[testing,Testing]=useState(false);
 useEffect(()=>{api('/admin/model-status','admin').then(Status).catch(e=>Result(e.message))},[]);
 return <div className="panel model-settings"><h3>模型接入</h3><p>购买、物流、退款权限和价格由业务系统决定；模型用于理解更多口语表达。无需先部署 Dify，也可以直接接入兼容接口。</p><dl><dt>当前模型</dt><dd>{status?.model}</dd><dt>接口地址</dt><dd>{status?.base_url}</dd><dt>密钥</dt><dd>{status?.configured?'已在服务端配置（不回传浏览器）':'未配置'}</dd><dt>启用状态</dt><dd>{status?.enabled?'已启用':'未启用，当前使用本地理解'}</dd></dl><p>在项目服务器的 .env 中填写以下配置后重启服务：</p><pre>APP_MODE=local{'\n'}ENABLE_LLM=true{'\n'}LLM_BASE_URL=兼容接口的 /v1 地址{'\n'}LLM_MODEL=模型名称{'\n'}LLM_API_KEY=你自己的密钥</pre><button disabled={!status?.configured||testing} onClick={async()=>{Testing(true);try{let r=await api('/admin/model-test','admin','POST');Result(r.connected?'连接测试通过':'连接未通过')}catch(e){Result(e.message)}finally{Testing(false)}}}>{testing?'正在测试…':'测试模型连接'}</button><p role="status">{result}</p><small>密钥不写入前端、不提交 GitHub。只有配置后启用或主动测试时才会调用该接口。</small></div>
}
