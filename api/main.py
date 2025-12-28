# -*- coding: utf-8 -*-
import uvicorn
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

import routers.崩滑物源算法_接口
import routers.坡面物源算法_接口
import routers.沟道物源算法_接口








app = FastAPI()
subprocs = {}  # 用于保存子进程信息的全局字典

fake_db = {"testuser": {"password": "testpass", "files": []}}
origins = [
    "*",
]




app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(routers.崩滑物源算法_接口.router)
app.include_router(routers.坡面物源算法_接口.router)
app.include_router(routers.沟道物源算法_接口.router)

base_dir = Path(__file__).parent
outputs_dir = base_dir / "outputs"
outputs_dir.mkdir(exist_ok=True)
app.mount("/files", StaticFiles(directory=str(outputs_dir)), name="files")

@app.get("/test")
def test_endpoint():
    return {"message": "test接口正常工作"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=25376, reload=True)