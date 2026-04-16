# Prompt 工程机制 (Prompt Engineering Mechanics)

在这个项目里，Prompt 工程不是“把问题说漂亮”，而是“让输出足够稳，稳到代码能接住”。

## 1. 当前主线为什么不用“直接 JSON”？

早期很多多模态项目都会要求模型直接返回 JSON，但真实运行里经常会遇到：

- 代码块包裹
- 额外解释文字
- 语法错误
- 多对象串在一起

当前主线 prompt `extract_object_attributes_prompt` 采取的是另一条路：

- 要求模型输出 **带明确字段头的 structured text**
- 再由 `parse_structured_text_enhanced()` 解析成 JSON

这就是当前仓库最值得记住的 Prompt 工程决策。

## 2. 主线属性提取 Prompt 的机制

`extract_object_attributes_prompt` 要求这些头：

- `Category:`
- `Description:`
- `Material:`
- `Dimensions:`
- `Mass:`
- `Placement:`

并且明确告诉模型：

- 不要输出 JSON
- 不要输出代码块
- 所有字段都必须给出

这相当于把模型限制在一个更窄、但更稳的回答轨道里。

## 3. Prompt 如何和多图输入结合

流水线内部的消息结构是：

```python
[
    {
        "role": "user",
        "content": [
            {"type": "text", "text": user_prompt},
            {"type": "image_url", "image": image_path_1},
            {"type": "image_url", "image": image_path_2},
            ...
        ]
    }
]
```

也就是说，Prompt 本身只是一部分；真正的输入是“文本约束 + 多视角图片”的组合。

## 4. 解析器如何配合 Prompt

`parse_structured_text_enhanced()` 做了三件事：

1. 清理模型输出中的杂质
2. 如果检测到多对象输出，只抽取第一对象块
3. 再用字段头正则提取键值

所以 Prompt 工程和解析器设计是一体的：

- Prompt 负责让结构出现
- Parser 负责把结构接住

## 5. 给新 Prompt 命名时要动脑子

当前规则是：

- 名字里包含 `extract`
- 或名字里包含 `json`

就会触发解析分支。

这非常方便，但也意味着你给 prompt 取名时要小心：

- 需要字段解析：可以利用这条规则
- 只想要纯文本：别误用这类命名

## 6. 什么时候该改 Prompt，什么时候该改 Parser？

- 输出太松散、字段顺序乱：先改 Prompt
- 模型偶尔有轻微脏文本或多对象串联：优先改 Parser
- 想新增字段：Prompt 和 Parser 通常都要一起改

Prompt 工程的目标不是“让模型看起来更聪明”，而是让整条流水线更稳定。
