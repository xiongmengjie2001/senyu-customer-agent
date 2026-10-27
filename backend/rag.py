"""无付费模型的中文字符 ngram 向量 + FAISS；显式标注为词法向量。"""
import hashlib, re
import faiss
import numpy as np

def vector(text):
 text = re.sub(r'\s+', '', text.lower())
 v = np.zeros(2048, dtype='float32')
 for n in (1,2,3):
  for i in range(max(0,len(text)-n+1)):
   token=text[i:i+n]; j=int.from_bytes(hashlib.blake2b(token.encode(),digest_size=4).digest(),'big')%2048
   v[j]+=1
 norm=np.linalg.norm(v)
 return v/max(float(norm),1e-9)

def search(query, entries):
 docs=[x for x in entries if x['status']=='发布']
 if not docs:return []
 matrix=np.stack([vector(x['title']+' '+x['keywords']+' '+x['content']) for x in docs])
 index=faiss.IndexFlatIP(2048);index.add(matrix)
 scores,ids=index.search(vector(query).reshape(1,-1),min(3,len(docs)))
 return [dict(docs[int(i)],score=round(float(s),3)) for s,i in zip(scores[0],ids[0]) if s>=0.20 and any(k in query for k in docs[int(i)]['keywords'].split())]
