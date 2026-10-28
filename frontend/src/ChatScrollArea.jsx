import React,{useLayoutEffect,useRef,useState} from 'react';
import './chat-scroll.css';

// 滚动仅作用于会话容器，输入框变化不触发滚动或重建消息树。
export default function ChatScrollArea({sessionKey,lastMessageId,busy,children}){
 const container=useRef(null);
 const following=useRef(true);
 const previous=useRef({sessionKey:null,lastMessageId:null});
 const[unread,Unread]=useState(false);
 function jump(){
  const node=container.current;
  if(!node)return;
  following.current=true;
  node.scrollTop=node.scrollHeight;
  Unread(false);
 }
 useLayoutEffect(()=>{
  const node=container.current;
  if(!node)return;
  const switched=previous.current.sessionKey!==sessionKey;
  const added=previous.current.lastMessageId!==lastMessageId;
  if(switched||following.current){
   following.current=true;
   node.scrollTop=node.scrollHeight;
   Unread(false);
  }else if(added){
   Unread(true);
  }
  previous.current={sessionKey,lastMessageId};
 },[sessionKey,lastMessageId,busy]);
 function onScroll(){
  const node=container.current;
  following.current=node.scrollHeight-node.clientHeight-node.scrollTop<=80;
  if(following.current)Unread(false);
 }
 return <div className="chat-scroll-area"><div className="messages" ref={container} onScroll={onScroll} tabIndex={0} role="log" aria-label="聊天记录" aria-live="polite" aria-relevant="additions">{children}</div>{unread&&<button type="button" className="new-message-notice" onClick={jump}>有新消息 · 回到底部 ↓</button>}</div>
}
