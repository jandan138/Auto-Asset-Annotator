import json
import os
import tempfile
from typing import Any, Dict, List

from ..config.settings import ModelConfig


class LocalGemma4MultimodalEngine:
    def __init__(self, config: ModelConfig):
        self.config = config
        self._prepare_unsloth_runtime()

        try:
            import torch
            import transformers
        except ImportError as exc:
            raise ValueError(
                "local_gemma4_multimodal backend requires torch and transformers "
                f"with Gemma4 multimodal support; installed transformers={self._transformers_version()}"
            ) from exc

        AutoProcessor = getattr(transformers, "AutoProcessor", None)
        if AutoProcessor is None:
            raise ValueError(
                "local_gemma4_multimodal backend requires transformers>=5.5.0 "
                f"with AutoProcessor; installed transformers={self._transformers_version(transformers)}"
            )

        model_class = self._resolve_model_class()
        try:
            torch_dtype = getattr(torch, config.dtype)
        except AttributeError as exc:
            raise ValueError(f"Unsupported torch dtype for Gemma4: {config.dtype}") from exc

        print(f"[INFO] Loading Gemma4 multimodal model: {config.name}")
        self.model = model_class.from_pretrained(
            config.name,
            torch_dtype=torch_dtype,
            attn_implementation=config.attn_implementation,
            device_map=config.device_map,
            trust_remote_code=True,
        )
        self.processor = AutoProcessor.from_pretrained(
            config.name, trust_remote_code=True
        )
        print(f"[INFO] Using Gemma4 model class: {model_class.__name__}")
        print("[INFO] Gemma4 multimodal model loaded successfully.")

    def _prepare_unsloth_runtime(self) -> None:
        if not self._requires_unsloth_runtime():
            return

        os.environ.setdefault(
            "UNSLOTH_COMPILE_LOCATION",
            self._default_unsloth_compile_location(),
        )

        try:
            import unsloth  # noqa: F401
        except ImportError as exc:
            raise ValueError(
                "local_gemma4_multimodal backend requires unsloth for "
                "Unsloth Gemma4 4-bit checkpoints. Use the Genesis-LLM QLoRA "
                "runtime or install unsloth in the active Python environment."
            ) from exc

    def _requires_unsloth_runtime(self) -> bool:
        model_name = str(self.config.name)
        if "unsloth" in model_name.lower():
            return True

        config_path = os.path.join(os.path.realpath(model_name), "config.json")
        try:
            with open(config_path, "r", encoding="utf-8") as handle:
                model_config = json.load(handle)
        except (OSError, json.JSONDecodeError, TypeError):
            return False

        if model_config.get("unsloth_fixed") is True:
            return True

        quantization_config = model_config.get("quantization_config", {})
        if not isinstance(quantization_config, dict):
            return False

        quant_method = str(quantization_config.get("quant_method", "")).lower()
        load_in_4bit = bool(
            quantization_config.get("load_in_4bit")
            or quantization_config.get("_load_in_4bit")
        )
        return quant_method == "bitsandbytes" and load_in_4bit

    def _default_unsloth_compile_location(self) -> str:
        leaf_name = "auto_asset_annotator_unsloth_compiled_cache"
        for root in (tempfile.gettempdir(), "/tmp", "/var/tmp"):
            candidate = os.path.realpath(os.path.join(root, leaf_name))
            if not self._is_path_under_working_tree(candidate):
                return candidate
        return os.path.realpath(os.path.join("/tmp", leaf_name))

    def _is_path_under_working_tree(self, path: str) -> bool:
        working_tree = os.path.realpath(os.getcwd())
        try:
            return (
                os.path.commonpath([working_tree, os.path.realpath(path)])
                == working_tree
            )
        except ValueError:
            return False

    def _resolve_model_class(self):
        import transformers

        for class_name in (
            "AutoModelForImageTextToText",
            "Gemma4ForConditionalGeneration",
        ):
            model_class = getattr(transformers, class_name, None)
            if model_class is not None:
                return model_class

        raise ValueError(
            "local_gemma4_multimodal backend requires transformers>=5.5.0 "
            "with AutoModelForImageTextToText or Gemma4ForConditionalGeneration; "
            f"installed transformers={self._transformers_version(transformers)}"
        )

    def _transformers_version(self, transformers_module=None) -> str:
        if transformers_module is not None:
            return getattr(transformers_module, "__version__", "unknown")

        try:
            import transformers
        except ImportError:
            return "not installed"
        return getattr(transformers, "__version__", "unknown")

    def _convert_messages_for_gemma4(
        self, inputs_messages: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        converted_messages = []
        for message in inputs_messages:
            converted_content = []
            for item in message.get("content", []):
                item_type = item.get("type")
                if item_type == "text":
                    converted_content.append({"type": "text", "text": item["text"]})
                    continue

                if item_type != "image_url":
                    continue

                source = item.get("image")
                if source is None:
                    source = item.get("image_url", {}).get("url")
                if not source:
                    raise ValueError(
                        "image_url content item is missing an image source"
                    )

                converted_content.append({"type": "image", "image": source})

            converted_messages.append(
                {"role": message["role"], "content": converted_content}
            )

        return converted_messages

    def inference(self, inputs_messages: List[Dict[str, Any]]) -> str:
        messages = self._convert_messages_for_gemma4(inputs_messages)
        inputs = self.processor.apply_chat_template(
            messages,
            tokenize=True,
            return_dict=True,
            return_tensors="pt",
            add_generation_prompt=True,
        )

        target_device = getattr(self.model, "device", None)
        if target_device is not None and hasattr(inputs, "to"):
            inputs = inputs.to(target_device)

        generated_ids = self.model.generate(
            **inputs,
            max_new_tokens=self.config.max_new_tokens,
            temperature=self.config.temperature,
            do_sample=self.config.temperature != 0.0,
        )

        input_ids = inputs["input_ids"]
        generated_ids_trimmed = [
            out_ids[len(in_ids) :]
            for in_ids, out_ids in zip(input_ids, generated_ids)
        ]

        output_text = self.processor.batch_decode(
            generated_ids_trimmed,
            skip_special_tokens=True,
            clean_up_tokenization_spaces=False,
        )
        return output_text[0]
