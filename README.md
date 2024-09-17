# ComfyUI Model Downloader (ComfyUI 模型下载器)

这是一个用于ComfyUI的模型下载器插件。

## 功能

- 下载Checkpoint模型
- 下载LoRA模型
- 下载VAE模型
- 下载UNET模型

## 安装

1. 克隆此仓库到ComfyUI的`custom_nodes`目录:

   ```bash
   git clone https://github.com/您的用户名/comfyui_model_downloader.git
   ```

2. 安装依赖:

   ```bash
   pip install -r requirements.txt
   ```

## 使用方法

在ComfyUI中,您可以使用以下节点:

- DownloadCheckpoint
- DownloadLora
- DownloadVAE
- DownloadUNET

每个节点都需要`model_id`和`source`作为输入。如果模型在本地存在,将直接加载;否则,将从指定的源下载。

## 许可证

MIT