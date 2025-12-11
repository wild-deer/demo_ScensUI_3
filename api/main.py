# -*- coding: utf-8 -*-
import uvicorn

from fastapi import FastAPI
from fastapi.responses import  FileResponse
from fastapi.middleware.cors import CORSMiddleware

from fastapi.staticfiles import StaticFiles


import routers.wyfwqd







app = FastAPI(docs_url=None,redoc_url=None)
subprocs = {}  # 用于保存子进程信息的全局字典

fake_db = {"testuser": {"password": "testpass", "files": []}}
origins = [
    "http://1.14.190.231:13089",
]




app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(routers.wyfwqd.router)



if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8889, reload=True)
