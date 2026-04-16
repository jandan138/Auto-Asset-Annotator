import builtins
import importlib
import io
import os
import types
import sys
import tempfile
import unittest
from unittest import mock
from urllib import error

from PIL import Image

from src.auto_asset_annotator.config.settings import ModelConfig


class TestModelBackendFactory(unittest.TestCase):
    def get_model_module(self):
        return importlib.import_module("src.auto_asset_annotator.core.model")

    def import_model_module_with_blocked_heavy_deps(self):
        module_name = "src.auto_asset_annotator.core.model"
        original_import = builtins.__import__

        def blocked_import(name, *args, **kwargs):
            if name in {"torch", "transformers", "qwen_vl_utils"}:
                raise ImportError(f"blocked import: {name}")
            return original_import(name, *args, **kwargs)

        original_module = sys.modules.pop(module_name, None)
        try:
            builtins.__import__ = blocked_import
            return importlib.import_module(module_name)
        finally:
            builtins.__import__ = original_import
            if original_module is not None:
                sys.modules[module_name] = original_module
            else:
                sys.modules.pop(module_name, None)

    def test_model_config_defaults_to_local_backend(self):
        cfg = ModelConfig(name="local-model")
        self.assertEqual(cfg.backend, "local_hf")
        self.assertIsNone(cfg.api_base_url)
        self.assertIsNone(cfg.api_key_env)

    def test_model_module_import_does_not_require_heavy_local_dependencies(self):
        module = self.import_model_module_with_blocked_heavy_deps()
        self.assertTrue(hasattr(module, "build_model_engine"))

    def test_unknown_backend_raises(self):
        model_module = self.get_model_module()
        cfg = ModelConfig(name="model", backend="unknown")
        with self.assertRaises(ValueError):
            model_module.build_model_engine(cfg)

    def test_openai_backend_missing_module_raises_generic_message(self):
        model_module = self.get_model_module()
        original_import = builtins.__import__
        module_name = "src.auto_asset_annotator.core.api_model"
        original_api_module = sys.modules.pop(module_name, None)

        def blocked_import(name, *args, **kwargs):
            if name.endswith("api_model"):
                raise ModuleNotFoundError(name=name)
            return original_import(name, *args, **kwargs)

        try:
            builtins.__import__ = blocked_import
            with self.assertRaisesRegex(
                ValueError, "openai_compatible backend is not available"
            ) as exc_info:
                model_module.build_model_engine(
                    ModelConfig(
                        name="remote-model",
                        backend="openai_compatible",
                        api_base_url="http://example.com",
                        api_key_env="TEST_API_KEY",
                    )
                )
        finally:
            builtins.__import__ = original_import
            if original_api_module is not None:
                sys.modules[module_name] = original_api_module
            else:
                sys.modules.pop(module_name, None)

        self.assertNotIn("Task 2", str(exc_info.exception))
        self.assertNotIn("src.auto_asset_annotator", str(exc_info.exception))


class TestFactorySelection(unittest.TestCase):
    def test_local_backend_factory_returns_real_local_engine_instance(self):
        model_module = importlib.import_module("src.auto_asset_annotator.core.model")

        fake_torch = types.SimpleNamespace(bfloat16="fake-bfloat16")

        class FakeLoadedModel:
            device = "cpu"

            def generate(self, **kwargs):
                return []

        class FakeAutoModel:
            @classmethod
            def from_pretrained(cls, *args, **kwargs):
                return FakeLoadedModel()

        class FakeAutoProcessor:
            @classmethod
            def from_pretrained(cls, *args, **kwargs):
                return object()

        fake_transformers = types.SimpleNamespace(
            AutoModel=FakeAutoModel,
            AutoProcessor=FakeAutoProcessor,
        )

        original_torch = sys.modules.get("torch")
        original_transformers = sys.modules.get("transformers")
        sys.modules["torch"] = fake_torch
        sys.modules["transformers"] = fake_transformers
        try:
            engine = model_module.build_model_engine(
                ModelConfig(name="local-model", backend="local_hf")
            )
        finally:
            if original_torch is not None:
                sys.modules["torch"] = original_torch
            else:
                sys.modules.pop("torch", None)
            if original_transformers is not None:
                sys.modules["transformers"] = original_transformers
            else:
                sys.modules.pop("transformers", None)

        self.assertIsInstance(engine, model_module.LocalHFEngine)

    def test_local_backend_factory_returns_local_engine(self):
        model_module = importlib.import_module("src.auto_asset_annotator.core.model")

        with mock.patch(
            "src.auto_asset_annotator.core.model.LocalHFEngine"
        ) as engine_cls:
            engine = object()
            engine_cls.return_value = engine

            cfg = ModelConfig(name="local-model", backend="local_hf")

            self.assertIs(model_module.build_model_engine(cfg), engine)
            engine_cls.assert_called_once_with(cfg)

    def test_local_engine_prefers_causal_lm_fallback_before_automodel(self):
        model_module = importlib.import_module("src.auto_asset_annotator.core.model")

        fake_torch = types.SimpleNamespace(bfloat16="fake-bfloat16")

        class FakeLoadedModel:
            device = "cpu"

            def generate(self, **kwargs):
                return []

            def generate(self, **kwargs):
                return []

            def generate(self, **kwargs):
                return []

        class FakeAutoModelForCausalLM:
            called_with = None

            @classmethod
            def from_pretrained(cls, *args, **kwargs):
                cls.called_with = (args, kwargs)
                return FakeLoadedModel()

        class FakeAutoModel:
            called = False

            @classmethod
            def from_pretrained(cls, *args, **kwargs):
                cls.called = True
                return FakeLoadedModel()

        class FakeAutoProcessor:
            @classmethod
            def from_pretrained(cls, *args, **kwargs):
                return object()

        fake_transformers = types.SimpleNamespace(
            AutoModel=FakeAutoModel,
            AutoModelForCausalLM=FakeAutoModelForCausalLM,
            AutoProcessor=FakeAutoProcessor,
        )

        original_torch = sys.modules.get("torch")
        original_transformers = sys.modules.get("transformers")
        sys.modules["torch"] = fake_torch
        sys.modules["transformers"] = fake_transformers
        try:
            model_module.LocalHFEngine(ModelConfig(name="generic-model"))
        finally:
            if original_torch is not None:
                sys.modules["torch"] = original_torch
            else:
                sys.modules.pop("torch", None)
            if original_transformers is not None:
                sys.modules["transformers"] = original_transformers
            else:
                sys.modules.pop("transformers", None)

        self.assertIsNotNone(FakeAutoModelForCausalLM.called_with)
        self.assertFalse(FakeAutoModel.called)

    def test_local_engine_rejects_broad_fallback_without_generate(self):
        model_module = importlib.import_module("src.auto_asset_annotator.core.model")

        fake_torch = types.SimpleNamespace(bfloat16="fake-bfloat16")

        class FakeLoadedModel:
            device = "cpu"

        class FakeAutoModel:
            @classmethod
            def from_pretrained(cls, *args, **kwargs):
                return FakeLoadedModel()

        class FakeAutoProcessor:
            @classmethod
            def from_pretrained(cls, *args, **kwargs):
                return object()

        fake_transformers = types.SimpleNamespace(
            AutoModel=FakeAutoModel,
            AutoProcessor=FakeAutoProcessor,
        )

        original_torch = sys.modules.get("torch")
        original_transformers = sys.modules.get("transformers")
        sys.modules["torch"] = fake_torch
        sys.modules["transformers"] = fake_transformers
        try:
            with self.assertRaisesRegex(RuntimeError, "does not support generation"):
                model_module.LocalHFEngine(ModelConfig(name="generic-model"))
        finally:
            if original_torch is not None:
                sys.modules["torch"] = original_torch
            else:
                sys.modules.pop("torch", None)
            if original_transformers is not None:
                sys.modules["transformers"] = original_transformers
            else:
                sys.modules.pop("transformers", None)


class TestMainRuntimeWiring(unittest.TestCase):
    def import_main_module_with_blocked_runtime_deps(self):
        module_name = "src.auto_asset_annotator.main"
        original_import = builtins.__import__

        def blocked_import(name, *args, **kwargs):
            if name in {
                "natsort",
                "src.auto_asset_annotator.core.pipeline",
                "src.auto_asset_annotator.utils.file",
            }:
                raise ImportError(f"blocked import: {name}")
            return original_import(name, *args, **kwargs)

        original_module = sys.modules.pop(module_name, None)
        try:
            builtins.__import__ = blocked_import
            return importlib.import_module(module_name)
        finally:
            builtins.__import__ = original_import
            if original_module is not None:
                sys.modules[module_name] = original_module
            else:
                sys.modules.pop(module_name, None)

    def test_main_module_import_is_lightweight_before_runtime_mocks(self):
        module = self.import_main_module_with_blocked_runtime_deps()
        self.assertTrue(hasattr(module, "main"))

    def test_main_uses_factory_with_cli_backend_overrides(self):
        from src.auto_asset_annotator.config.settings import (
            Config,
            DataConfig,
            ProcessingConfig,
            PromptConfig,
        )
        from src.auto_asset_annotator.main import main

        cfg = Config(
            model=ModelConfig(name="local-model"),
            data=DataConfig(
                input_dir="/tmp/input",
                output_dir="/tmp/output",
                views={"front": ["front.png"]},
            ),
            processing=ProcessingConfig(),
            prompts=PromptConfig(),
        )
        build_engine = mock.Mock()
        pipeline_cls = mock.Mock()
        list_assets = mock.Mock(return_value=[])

        with (
            mock.patch(
                "src.auto_asset_annotator.main._load_runtime_dependencies",
                return_value=(build_engine, pipeline_cls, list_assets),
            ),
            mock.patch(
                "src.auto_asset_annotator.main.tqdm",
                side_effect=lambda items, **_: items,
            ),
            mock.patch("src.auto_asset_annotator.main.os.makedirs"),
            mock.patch("src.auto_asset_annotator.config.load_config", return_value=cfg),
            mock.patch(
                "sys.argv",
                [
                    "annotator",
                    "--model_path",
                    "override-model",
                    "--model_backend",
                    "openai_compatible",
                    "--api_base_url",
                    "http://example.com",
                    "--api_key_env",
                    "TEST_API_KEY",
                ],
            ),
        ):
            self.assertEqual(main(), 0)

        self.assertEqual(cfg.model.name, "override-model")
        self.assertEqual(cfg.model.backend, "openai_compatible")
        self.assertEqual(cfg.model.api_base_url, "http://example.com")
        self.assertEqual(cfg.model.api_key_env, "TEST_API_KEY")
        build_engine.assert_called_once_with(cfg.model)
        pipeline_cls.assert_called_once()
        list_assets.assert_called_once_with("/tmp/input")

    def test_main_returns_nonzero_on_config_load_failure(self):
        from src.auto_asset_annotator.main import main

        with (
            mock.patch(
                "src.auto_asset_annotator.config.load_config",
                side_effect=FileNotFoundError,
            ),
            mock.patch("sys.argv", ["annotator"]),
        ):
            self.assertEqual(main(), 1)

    def test_main_returns_nonzero_on_engine_initialization_failure(self):
        from src.auto_asset_annotator.config.settings import (
            Config,
            DataConfig,
            ProcessingConfig,
            PromptConfig,
        )
        from src.auto_asset_annotator.main import main

        cfg = Config(
            model=ModelConfig(name="local-model"),
            data=DataConfig(
                input_dir="/tmp/input",
                output_dir="/tmp/output",
                views={"front": ["front.png"]},
            ),
            processing=ProcessingConfig(),
            prompts=PromptConfig(),
        )

        with (
            mock.patch(
                "src.auto_asset_annotator.main._load_runtime_dependencies",
                side_effect=RuntimeError("boom"),
            ),
            mock.patch("src.auto_asset_annotator.config.load_config", return_value=cfg),
            mock.patch("sys.argv", ["annotator"]),
        ):
            self.assertEqual(main(), 1)

    def test_local_engine_falls_back_to_automodel_when_qwen25_class_is_unavailable(
        self,
    ):
        model_module = importlib.import_module("src.auto_asset_annotator.core.model")

        fake_torch = types.SimpleNamespace(bfloat16="fake-bfloat16")

        class FakeLoadedModel:
            device = "cpu"

            def generate(self, **kwargs):
                return []

        class FakeAutoModel:
            called_with = None

            @classmethod
            def from_pretrained(cls, *args, **kwargs):
                cls.called_with = (args, kwargs)
                return FakeLoadedModel()

        class FakeAutoProcessor:
            @classmethod
            def from_pretrained(cls, *args, **kwargs):
                return object()

        fake_transformers = types.SimpleNamespace(
            AutoModel=FakeAutoModel,
            AutoProcessor=FakeAutoProcessor,
        )

        original_torch = sys.modules.get("torch")
        original_transformers = sys.modules.get("transformers")
        sys.modules["torch"] = fake_torch
        sys.modules["transformers"] = fake_transformers
        try:
            model_module.LocalHFEngine(ModelConfig(name="generic-model"))
        finally:
            if original_torch is not None:
                sys.modules["torch"] = original_torch
            else:
                sys.modules.pop("torch", None)
            if original_transformers is not None:
                sys.modules["transformers"] = original_transformers
            else:
                sys.modules.pop("transformers", None)

        self.assertIsNotNone(FakeAutoModel.called_with)
        _, kwargs = FakeAutoModel.called_with
        self.assertEqual(kwargs["trust_remote_code"], True)


class TestOpenAICompatibleAPIEngine(unittest.TestCase):
    def make_engine(self, **kwargs):
        from src.auto_asset_annotator.core.api_model import OpenAICompatibleAPIEngine

        cfg = ModelConfig(
            name="gemini-2.5-flash-image",
            backend="openai_compatible",
            api_base_url="http://example.com",
            api_key_env="TEST_API_KEY",
            **kwargs,
        )
        with mock.patch.dict(os.environ, {"TEST_API_KEY": "secret"}):
            return OpenAICompatibleAPIEngine(cfg)

    def make_png(self, color):
        img = Image.new("RGB", (8, 8), color)
        fd, path = tempfile.mkstemp(suffix=".png")
        os.close(fd)
        img.save(path, format="PNG")
        self.addCleanup(lambda: os.path.exists(path) and os.remove(path))
        return path

    def test_missing_api_key_env_raises(self):
        cfg = ModelConfig(
            name="gemini-2.5-flash-image",
            backend="openai_compatible",
            api_base_url="http://example.com",
            api_key_env="MISSING_KEY",
        )
        with self.assertRaisesRegex(
            ValueError, "Environment variable MISSING_KEY is not set"
        ):
            from src.auto_asset_annotator.core.api_model import (
                OpenAICompatibleAPIEngine,
            )

            OpenAICompatibleAPIEngine(cfg)

    def test_message_conversion_turns_local_path_into_data_url(self):
        path = self.make_png((255, 0, 0))
        engine = self.make_engine()
        payload = engine._build_payload(
            [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Describe it."},
                        {"type": "image_url", "image": path},
                    ],
                }
            ]
        )
        item = payload["messages"][0]["content"][1]
        self.assertEqual(item["type"], "image_url")
        self.assertTrue(item["image_url"]["url"].startswith("data:image/png;base64,"))

    def test_response_extraction_reads_chat_completion_text(self):
        engine = self.make_engine()
        text = engine._extract_text(
            {"choices": [{"message": {"content": "Category: cup"}}]}
        )
        self.assertEqual(text, "Category: cup")

    def test_response_extraction_raises_clear_error_for_malformed_response(self):
        engine = self.make_engine()

        with self.assertRaisesRegex(RuntimeError, "Malformed chat completion response"):
            engine._extract_text({"choices": [{}], "debug": "x" * 500})

    def test_inference_retries_url_errors_up_to_configured_limit(self):
        engine = self.make_engine(api_max_retries=2)
        attempts = []

        class FakeResponse:
            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

            def read(self):
                return b'{"choices": [{"message": {"content": "Category: cup"}}]}'

        def fake_urlopen(_req, timeout):
            attempts.append(timeout)
            if len(attempts) < 3:
                raise error.URLError("temporary")
            return FakeResponse()

        with mock.patch(
            "src.auto_asset_annotator.core.api_model.request.urlopen",
            side_effect=fake_urlopen,
        ):
            text = engine.inference(
                [{"role": "user", "content": [{"type": "text", "text": "Hi"}]}]
            )

        self.assertEqual(text, "Category: cup")
        self.assertEqual(len(attempts), 3)

    def test_inference_does_not_retry_non_transient_http_errors(self):
        engine = self.make_engine(api_max_retries=5)
        attempts = []

        def fake_urlopen(_req, timeout):
            attempts.append(timeout)
            raise error.HTTPError(
                url="http://example.com/v1/chat/completions",
                code=400,
                msg="Bad Request",
                hdrs=None,
                fp=io.BytesIO(b'{"error":"bad request"}'),
            )

        with mock.patch(
            "src.auto_asset_annotator.core.api_model.request.urlopen",
            side_effect=fake_urlopen,
        ):
            with self.assertRaisesRegex(RuntimeError, "HTTP 400"):
                engine.inference(
                    [{"role": "user", "content": [{"type": "text", "text": "Hi"}]}]
                )

        self.assertEqual(len(attempts), 1)


if __name__ == "__main__":
    unittest.main()
