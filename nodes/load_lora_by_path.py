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
                "lora_path": ("STRING", {
                    "default": "",
                    "multiline": False,
                }),
            }
        }
    
    RETURN_TYPES = (ANY,)
    RETURN_NAMES = ("loras",)
    OUTPUT_IS_LIST = (True,)
    FUNCTION = "load_loras"
    CATEGORY = "Model (Down)load"

    def load_loras(self, lora_path):
        # 构建完整路径
        full_path = os.path.join(self.lora_path, lora_path)
        
        # 检查目录是否存在
        if not os.path.exists(full_path):
            raise ValueError(f"Path not found: {full_path}")
        
        # 获取所有lora文件
        lora_files = []
        for file in os.listdir(full_path):
            if file.endswith(('.safetensors')):
                # 返回相对于loras目录的路径
                relative_path = os.path.join(lora_path, file)
                lora_files.append(relative_path)
        
        return (lora_files,) 