import os
import json
from .model_downloader import ModelDownloader
import logging

# Hack: string type that is always equal in not equal comparisons
class AnyType(str):
    def __ne__(self, __value: object) -> bool:
        return False

# Our any instance wants to be a wildcard string
ANY = AnyType("*")

# ComfyUI节点定义
class BaseModelDownloader:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "source": (["civitai", "huggingface"], {"default": "civitai"}),
                "model_id": ("STRING", {"default": "", "multiline": False}),
                "base_model": (["SD1.5", "SDXL", "Flux.1"], {"default": "Flux.1"})
            },
            "optional": {
                "file_names": ("STRING", {
                    "default": "", 
                    "multiline": True, 
                    "placeholder": "仅在huggingface下载时生效，支持多个文件，每行一个，空下载所有文件"
                })
            }
        }

    RETURN_TYPES = (ANY,)
    FUNCTION = "download_and_get_filename"
    CATEGORY = "模型下载"
    OUTPUT_NODE = True

    @classmethod
    def download_and_get_filename(cls, source, model_id, base_model, file_names=None, progress_callback=None):
        downloader = ModelDownloader(progress_callback=progress_callback)
        file_names_list = file_names.splitlines() if file_names and source == "huggingface" else None
        main_model_path, model_details = downloader.ensure_downloaded(cls.MODEL_TYPE, model_id, source, base_model, file_names_list)

        logging.info(model_details)

        return {"ui": {"model_details": (model_details,)}, "result": (main_model_path,)}

class DownloadCheckpoint(BaseModelDownloader):
    MODEL_TYPE = "checkpoint"
    RETURN_NAMES = ("ckpt_name",)

class DownloadLora(BaseModelDownloader):
    MODEL_TYPE = "lora"
    RETURN_NAMES = ("lora_name",)

class DownloadVAE(BaseModelDownloader):
    MODEL_TYPE = "vae"
    RETURN_NAMES = ("vae_name",)

class DownloadUNET(BaseModelDownloader):
    MODEL_TYPE = "unet"
    RETURN_NAMES = ("unet_name",)

# 注册节点
NODE_CLASS_MAPPINGS = {
    "DownloadCheckpoint": DownloadCheckpoint,
    "DownloadLora": DownloadLora,
    "DownloadVAE": DownloadVAE,
    "DownloadUNET": DownloadUNET
}

# 定义节点显示名称
NODE_DISPLAY_NAME_MAPPINGS = {
    "DownloadCheckpoint": "下载 Checkpoint",
    "DownloadLora": "下载 LoRA",
    "DownloadVAE": "下载 VAE",
    "DownloadUNET": "下载 UNET"
}