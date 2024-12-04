import os
import json
from ..lib.model_downloader import ModelDownloader
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
                "base_model": (["SD1.5", "SDXL", "Flux.1", "Kolors", "Pony"], {"default": "Flux.1"})
            },
            "optional": {
                "version_id": ("STRING", {
                    "default": "", 
                    "multiline": False,
                    "placeholder": "仅在civitai下载时生效，留空则下载最新版本"
                }),
                "file_names": ("STRING", {
                    "default": "", 
                    "multiline": True, 
                    "placeholder": "仅在huggingface下载时生效，支持多个文件，每行一个，空下载所有文件"
                })
            }
        }

    RETURN_TYPES = (ANY,)
    FUNCTION = "download_and_get_filename"
    CATEGORY = "Model (Down)load"
    OUTPUT_NODE = True

    @classmethod
    def download_and_get_filename(cls, source, model_id, base_model, version_id=None, file_names=None, progress_callback=None):
        downloader = ModelDownloader(progress_callback=progress_callback)
        file_names_list = file_names.splitlines() if file_names and source == "huggingface" else None
        main_model_path, model_details = downloader.ensure_downloaded(cls.MODEL_TYPE, model_id, source, base_model, version_id, file_names_list)

        # 格式化模型详情为中文字符串
        formatted_details = f"模型名称: {model_details['name']}\n"
        
        if model_details['version']:
            formatted_details += f"版本: {model_details['version']}\n"
        
        if model_details['trigger_words']:
            trigger_words_str = ', '.join(model_details['trigger_words']) if model_details['trigger_words'] else '无'
            formatted_details += f"触发词: {trigger_words_str}\n"
        else:
            formatted_details += "触发词: 无\n"
            
        if model_details['url']:
            formatted_details += f"模型地址: {model_details['url']}"
        
        logging.info(model_details)

        return {"ui": {"model_details": (formatted_details,)}, "result": (main_model_path,)}

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

class DownloadControlNet(BaseModelDownloader):
    MODEL_TYPE = "controlnet"
    RETURN_NAMES = ("controlnet_name",)
