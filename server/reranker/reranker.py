import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from typing import Any, Optional, Sequence
import httpx
from langchain_core.documents import Document
from langchain.callbacks.manager import Callbacks
from langchain.retrievers.document_compressors.base import BaseDocumentCompressor
from pydantic import Field, PrivateAttr


class LangchainReranker(BaseDocumentCompressor):
    """Document compressor that uses `Cohere Rerank API`."""
    model_name_or_path: str = Field()
    _model: Any = PrivateAttr()
    top_n: int = Field()
    device: str = Field()
    max_length: int = Field()
    batch_size: int = Field()
    # show_progress_bar: bool = None
    num_workers: int = Field()

    # activation_fct = None
    # apply_softmax = False

    def __init__(self,
                 model_name_or_path: str,
                 top_n: int = 3,
                 device: str = "cuda",
                 max_length: int = 1024,
                 batch_size: int = 32,
                 # show_progress_bar: bool = None,
                 num_workers: int = 0,
                 # activation_fct = None,
                 # apply_softmax = False,
                 ):
        # self.top_n=top_n
        # self.model_name_or_path=model_name_or_path
        # self.device=device
        # self.max_length=max_length
        # self.batch_size=batch_size
        # self.show_progress_bar=show_progress_bar
        # self.num_workers=num_workers
        # self.activation_fct=activation_fct
        # self.apply_softmax=apply_softmax

        # Keep this import local: the Gitee-only Docker image deliberately omits
        # the heavyweight local reranking dependencies.
        from sentence_transformers import CrossEncoder
        self._model = CrossEncoder(model_name=model_name_or_path, max_length=1024, device=device)
        super().__init__(
            top_n=top_n,
            model_name_or_path=model_name_or_path,
            device=device,
            max_length=max_length,
            batch_size=batch_size,
            # show_progress_bar=show_progress_bar,
            num_workers=num_workers,
            # activation_fct=activation_fct,
            # apply_softmax=apply_softmax
        )

    def compress_documents(
            self,
            documents: Sequence[Document],
            query: str,
            callbacks: Optional[Callbacks] = None,
    ) -> Sequence[Document]:
        """
        Compress documents using Cohere's rerank API.

        Args:
            documents: A sequence of documents to compress.
            query: The query to use for compressing the documents.
            callbacks: Callbacks to run during the compression process.

        Returns:
            A sequence of compressed documents.
        """
        if len(documents) == 0:  # to avoid empty api call
            return []
        doc_list = list(documents)
        _docs = [d.page_content for d in doc_list]
        sentence_pairs = [[query, _doc] for _doc in _docs]
        results = self._model.predict(sentences=sentence_pairs,
                                      batch_size=self.batch_size,
                                      #  show_progress_bar=self.show_progress_bar,
                                      num_workers=self.num_workers,
                                      #  activation_fct=self.activation_fct,
                                      #  apply_softmax=self.apply_softmax,
                                      convert_to_tensor=True
                                      )
        top_k = self.top_n if self.top_n < len(results) else len(results)

        values, indices = results.topk(top_k)
        final_results = []
        for value, index in zip(values, indices):
            doc = doc_list[index]
            doc.metadata["relevance_score"] = value
            final_results.append(doc)
        return final_results


class OpenAIReranker(BaseDocumentCompressor):
    """Rerank documents through an OpenAI-compatible ``/rerank`` endpoint."""

    model_name: str = Field()
    api_base_url: str = Field()
    api_key: str = Field()
    top_n: int = Field()
    timeout: float = Field(default=120.0)

    def __init__(
            self,
            model_name: str,
            api_base_url: str,
            api_key: str,
            top_n: int = 3,
            timeout: float = 120.0,
    ):
        super().__init__(
            model_name=model_name,
            api_base_url=api_base_url.rstrip("/"),
            api_key=api_key,
            top_n=top_n,
            timeout=timeout,
        )

    def compress_documents(
            self,
            documents: Sequence[Document],
            query: str,
            callbacks: Optional[Callbacks] = None,
    ) -> Sequence[Document]:
        if not documents:
            return []

        doc_list = list(documents)
        response = httpx.post(
            f"{self.api_base_url}/rerank",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": self.model_name,
                "query": query,
                "documents": [document.page_content for document in doc_list],
                "top_n": min(self.top_n, len(doc_list)),
            },
            timeout=self.timeout,
        )
        response.raise_for_status()
        payload = response.json()
        results = payload.get("results")
        if not isinstance(results, list):
            raise RuntimeError(f"Unexpected rerank response: {payload}")

        reranked_documents = []
        for result in results:
            index = result.get("index")
            if not isinstance(index, int) or not 0 <= index < len(doc_list):
                continue
            document = doc_list[index]
            document.metadata["relevance_score"] = result.get("relevance_score")
            reranked_documents.append(document)

        if not reranked_documents:
            raise RuntimeError(f"Rerank response contains no valid document indexes: {payload}")
        return reranked_documents[:self.top_n]


if __name__ == "__main__":
    from configs import (LLM_MODELS,
                         VECTOR_SEARCH_TOP_K,
                         SCORE_THRESHOLD,
                         TEMPERATURE,
                         USE_RERANKER,
                         RERANKER_MODEL,
                         RERANKER_MAX_LENGTH,
                         MODEL_PATH)
    from server.utils import embedding_device

    if USE_RERANKER:
        reranker_model_path = MODEL_PATH["reranker"].get(RERANKER_MODEL, "BAAI/bge-reranker-large")
        print("-----------------model path------------------")
        print(reranker_model_path)
        reranker_model = LangchainReranker(top_n=3,
                                           device=embedding_device(),
                                           max_length=RERANKER_MAX_LENGTH,
                                           model_name_or_path=reranker_model_path
                                           )
