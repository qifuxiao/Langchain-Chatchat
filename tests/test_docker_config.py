"""Regression checks that do not need application packages or model credentials."""
import os
from pathlib import Path
import runpy
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
PREPARE = runpy.run_path(str(ROOT / "docker/prepare_configs.py"))["prepare_configs"]


class DockerConfigTests(unittest.TestCase):
    def load_config(self, env):
        with patch.dict(os.environ, env, clear=True):
            return runpy.run_path(str(ROOT / "configs/model_config.py.example"))

    def test_missing_config_files_are_filled_individually(self):
        with tempfile.TemporaryDirectory() as name:
            directory = Path(name)
            (directory / "model_config.py").write_text("custom model settings")
            (directory / "model_config.py.example").write_text("defaults")
            (directory / "server_config.py.example").write_text("server defaults")
            PREPARE(directory)
            PREPARE(directory)
            self.assertEqual((directory / "model_config.py").read_text(), "custom model settings")
            self.assertEqual((directory / "server_config.py").read_text(), "server defaults")

    def test_api_defaults_have_no_secret_or_local_model(self):
        config = self.load_config({})
        self.assertEqual(config["EMBEDDING_MODEL"], "openai-api")
        self.assertEqual(config["LLM_MODELS"], ["openai"])
        self.assertFalse(config["USE_RERANKER"])
        self.assertTrue(all(not paths for paths in config["MODEL_PATH"].values()))
        for model in config["ONLINE_LLM_MODEL"].values():
            self.assertEqual(model["api_key"], "")
            self.assertEqual(model["provider"], "OpenAIWorker")

    def test_separate_intranet_embedding_endpoint(self):
        config = self.load_config({
            "OPENAI_API_BASE_URL": "http://llm.internal/v1",
            "OPENAI_API_KEY": "test-chat-key",
            "OPENAI_CHAT_MODEL": "chat-model",
            "OPENAI_EMBEDDING_API_BASE_URL": "http://embed.internal/v1",
            "OPENAI_EMBEDDING_API_KEY": "test-embed-key",
            "OPENAI_EMBEDDING_MODEL": "embed-model",
        })["ONLINE_LLM_MODEL"]
        self.assertEqual(config["openai"]["api_base_url"], "http://llm.internal/v1")
        self.assertEqual(config["openai"]["api_key"], "test-chat-key")
        self.assertEqual(config["openai"]["model_name"], "chat-model")
        self.assertEqual(config["openai-api"]["api_base_url"], "http://embed.internal/v1")
        self.assertEqual(config["openai-api"]["api_key"], "test-embed-key")
        self.assertEqual(config["openai-api"]["embed_model"], "embed-model")

    def test_gitee_aliases_share_endpoint_and_key(self):
        config = self.load_config({"GITEE_AI_API_BASE_URL": "http://shared/v1", "GITEE_AI_API_KEY": "test-key"})
        for model in config["ONLINE_LLM_MODEL"].values():
            self.assertEqual(model["api_base_url"], "http://shared/v1")
            self.assertEqual(model["api_key"], "test-key")

    def test_generic_settings_override_gitee_aliases(self):
        config = self.load_config({"GITEE_AI_API_KEY": "gitee-test", "OPENAI_API_KEY": "generic-test"})
        self.assertEqual(config["ONLINE_LLM_MODEL"]["openai"]["api_key"], "generic-test")


if __name__ == "__main__":
    unittest.main()
