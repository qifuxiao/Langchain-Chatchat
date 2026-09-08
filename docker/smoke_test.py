"""Build-time import checks. No model requests or database writes."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import importlib.metadata
import torch

assert torch.version.cuda is None, "Expected CPU-only torch"
for distribution in importlib.metadata.distributions():
    name = distribution.metadata["Name"].lower().replace("_", "-")
    assert not name.startswith("nvidia-"), name
    assert name not in {"vllm", "xformers", "triton", "torchvision", "sentence-transformers", "unstructured-inference"}, name

import startup
from server.api import create_app
from server.model_workers import OpenAIWorker
from document_loaders import RapidOCRPDFLoader
from document_loaders.ocr import get_ocr
from server.knowledge_base.utils import make_text_splitter
from configs import EMBEDDING_MODEL, LLM_MODELS, ONLINE_LLM_MODEL, USE_RERANKER
assert EMBEDDING_MODEL == "openai-api"
assert LLM_MODELS == ["openai"]
assert not USE_RERANKER
assert ONLINE_LLM_MODEL["openai-api"]["embed_model"]
worker = OpenAIWorker(model_names=["openai"], no_register=True)
assert worker.model_names == ["openai"]
assert create_app().openapi()["paths"]
assert make_text_splitter().split_text("文档导入检查。" * 100)
assert get_ocr() is not None
import nltk
assert nltk.data.find("tokenizers/punkt/english.pickle")
assert nltk.data.find("taggers/averaged_perceptron_tagger/averaged_perceptron_tagger.pickle")
from unstructured.partition.text import partition_text
assert partition_text(text="This is a document parsing check. It must work offline.")
import streamlit
import st_aggrid
import streamlit_chatbox
print("CPU API deployment smoke checks passed")
