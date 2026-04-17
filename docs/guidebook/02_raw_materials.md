# 第二章：准备原材料

模型再聪明，也得先看对图。这个项目当前识别资产的规则很明确：**递归寻找“包含图片的目录”**，一旦命中就停止继续向下遍历该分支，并把这个目录当成一个资产。

## 1. 推荐的仓库摆放方式

最常见、也最适合当前代码的输入结构是：

```text
input_dir/
  category/
    asset_uuid/
      front.png
      left.png
      back.png
      right.png
```

输出则会镜像成：

```text
output_dir/
  category/
    asset_uuid_annotation.json
```

## 2. 视角命名不一定非得一样

`config/config.yaml` 当前默认写的是：

```yaml
data:
  views:
    front: ["front.png", "0.png"]
    left: ["left.png", "1.png"]
    back: ["back.png", "2.png"]
    right: ["right.png", "3.png"]
```

意思是：

- 如果目录里有 `front.png`，它会被当作正面图
- 如果没有，但有 `0.png`，也会把它当作正面图

## 3. 找不到命名视角怎么办？

`get_asset_images()` 还有一个很实用的回退逻辑：

- 如果一个命名视角都没匹配上
- 它会扫描目录里所有 `.png`、`.jpg`、`.jpeg`
- 然后按自然排序全部拿来用

所以，规范命名最好；但只要目录里确实有图，也不至于立刻完全跑不起来。

## 4. 缩略图目录是兼容模式

如果你把 `use_thumbnails_dir` 打开，程序会优先去资产目录下的 `thumbnails/` 子目录找图；找不到时，再回退到资产根目录。这是一个兼容旧数据布局的开关，不是当前默认生产布局。

## 5. 小提醒

- 背景越干净，模型越不容易分心
- 多视角越完整，描述越稳
- 文件夹里只要出现图片，该目录就可能被识别为一个资产；不要把临时图片随手塞进上层目录

原材料备齐之后，下一章就可以正式施法了。
