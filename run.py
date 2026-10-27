"""在项目独立依赖目录启动，不修改全局 Python 包。"""
import os,sys
from pathlib import Path
root=Path(__file__).resolve().parent
sys.path.insert(0,str(root/'.runtime'));sys.path.insert(0,str(root));os.chdir(root)
if __name__=='__main__':
 import uvicorn
 from dotenv import load_dotenv
 load_dotenv(root/'.env')
 uvicorn.run('backend.main:app',host=os.getenv('APP_HOST','127.0.0.1'),port=int(os.getenv('APP_PORT','8000')))
