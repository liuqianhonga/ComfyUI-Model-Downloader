import os
import folder_paths

class AnyType(str):
    def __ne__(self, __value: object) -> bool:
        return False

ANY = AnyType("*")

class LoadLoraByPath:
    def __init__(self):
        self.lora_path = folder_paths.models_dir + "/loras"
    
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "lora_paths": ("STRING", {
                    "default": "",
                    "multiline": False,
                    "placeholder": "Multiple paths separated by comma (,)"
                }),
            },
            "optional": {
                "filter_text": ("STRING", {
                    "default": "",
                    "multiline": False,
                    "placeholder": "Multiple filter texts separated by comma (,)"
                }),
            }
        }
    
    RETURN_TYPES = (ANY,)
    RETURN_NAMES = ("loras",)
    OUTPUT_IS_LIST = (True,)
    FUNCTION = "load_loras"
    CATEGORY = "Model (Down)load"

    def load_loras(self, lora_paths, filter_text=""):
        # 将lora_paths分割成多个路径
        paths = [p.strip() for p in lora_paths.split(',') if p.strip()]
        if not paths:
            raise ValueError("No valid path provided")
            
        # 将filter_text转换为列表，改用逗号分隔
        filters = [text.strip() for text in filter_text.split(',') if text.strip()]
        
        # 获取所有lora文件
        lora_files = []
        for path in paths:
            # 构建完整路径
            full_path = os.path.join(self.lora_path, path)
            
            # 检查目录是否存在
            if not os.path.exists(full_path):
                print(f"Warning: Path not found: {full_path}")
                continue
            
            for file in os.listdir(full_path):
                if file.endswith('.safetensors'):
                    # 如果没有指定过滤条件，或者文件名匹配任意一个过滤条件
                    if not filters or any(f.lower() in file.lower() for f in filters):
                        relative_path = os.path.join(path, file)
                        lora_files.append(relative_path)
        
        return {"ui": {"loras": [lora_files]}, "result": (lora_files,)} 