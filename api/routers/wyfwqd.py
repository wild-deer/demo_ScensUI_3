
from fastapi import UploadFile,File,Form,APIRouter,Request,responses,HTTPException
from fastapi.responses import StreamingResponse,JSONResponse
import os
from datetime import datetime
import uuid
from termcolor import colored
from typing import Literal,AsyncGenerator,Optional

import sys
import json
from pydantic import BaseModel
import asyncio
# 大纲优化
router = APIRouter()

# 获取当前脚本所在的目录
current_dir = os.path.dirname(os.path.abspath(__file__))

# 获取根目录（假设 db_config 在根目录）
root_dir = os.path.dirname(current_dir)

# 将根目录添加到 sys.path 中
sys.path.append(root_dir)



