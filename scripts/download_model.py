import os
from huggingface_hub import snapshot_download

def main():
    # 1. 设置 HF 国内镜像环境变量
    os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"

    # 2. 配置下载参数
    # 模型 ID
    repo_id = "Qwen/Qwen2.5-VL-7B-Instruct"
    
    # 基础路径：用户指定的 /cpfs/shared/simulation/zhuzihou
    base_path = "/cpfs/shared/simulation/zhuzihou"
    
    # 新建文件夹名称，例如叫 'models'
    new_folder = "models"
    
    # 最终存放路径
    target_dir = os.path.join(base_path, new_folder, repo_id.split("/")[-1])

    print(f"准备从 hf-mirror.com 下载模型: {repo_id}")
    print(f"保存路径: {target_dir}")

    # 3. 开始下载
    # local_dir_use_symlinks=False 确保下载的是实际文件而不是缓存软链接，方便迁移和共享
    snapshot_download(
        repo_id=repo_id,
        local_dir=target_dir,
        local_dir_use_symlinks=False, 
        resume_download=True,
        max_workers=8 # 加速下载
    )

    print(f"\n下载完成！模型位于: {target_dir}")
    print("您可以将此路径配置到 config.yaml 的 model.name 字段中。")

if __name__ == "__main__":
    # 确保安装了 huggingface_hub: pip install huggingface_hub
    main()
