import logging
import re
from langchain.docstore.document import Document
from configs import EMBEDDING_MODEL, logger
from server.model_workers.base import ApiEmbeddingsParams
from server.utils import BaseResponse, get_model_worker_config, list_embed_models, list_online_embed_models
from fastapi import Body
from fastapi.concurrency import run_in_threadpool
from typing import Dict, List

online_embed_models = list_online_embed_models()


def clean_text_for_api(text: str) -> str:
    """
    清洗送往在线API的文本，过滤掉纯标点、纯空白符或过于碎屑的无意义OCR残渣
    """
    if not text or not isinstance(text, str):
        return ""
    # 去除两端空格
    t = text.strip()
    # 如果清洗后只剩下换行、空格或特殊符号，或者长度极短，返回空字符串以便后续平替
    if not t or len(t) < 2:
        return ""
    # 过滤掉完全由标点符号组成的字符串
    if re.match(r'^[^\w\s]+$', t):
        return ""
    return t


def embed_texts(
        texts: List[str],
        embed_model: str = EMBEDDING_MODEL,
        to_query: bool = False,
) -> BaseResponse:
    try:
        # ⬇️ 针对 OpenAI-API / Gitee AI 的高级同步清洗拦截器 ⬇️
        if embed_model == "openai-api":
            import requests
            from configs.model_config import ONLINE_LLM_MODEL
            
            config = ONLINE_LLM_MODEL.get("openai-api", {})
            url = f"{config.get('api_base_url').rstrip('/')}/embeddings"
            headers = {
                "Authorization": f"Bearer {config.get('api_key')}",
                "Content-Type": "application/json"
            }
            
            res_data = []
            for text in texts:
                cleaned_text = clean_text_for_api(text)
                if not cleaned_text:
                    # 必须使用固定文本占位，确保返回的向量数量与输入的 texts 严格对齐，防止 LangChain/FAISS 报错
                    cleaned_text = "Empty text token holder"
                
                payload = {
                    "model": config.get("embed_model"),
                    "input": cleaned_text  # 送入严格校验的单条纯字符串
                }
                response = requests.post(url, json=payload, headers=headers)
                if response.status_code == 200:
                    res_json = response.json()
                    if isinstance(res_json.get("data"), list) and len(res_json["data"]) > 0:
                        res_data.append(res_json["data"][0]["embedding"])
                    elif "embedding" in res_json.get("data", {}):
                        res_data.append(res_json["data"]["embedding"])
                else:
                    logger.error(f"Gitee API 同步错误响应. 原始文本: {text[:20]}... 错误: {response.text}")
                    return BaseResponse(code=response.status_code, msg=f"Gitee API 错误: {response.text}")
            
            return BaseResponse(data=res_data)
        # ⬆️ 针对 OpenAI-API / Gitee AI 的高级同步清洗拦截器 ⬆️

        if embed_model in list_embed_models():  # 使用本地Embeddings模型
            from server.utils import load_local_embeddings
            embeddings = load_local_embeddings(model=embed_model)
            return BaseResponse(data=embeddings.embed_documents(texts))

        if embed_model in list_online_embed_models():  # 使用在线API
            config = get_model_worker_config(embed_model)
            worker_class = config.get("worker_class")
            embed_model = config.get("embed_model")
            worker = worker_class()
            if worker_class.can_embedding():
                params = ApiEmbeddingsParams(texts=texts, to_query=to_query, embed_model=embed_model)
                resp = worker.do_embeddings(params)
                return BaseResponse(**resp)

        return BaseResponse(code=500, msg=f"指定的模型 {embed_model} 不支持 Embeddings 功能。")
    except Exception as e:
        logger.error(e)
        return BaseResponse(code=500, msg=f"文本向量化过程中出现错误：{e}")


async def aembed_texts(
        texts: List[str],
        embed_model: str = EMBEDDING_MODEL,
        to_query: bool = False,
) -> BaseResponse:
    """
    异步文本向量化接口
    """
    try:
        # ⬇️ 针对 OpenAI-API / Gitee AI 的高级异步清洗拦截器 ⬇️
        if embed_model == "openai-api":
            import httpx
            from configs.model_config import ONLINE_LLM_MODEL
            
            config = ONLINE_LLM_MODEL.get("openai-api", {})
            url = f"{config.get('api_base_url').rstrip('/')}/embeddings"
            headers = {
                "Authorization": f"Bearer {config.get('api_key')}",
                "Content-Type": "application/json"
            }
            
            res_data = []
            # 使用 httpx 异步循环发送纯文本请求
            async with httpx.AsyncClient() as client:
                for text in texts:
                    cleaned_text = clean_text_for_api(text)
                    if not cleaned_text:
                        # 保持 1:1 数量对齐
                        cleaned_text = "Empty text token holder"
                        
                    payload = {
                        "model": config.get("embed_model"),
                        "input": cleaned_text  # 传入单条清洗过的纯字符串
                    }
                    response = await client.post(url, json=payload, headers=headers, timeout=60.0)
                    if response.status_code == 200:
                        res_json = response.json()
                        if isinstance(res_json.get("data"), list) and len(res_json["data"]) > 0:
                            res_data.append(res_json["data"][0]["embedding"])
                        elif "embedding" in res_json.get("data", {}):
                            res_data.append(res_json["data"]["embedding"])
                    else:
                        logger.error(f"Gitee API 异步错误响应. 原始文本: {text[:20]}... 错误: {response.text}")
                        return BaseResponse(code=response.status_code, msg=f"Gitee API 错误: {response.text}")
            
            return BaseResponse(data=res_data)
        # ⬆️ 针对 OpenAI-API / Gitee AI 的高级异步清洗拦截器 ⬆️

        if embed_model in list_embed_models():  # 使用本地Embeddings模型
            from server.utils import load_local_embeddings
            embeddings = load_local_embeddings(model=embed_model)
            return BaseResponse(data=await embeddings.aembed_documents(texts))

        if embed_model in list_online_embed_models():  # 使用在线API
            config = get_model_worker_config(embed_model)
            worker_class = config.get("worker_class")
            embed_model = config.get("embed_model")
            worker = worker_class()
            if worker_class.can_embedding():
                from server.utils import ApiEmbeddingsParams
                params = ApiEmbeddingsParams(texts=texts, to_query=to_query, embed_model=embed_model)
                resp = await worker.ado_embeddings(params)
                return BaseResponse(**resp)

        return BaseResponse(code=500, msg=f"指定的模型 {embed_model} 不支持 Embeddings 功能。")
    except Exception as e:
        logger.error(e)
        return BaseResponse(code=500, msg=f"文本向量化过程中出现错误：{e}")


def embed_texts_endpoint(
        texts: List[str] = Body(..., description="要嵌入的文本列表", examples=[["hello", "world"]]),
        embed_model: str = Body(EMBEDDING_MODEL,
                                description=f"使用的嵌入模型，除了本地部署的Embedding模型，也支持在线API({online_embed_models})提供的嵌入服务。"),
        to_query: bool = Body(False, description="向量是否用于查询。有些模型如Minimax对存储/查询的向量进行了区分优化。"),
) -> BaseResponse:
    """
    对文本进行向量化，返回 BaseResponse(data=List[List[float]])
    """
    return embed_texts(texts=texts, embed_model=embed_model, to_query=to_query)


def embed_documents(
        docs: List[Document],
        embed_model: str = EMBEDDING_MODEL,
        to_query: bool = False,
) -> Dict:
    """
    将 List[Document] 向量化，转化为 VectorStore.add_embeddings 可以接受的参数
    """
    texts = [x.page_content for x in docs]
    metadatas = [x.metadata for x in docs]
    embeddings = embed_texts(texts=texts, embed_model=embed_model, to_query=to_query).data
    if embeddings is not None:
        return {
            "texts": texts,
            "embeddings": embeddings,
            "metadatas": metadatas,
        }