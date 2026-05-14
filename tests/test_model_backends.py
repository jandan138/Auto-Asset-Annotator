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


def restore_module_binding(module_name, original_module):
    parent_name, attr_name = module_name.rsplit(".", 1)
    parent_module = sys.modules.get(parent_name)

    if original_module is not None:
        sys.modules[module_name] = original_module
        if parent_module is not None:
            setattr(parent_module, attr_name, original_module)
        return

    sys.modules.pop(module_name, None)
    if parent_module is not None and hasattr(parent_module, attr_name):
        delattr(parent_module, attr_name)


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
            restore_module_binding(module_name, original_module)

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
            restore_module_binding(module_name, original_api_module)

        self.assertNotIn("Task 2", str(exc_info.exception))
        self.assertNotIn("src.auto_asset_annotator", str(exc_info.exception))


class TestFactorySelection(unittest.TestCase):
    def test_gemma4_backend_factory_returns_gemma4_engine(self):
        model_module = importlib.import_module("src.auto_asset_annotator.core.model")

        class FakeGemma4Engine:
            def __init__(self, config):
                self.config = config

        fake_module_name = "src.auto_asset_annotator.core.gemma4_model"
        fake_module = types.SimpleNamespace(
            LocalGemma4MultimodalEngine=FakeGemma4Engine
        )
        original_module = sys.modules.get(fake_module_name)
        sys.modules[fake_module_name] = fake_module
        try:
            cfg = ModelConfig(name="gemma4-model", backend="local_gemma4_multimodal")
            engine = model_module.build_model_engine(cfg)
        finally:
            if original_module is not None:
                sys.modules[fake_module_name] = original_module
            else:
                sys.modules.pop(fake_module_name, None)

        self.assertIsInstance(engine, FakeGemma4Engine)
        self.assertIs(engine.config, cfg)

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
            restore_module_binding(module_name, original_module)

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


class TestGemma4MultimodalEngine(unittest.TestCase):
    def import_gemma4_module_with_fake_deps(self):
        module_name = "src.auto_asset_annotator.core.gemma4_model"
        original_module = sys.modules.pop(module_name, None)
        try:
            return importlib.import_module(module_name)
        finally:
            restore_module_binding(module_name, original_module)

    def test_convert_messages_for_gemma4_maps_image_blocks_in_place(self):
        from src.auto_asset_annotator.core.gemma4_model import (
            LocalGemma4MultimodalEngine,
        )

        engine = object.__new__(LocalGemma4MultimodalEngine)
        converted = engine._convert_messages_for_gemma4(
            [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Describe it."},
                        {"type": "image_url", "image": "/tmp/front.png"},
                        {"type": "text", "text": "Use the left view too."},
                        {
                            "type": "image_url",
                            "image_url": {"url": "/tmp/left.png"},
                        },
                    ],
                }
            ]
        )

        self.assertEqual(
            converted,
            [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Describe it."},
                        {"type": "image", "image": "/tmp/front.png"},
                        {"type": "text", "text": "Use the left view too."},
                        {"type": "image", "image": "/tmp/left.png"},
                    ],
                }
            ],
        )

    def test_missing_gemma4_transformers_classes_raise_versioned_error(self):
        fake_torch = types.SimpleNamespace(bfloat16="fake-bfloat16")
        class FakeAutoProcessor:
            @classmethod
            def from_pretrained(cls, *args, **kwargs):
                return cls()

        fake_transformers = types.SimpleNamespace(
            __version__="4.37.0",
            AutoProcessor=FakeAutoProcessor,
        )

        with mock.patch.dict(
            sys.modules,
            {"torch": fake_torch, "transformers": fake_transformers},
        ):
            gemma4_module = self.import_gemma4_module_with_fake_deps()
            with self.assertRaisesRegex(ValueError, "installed transformers=4.37.0"):
                gemma4_module.LocalGemma4MultimodalEngine(
                    ModelConfig(
                        name="gemma4-model",
                        backend="local_gemma4_multimodal",
                    )
                )

    def test_inference_uses_gemma4_processor_chat_template_and_trims_prompt(self):
        fake_torch = types.SimpleNamespace(bfloat16="fake-bfloat16")

        class FakeInputs(dict):
            def to(self, device):
                self.moved_to = device
                return self

        class FakeLoadedModel:
            device = "cuda:0"
            generate_kwargs = None

            def generate(self, **kwargs):
                type(self).generate_kwargs = kwargs
                return [[10, 11, 12, 42, 43]]

        class FakeAutoModelForImageTextToText:
            called_with = None

            @classmethod
            def from_pretrained(cls, *args, **kwargs):
                cls.called_with = (args, kwargs)
                return FakeLoadedModel()

        class FakeAutoProcessor:
            last_instance = None

            @classmethod
            def from_pretrained(cls, *args, **kwargs):
                cls.last_instance = cls()
                cls.last_instance.called_with = (args, kwargs)
                return cls.last_instance

            def apply_chat_template(self, messages, **kwargs):
                self.template_messages = messages
                self.template_kwargs = kwargs
                return FakeInputs(
                    {
                        "input_ids": [[10, 11, 12]],
                        "attention_mask": [[1, 1, 1]],
                    }
                )

            def batch_decode(self, token_ids, **kwargs):
                self.decoded_token_ids = token_ids
                self.decode_kwargs = kwargs
                return ["Category: chair"]

        fake_transformers = types.SimpleNamespace(
            AutoModelForImageTextToText=FakeAutoModelForImageTextToText,
            AutoProcessor=FakeAutoProcessor,
        )
        with mock.patch.dict(
            sys.modules,
            {"torch": fake_torch, "transformers": fake_transformers},
        ):
            gemma4_module = self.import_gemma4_module_with_fake_deps()
            engine = gemma4_module.LocalGemma4MultimodalEngine(
                ModelConfig(
                    name="gemma4-model",
                    backend="local_gemma4_multimodal",
                    temperature=0.1,
                    max_new_tokens=7,
                )
            )
            output = engine.inference(
                [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "Describe it."},
                            {"type": "image_url", "image": "/tmp/front.png"},
                        ],
                    }
                ]
            )

        self.assertEqual(output, "Category: chair")
        self.assertEqual(
            FakeAutoModelForImageTextToText.called_with[1]["torch_dtype"],
            "fake-bfloat16",
        )
        processor = FakeAutoProcessor.last_instance
        self.assertEqual(
            processor.template_messages[0]["content"][0],
            {"type": "text", "text": "Describe it."},
        )
        self.assertEqual(
            processor.template_messages[0]["content"][1],
            {"type": "image", "image": "/tmp/front.png"},
        )
        self.assertEqual(
            processor.template_kwargs,
            {
                "tokenize": True,
                "return_dict": True,
                "return_tensors": "pt",
                "add_generation_prompt": True,
            },
        )
        self.assertEqual(FakeLoadedModel.generate_kwargs["max_new_tokens"], 7)
        self.assertEqual(FakeLoadedModel.generate_kwargs["temperature"], 0.1)
        self.assertEqual(FakeLoadedModel.generate_kwargs["do_sample"], True)
        self.assertEqual(processor.decoded_token_ids, [[42, 43]])

    @unittest.skipUnless(
        os.environ.get("RUN_GEMMA4_PROCESSOR_SMOKE") == "1",
        "Set RUN_GEMMA4_PROCESSOR_SMOKE=1 to run the local Gemma4 processor smoke",
    )
    def test_gemma4_processor_smoke_includes_image_tensors(self):
        from transformers import AutoProcessor

        model_path = os.environ.get(
            "GEMMA4_MODEL_PATH",
            "/cpfs/user/zhuzihou/models/gemma4/current",
        )
        img = Image.new("RGB", (8, 8), (255, 0, 0))
        fd, path = tempfile.mkstemp(suffix=".png")
        os.close(fd)
        img.save(path, format="PNG")
        self.addCleanup(lambda: os.path.exists(path) and os.remove(path))

        processor = AutoProcessor.from_pretrained(
            model_path, trust_remote_code=True, local_files_only=True
        )
        inputs = processor.apply_chat_template(
            [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Describe this asset."},
                        {"type": "image", "image": path},
                    ],
                }
            ],
            tokenize=True,
            return_dict=True,
            return_tensors="pt",
            add_generation_prompt=True,
        )

        self.assertIn("input_ids", inputs)
        self.assertTrue(
            any("image" in key or "pixel" in key for key in inputs.keys()),
            f"Gemma4 processor inputs did not include image tensor keys: {list(inputs.keys())}",
        )


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
