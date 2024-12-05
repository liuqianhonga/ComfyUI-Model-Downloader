import { app } from "../../../scripts/app.js";
import { ComfyWidgets } from "../../../scripts/widgets.js";

app.registerExtension({
    name: "ModelDownloader.DisplayLoraList",
    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        if (nodeData.name === "LoadLoraByPath") {
            const onExecuted = nodeType.prototype.onExecuted;
            nodeType.prototype.onExecuted = function (message) {
                onExecuted?.apply(this, arguments);

                if (this.widgets) {
                    const pos = this.widgets.findIndex((w) => w.name === "lora_list");
                    if (pos !== -1) {
                        for (let i = pos; i < this.widgets.length; i++) {
                            this.widgets[i].onRemove?.();
                        }
                        this.widgets.length = pos;
                    }
                }

                // 创建一个新的只读文本框来显示 LoRA 列表
                const widget = ComfyWidgets["STRING"](this, "lora_list", ["STRING", { multiline: true }], app).widget;
                widget.inputEl.readOnly = true;
                widget.inputEl.style.opacity = 0.6;
                
                // 如果有返回的 loras 列表，将其格式化并显示
                if (message.loras && Array.isArray(message.loras[0])) {
                    const loraFiles = message.loras[0];
                    const formattedList = loraFiles.map(path => {
                        // 从路径中提取文件名
                        const fileName = path.split('/').pop();
                        return fileName;
                    }).join('\n');
                    widget.value = formattedList || "No LoRA files found";
                } else {
                    widget.value = "No LoRA files found";
                }

                this.onResize?.(this.size);
            };
        }
    }
}); 