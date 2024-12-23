from .nodes.model_downloader import (
    DownloadCheckpoint,
    DownloadLora,
    DownloadVAE,
    DownloadUNET,
    DownloadControlNet
)

NODE_CLASS_MAPPINGS = {
    "DownloadCheckpoint": DownloadCheckpoint,
    "DownloadLora": DownloadLora,
    "DownloadVAE": DownloadVAE,
    "DownloadUNET": DownloadUNET,
    "DownloadControlNet": DownloadControlNet
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "DownloadCheckpoint": "(Down)load Checkpoint",
    "DownloadLora": "(Down)load LoRA",
    "DownloadVAE": "(Down)load VAE",
    "DownloadUNET": "(Down)load UNET",
    "DownloadControlNet": "(Down)load ControlNet"
}

WEB_DIRECTORY = "./web"

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"]
