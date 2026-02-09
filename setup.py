from setuptools import setup, find_packages

setup(
    name="auto_asset_annotator",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "transformers",
        "torch",
        "pillow",
        "natsort",
        "tqdm",
        "qwen-vl-utils",
        "pyyaml",
        "accelerate",
    ],
    entry_points={
        "console_scripts": [
            "auto-annotator=auto_asset_annotator.main:main",
        ],
    },
    author="Your Name",
    description="3D Asset Automated Annotation Tool based on Qwen3-VL",
    python_requires=">=3.8",
)
