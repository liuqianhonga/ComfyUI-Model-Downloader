import os
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from tqdm import tqdm
from huggingface_hub import hf_hub_download, HfApi, hf_hub_url
import logging
import re

# 设置日志记录
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Hack: string type that is always equal in not equal comparisons
class AnyType(str):
    def __ne__(self, __value: object) -> bool:
        return False

# Our any instance wants to be a wildcard string
ANY = AnyType("*")

class CivitaiAPI:
    def __init__(self):
        self.base_url = "https://civitai.com/api/v1"

    def get_model(self, model_id):
        response = requests.get(f"{self.base_url}/models/{model_id}")
        response.raise_for_status()
        return response.json()

class ModelDownloader:
    def __init__(self, progress_callback=None):
        self.civitai = CivitaiAPI()
        self.model_types = {
            "checkpoint": os.path.join("models", "checkpoints"),
            "lora": os.path.join("models", "loras"),
            "vae": os.path.join("models", "vae"),
            "unet": os.path.join("models", "unet")
        }
        self.base_model_types = ["SD1.5", "SDXL", "Flux.1"]
        self.name = "ComfyUI Model Manager"
        self.name_zh = "ComfyUI 模型下载器"
        self.hf_api = HfApi()
        self.session = self.create_session()
        self.progress_callback = progress_callback

    def create_session(self):
        session = requests.Session()
        retries = Retry(total=5, backoff_factor=1, status_forcelist=[502, 503, 504])
        session.mount('https://', HTTPAdapter(max_retries=retries))
        return session
    
    def sanitize_repo_id(self, repo_id):
        # 移除不允许的字符，并确保仓库 ID 符合 Hugging Face 的命名规则
        repo_id = re.sub(r'[^a-zA-Z0-9\-_.]', '', repo_id)
        repo_id = re.sub(r'^[\-.]+|[\-.]+$', '', repo_id)
        return repo_id[:96]

    def get_model_name(self, source, model_id):
        if source == "huggingface":
            return self.sanitize_repo_id(model_id.split('/')[-1])
        elif source == "civitai":
            model_info = self.civitai.get_model(model_id)
            return model_info.get('name', model_id)
        else:
            return model_id

    def download_from_huggingface(self, model_type, model_id, local_path, download_url, file_names=None):
        logging.info(f"从Hugging Face下载{model_type}模型: {model_id}")
        try:
            files = file_names if file_names else self.hf_api.list_repo_files(model_id)
            for file in files:
                file_url = hf_hub_url(model_id, filename=file)
                file_local_path = os.path.join(local_path, file)
                os.makedirs(os.path.dirname(file_local_path), exist_ok=True)
                
                response = self.session.get(file_url, stream=True)
                response.raise_for_status()
                total_size = int(response.headers.get('content-length', 0))
                
                with open(file_local_path, 'wb') as f, tqdm(
                    desc=f"下载 {file}",
                    total=total_size,
                    unit='iB',
                    unit_scale=True,
                    unit_divisor=1024,
                ) as progress_bar:
                    for data in response.iter_content(chunk_size=8192):
                        size = f.write(data)
                        progress_bar.update(size)
                        if self.progress_callback:
                            self.progress_callback(progress_bar.n / total_size * 100)
                
                logging.info(f"下载完成: {file_local_path}")
        except Exception as e:
            logging.error(f"从Hugging Face下载模型时出错: {e}")
            raise
        return local_path
    
    def download_from_civitai(self, model_type, model_id, local_path, download_url):
        logging.info(f"从Civitai下载{model_type}模型: {model_id}")
        try:
            response = self.session.get(download_url, stream=True, verify=False)  # 忽略 SSL 验证
            if response.status_code == 401:
                error_message = (
                    f"下载 Civitai 模型 {model_id} 时遇到 401 Unauthorized 错误。\n"
                    "可能的原因：\n"
                    "1. 该模型可能需要登录才能下载。\n"
                    "2. 您可能需要在 Civitai 上购买或获得该模型的访问权限。\n"
                    "3. Civitai 的 API 可能发生了变化。\n"
                    "建议解决方法：\n"
                    "1. 请尝试手动从 Civitai 网站下载模型，然后将其放置在正确的目录中。\n"
                    "2. 检查 Civitai 的 API 文档，看是否需要提供额外的认证信息。"
                )
                logging.error(error_message)
                raise ValueError(error_message)
            
            response.raise_for_status()
            total_size = int(response.headers.get('content-length', 0))
            
            with open(local_path, 'wb') as file, tqdm(
                desc=f"下载 {model_id}",
                total=total_size,
                unit='iB',
                unit_scale=True,
                unit_divisor=1024,
            ) as progress_bar:
                for data in response.iter_content(chunk_size=8192):
                    size = file.write(data)
                    progress_bar.update(size)
                    if self.progress_callback:
                        self.progress_callback(progress_bar.n / total_size * 100)
            
            if os.path.getsize(local_path) == 0:
                raise ValueError(f"下载完成，但文件大小为0: {local_path}")
            
            logging.info(f"下载完成: {local_path}")
        except requests.exceptions.HTTPError as e:
            error_message = f"从Civitai下载模型时遇到HTTP错误: {e}\n"
            if e.response.status_code == 401:
                error_message += (
                    "401 Unauthorized 错误可能意味着：\n"
                    "1. 该模型需要登录才能下载。\n"
                    "2. 您可能需要在 Civitai 上购买或获得该模型的访问权限。\n"
                    "请尝试手动从 Civitai 网站下载模型，然后将其放置在正确的目录中。"
                )
            elif e.response.status_code == 404:
                error_message += "404 Not Found 错误可能意味着模型不存在或已被删除。请检查模型 ID 是否正确。"
            logging.error(error_message)
            if os.path.exists(local_path):
                os.remove(local_path)
            raise ValueError(error_message)
        except Exception as e:
            logging.error(f"从Civitai下载模型时出错: {e}")
            if os.path.exists(local_path):
                os.remove(local_path)
            raise
        return local_path

    def get_download_url(self, source, model_id, model_info):
        if source == "huggingface":
            try:
                files = self.hf_api.list_repo_files(model_id)
                model_file = next((f for f in files if f.endswith(('.safetensors', '.ckpt', '.pt', '.bin'))), None)
                if model_file:
                    return hf_hub_url(model_id, filename=model_file)
                else:
                    raise ValueError(f"在仓库 {model_id} 中未找到合适的模型文件")
            except Exception as e:
                logging.error(f"从Hugging Face获取下载链接时出错: {e}")
                raise ValueError(f"从Hugging Face获取下载链接时出错: {e}")
        elif source == "civitai":
            try:
                if isinstance(model_info, str):
                    model_info = self.civitai.get_model(model_id)
                
                if 'modelVersions' in model_info and model_info['modelVersions']:
                    latest_version = model_info['modelVersions'][0]
                    files = latest_version.get('files', [])
                    if files:
                        download_url = files[0].get('downloadUrl')
                        if download_url:
                            logging.info(f"成功获取Civitai模型 {model_id} 的下载链接")
                            return download_url
                
                logging.error(f"无法从Civitai模型信息中获取下载链接: {model_info}")
                raise ValueError(f"无法从Civitai模型信息中获取下载链接")
            except Exception as e:
                logging.error(f"处理Civitai模型 {model_id} 信息时出错: {e}")
                raise ValueError(f"处理Civitai模型 {model_id} 信息时出错: {e}")
        
        logging.error(f"无法获取模型 {model_id} 的下载链接")
        raise ValueError(f"无法获取模型 {model_id} 的下载链接")

    def get_model_info(self, source, model_id):
        if source == "huggingface":
            return f"Hugging Face模型: {model_id}"
        elif source == "civitai":
            try:
                model_info = self.civitai.get_model(model_id)
                logging.info(f"成功获取Civitai模型 {model_id} 的信息")
                return model_info
            except Exception as e:
                logging.error(f"获取Civitai模型 {model_id} 信息时出错: {e}")
                raise ValueError(f"获取Civitai模型 {model_id} 信息时出错: {e}")
        else:
            return f"未知来源模型: {model_id}"

    def get_file_extension(self, source, model_info, download_url):
        if source == "huggingface":
            try:
                files = self.hf_api.list_repo_files(model_info)
                model_file = next((f for f in files if f.endswith(('.safetensors', '.ckpt', '.pt', '.bin'))), None)
                if model_file:
                    return os.path.splitext(model_file)[-1]
            except Exception as e:
                logging.error(f"从Hugging Face获取文件信息时出错: {e}")
        elif source == "civitai":
            if 'modelVersions' in model_info and model_info['modelVersions']:
                files = model_info['modelVersions'][0].get('files', [])
                if files:
                    return os.path.splitext(files[0].get('name', ''))[-1]
        return '.safetensors'

    def sanitize_filename(self, filename):
        return re.sub(r'[\\/*?:"<>|]', "_", filename)

    def get_model_details(self, source, model_id, model_info):
        if source == "huggingface":
            model_name = self.get_model_name(source, model_id)
            return f"模型名称: {model_name}\n触发词: 未知\n模型地址: https://huggingface.co/{model_id}\n本地存储路径: {model_info.get('local_path', '未知')}"
        elif source == "civitai":
            model_name = model_info.get('name', 'Unknown')
            trigger_words = []
            
            if 'modelVersions' in model_info and model_info['modelVersions']:
                # 尝试找到当前版本
                current_version = next((v for v in model_info['modelVersions'] if v.get('id') == model_info.get('currentVersionId')), None)
                
                # 如果找不到当前版本，就使用第一个版本
                version_to_use = current_version or model_info['modelVersions'][0]
                
                # 获取触发词
                trigger_words = version_to_use.get('trainedWords', [])
            
            trigger_words_str = ', '.join(trigger_words) if trigger_words else '未知'
            return f"模型名称: {model_name}\n触发词: {trigger_words_str}\n模型地址: https://civitai.com/models/{model_id}\n本地存储路径: {model_info.get('local_path', '未知')}"
        else:
            return "无法获取模型详细信息"

    def download_preview_image(self, image_url, local_path):
        try:
            response = self.session.get(image_url, stream=True, verify=False)  # 忽略 SSL 验证
            response.raise_for_status()
            with open(local_path, 'wb') as file:
                for chunk in response.iter_content(chunk_size=8192):
                    file.write(chunk)
            logging.info(f"预览图片下载完成: {local_path}")
        except Exception as e:
            logging.error(f"下载预览图片时出错: {e}")

    def ensure_downloaded(self, model_type, model_id, source, base_model, file_names=None):
        model_info = self.get_model_info(source, model_id)
        model_name = self.get_model_name(source, model_id)
        download_url = self.get_download_url(source, model_id, model_info)
        file_extension = self.get_file_extension(source, model_info, download_url)
        
        # 使用新的命名规则：[模型id]+模型名称，包含完整的文件后缀名
        filename = self.sanitize_filename(f"[{model_id}]{model_name}{file_extension}")
        local_path = os.path.join(self.model_types[model_type], base_model, filename)
        
        model_exists = os.path.exists(local_path) and os.path.getsize(local_path) > 0
        
        if not model_exists:
            logging.info(f"模型文件不存在或为空，开始下载: {local_path}")
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            if source == "huggingface":
                self.download_from_huggingface(model_type, model_id, local_path, download_url, file_names)
            elif source == "civitai":
                self.download_from_civitai(model_type, model_id, local_path, download_url)
            
            if not os.path.exists(local_path) or os.path.getsize(local_path) == 0:
                raise ValueError(f"下载失败或文件大小为0: {local_path}")
        else:
            logging.info(f"模型文件已存在: {local_path}")
        
        # 下载预览图片（无论模型是否已存在）
        preview_image_path = None
        if source == "civitai" and 'modelVersions' in model_info and model_info['modelVersions']:
            first_version = model_info['modelVersions'][0]
            if 'images' in first_version and first_version['images']:
                first_image = first_version['images'][0]
                image_url = first_image.get('url')
                if image_url:
                    # 从URL中获取图片的原始扩展名
                    image_extension = os.path.splitext(image_url.split('?')[0])[1]
                    # 使用与模型相同的命名规则，但保留预览图的原始扩展名
                    image_filename = self.sanitize_filename(f"[{model_id}]{model_name}{image_extension}")
                    preview_image_path = os.path.join(self.model_types[model_type], base_model, image_filename)
                    
                    if not os.path.exists(preview_image_path):
                        logging.info(f"预览图片不存在，开始下载: {preview_image_path}")
                        self.download_preview_image(image_url, preview_image_path)
                    else:
                        logging.info(f"预览图片已存在: {preview_image_path}")
        
        # 增加本地存储路径字段到 model_info
        model_info['local_path'] = local_path
        model_details = self.get_model_details(source, model_id, model_info)
        return local_path, model_details

# ComfyUI节点定义
class BaseModelDownloader:
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {
            "source": (["huggingface", "civitai"], {"default": "civitai"}),
            "model_id": ("STRING", {"default": "", "multiline": False}),
            "base_model": (["SD1.5", "SDXL", "Flux.1"], {"default": "Flux.1"}),
            "file_names": ("STRING", {"default": "", "multiline": True, "optional": True}) if cls.MODEL_TYPE == "huggingface" else None
        }}
    
    RETURN_TYPES = (ANY, "STRING")
    FUNCTION = "download_and_get_filename"
    CATEGORY = "模型下载"

    @classmethod
    def download_and_get_filename(cls, source, model_id, base_model, file_names=None, progress_callback=None):
        downloader = ModelDownloader(progress_callback=progress_callback)
        file_names_list = file_names.splitlines() if file_names else None
        full_path, model_details = downloader.ensure_downloaded(cls.MODEL_TYPE, model_id, source, base_model, file_names_list)
        filename = os.path.basename(full_path)
        result = os.path.join(base_model, filename)
        
        return (result, model_details)

class DownloadCheckpoint(BaseModelDownloader):
    MODEL_TYPE = "checkpoint"
    RETURN_NAMES = ("ckpt_name", "model_info")

class DownloadLora(BaseModelDownloader):
    MODEL_TYPE = "lora"
    RETURN_NAMES = ("lora_name", "model_info")

class DownloadVAE(BaseModelDownloader):
    MODEL_TYPE = "vae"
    RETURN_NAMES = ("vae_name", "model_info")

class DownloadUNET(BaseModelDownloader):
    MODEL_TYPE = "unet"
    RETURN_NAMES = ("unet_name", "model_info")

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
