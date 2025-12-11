
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


async def generate_content(pageNum:int,ppturl:str="",imageUrls:list[str] = [""])->AsyncGenerator[dict,any]:
    """
    此函数用于流式返回

    :param pageNum str: ppt的总的页数
    :param ppturl str: 返回生成的ppt的链接
    :param imageUrls list: 用于流式返回的每页ppt的链接
    """
    # 这里模拟流式返回内容，你可以根据实际需求修改
    for item in range(pageNum):
        await asyncio.sleep(0)
        content={
            "currentpage":item+1,
            "imageUrl":imageUrls[0]
        }
        # 将字典转换为 JSON 字符串并编码为字节
        yield json.dumps(content).encode('utf-8')
    await asyncio.sleep(0.5)
    content={
        "ppturl":ppturl
    }
    yield json.dumps(content).encode('utf-8')
    


class OutlineInfo(BaseModel):
    strToExtentd:str
    uid:str
@router.post("/compress_extent_outline")
async def outline_prety(
    outlineinfo:OutlineInfo,
    request:Request
):
    """
    ppt大纲优化接口，用于扩写ppt大纲

    :param OutlineInfo outlineinfo: 传入信息，需要扩写的ppt的信息
    """
    strToExtentd = outlineinfo.strToExtentd
    uid = outlineinfo.uid
    server_host = request.url.hostname  # 获取服务端的主机名
    server_port = request.url.port # 获取服务端的端口号
    
    print(colored(f"需要扩展的句子：{strToExtentd}","grey"))
    # 检查文件是否成功上传
    if not strToExtentd:
        return responses.JSONResponse(status_code=400, content={"message": "No file uploaded"})
    current_time = uid
    # 获取文件内容并保存到服务器（可选）
    # 检查目录是否存在，如果不存在则创建
    if not os.path.exists(f"pptoutput/{current_time}"):
        os.makedirs(f"pptoutput/{current_time}")

    return StreamingResponse(generate_content(1,ppt_url,imageUrls = imageUrls), media_type="application/json")

UPLOAD_DIR = "uploads"  # 确保这个目录存在

@router.post("/upload")
async def upload_file(file: UploadFile = File(...), 
                      file_name: Optional[str] = None):
    """处理文件上传请求"""
    try:
        # 生成UUID目录
        uuid_dir = str(uuid.uuid4())
        upload_path = os.path.join(UPLOAD_DIR, uuid_dir)
        
        # 创建UUID目录（包括父目录）
        os.makedirs(upload_path, exist_ok=True)
        
        # 生成唯一文件名（避免重名）
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        original_filename = file.filename or "unknown_file"
        file_ext = os.path.splitext(original_filename)[1]
        safe_filename = f"{timestamp}_{original_filename.replace(' ', '_')}"
        
        # 保存文件到UUID目录
        file_path = os.path.join(upload_path, safe_filename)
        with open(file_path, "wb") as buffer:
            contents = await file.read()  # 异步读取文件内容
            buffer.write(contents)
        
        # 可选：记录上传信息
        upload_info = {
            "original_filename": original_filename,
            "saved_filename": safe_filename,
            "upload_time": datetime.now().isoformat(),
            "size": len(contents),
            "content_type": file.content_type,
            "storage_directory": uuid_dir
        }
        
        # 如果前端传递了fileName参数
        if file_name:
            upload_info["provided_file_name"] = file_name
            
        return JSONResponse(
            status_code=200,
            content={"success": True, "message": "文件上传成功", "data": upload_info}
        )
        
    except Exception as e:
        # 发生错误时返回500错误
        raise HTTPException(
            status_code=500, 
            detail=f"文件上传失败: {str(e)}"
        )
    finally:
        # 关闭文件
        await file.close()