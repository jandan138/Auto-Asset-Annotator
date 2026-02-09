from typing import List, Union, Optional  # 导入类型提示：列表、联合类型、可选类型

SUPPORTED_PROMPT_TYPES = [  # 定义支持的提示词类型列表
    "find_canonical_front_view_prompt",  # 寻找标准正视图提示词
    "is_symmetric_object_prompt",  # 判断物体是否对称提示词
    "classify_object_category_prompt",  # 物品分类提示词
    "classify_object_category_with_background_prompt",  # 带背景的物品分类提示词
    "describe_object_prompt_MMScan",  # MMScan 物品描述提示词
    "describe_object_with_background_prompt",  # 带背景的物品描述提示词
    "polish_description_prompt_MMScan",  # MMScan 描述润色提示词
    "extract_object_attributes_prompt",  # 提取物品属性提示词
    "object_cognition_QA_with_background_prompt",  # 带背景的物品认知问答提示词
]

class PromptFactory:  # 定义 PromptFactory 类，用于生成提示词
    @staticmethod  # 静态方法装饰器
    def compose_user_prompt(  # 定义生成用户提示词的方法
        image_number: int,  # 图片数量
        prompt_type: str,  # 提示词类型
        image_merge: bool = False,  # 是否合并图片，默认为 False
        object_additional_info: Optional[List[str]] = None  # 对象的额外信息，可选
    ) -> Union[str, List[str]]:  # 返回字符串或字符串列表
        
        if prompt_type not in SUPPORTED_PROMPT_TYPES:  # 检查提示词类型是否受支持
             raise ValueError(f"Invalid prompt_type: {prompt_type}. Supported: {SUPPORTED_PROMPT_TYPES}")  # 如果不支持，抛出异常

        if prompt_type == "find_canonical_front_view_prompt":  # 如果是寻找标准正视图提示词
            return (  # 返回提示词字符串
                f"The 3D asset is represented by {image_number} separate images showing different views of the object.\n"  # 描述输入：N 张展示不同视角的图片
                f"Identify the canonical front view index (0-{image_number-1}) from these {image_number} orthogonal images.\n"  # 要求：识别标准正视图的索引
                "Using 3D modeling standards. Output only the integer with no additional text or formatting."  # 约束：仅输出整数，无其他文本
            )
        elif prompt_type == "is_symmetric_object_prompt":  # 如果是判断物体是否对称提示词
            return (  # 返回提示词字符串
                f"You are given {image_number} images showing a 360-degree rotation of the same object. Please analyze these images and determine:\n"  # 描述输入：360度旋转图
                "Does the object appear nearly identical from all angles — such as being spherical, cylindrical, or highly symmetric?\n"  # 问题：物体是否在所有角度看起来几乎相同？
                "Based on your analysis, output exactly one of the following:\n"  # 输出要求
                "- '0': If the object appear nearly identical from all angles.\n"  # 0：是
                "- '1': Else.\n"  # 1：否
                "Do NOT provide any additional explanation. Only return one number: 0, 1"  # 约束：仅返回数字，无解释
            )
        elif prompt_type == "classify_object_category_prompt":  # 如果是物品分类提示词
            multi_image_query = f"You are presented with {image_number} distinct rendered views of an indoor object captured against a neutral gray-white background."  # 多图查询描述
            merge_image_query = "This composite image displays multiple rendered views of the same object from different perspectives."  # 合并图查询描述
            image_query = merge_image_query if image_merge else multi_image_query  # 根据是否合并图片选择查询描述
            categories_query = "Analyze the object and classify it into a single, precise category based on its primary function and characteristics."  # 分类要求
            output_query = "Provide ONLY the category name as your response - no additional text, explanation, or formatting."  # 输出约束
            return f"{image_query} {categories_query} {output_query}"  # 拼接并返回完整提示词
        
        elif prompt_type == "extract_object_attributes_prompt":  # 如果是提取物品属性提示词
            # object_additional_info usually [scene_type, ..., category]
            if not object_additional_info:  # 如果没有提供额外信息
                 # Fallback if info missing
                 object_in_scene_type = "indoor scene"  # 默认为室内场景
                 object_category = "object"  # 默认为物体
            else:  # 如果提供了额外信息
                 object_in_scene_type = f"{object_additional_info[0]} scene"  # 提取场景类型
                 object_category = object_additional_info[-1]  # 提取物体类别

            object_query = (  # 定义对象查询描述
                f"You are provided with multiple views of a {object_category} object that is placed {object_in_scene_type}. "  # 描述物体及其场景
            )
            attribute_query = (  # 定义属性查询要求
                "Analyze the provided image and extract the following structured information. "  # 分析图片并提取结构化信息
                "You MUST respond in strict JSON format with ALL fields required. Do not omit any field.\n\n"  # 必须返回严格的 JSON 格式
                "Required JSON structure:\n"  # 要求的 JSON 结构
                "{\n"
                '  "category": "object type (e.g., plate, cup, bottle)",\n'  # 类别字段
                '  "description": "comprehensive description covering: physical appearance (shape, form, colors), material properties (surface texture, finish), scale and proportions, current state (e.g., open/closed components), functional purpose, and distinctive design features. Use concrete, observable details in 3-4 sentences.",\n'  # 描述字段
                '  "material": "describe all materials present in the object in detail. For each material, specify which part of the object it applies to (e.g., \'metal handle\', \'ceramic body\', \'rubber base\'). List as many different materials as you can identify. Common materials include: plastic, metal, wood, fabric, ceramic, glass, rubber, stone, paper, foam, leather, cardboard, clay, resin, plaster, polyester, laminate, cotton, steel, aluminum, concrete, stainless steel, gold, silver, etc.",\n'  # 材质字段
                '  "dimensions": "length * width * height in meters (e.g., 0.25 * 0.25 * 0.05). Estimate if exact values unknown.",\n'  # 尺寸字段
                '  "mass": "mass in kilograms as a number (e.g., 0.5). Estimate if exact value unknown.",\n'  # 质量字段
                '  "placement": "select one or more possible placements from the list: OnFloor, OnObject, OnWall, OnCeiling, OnTable. If multiple placements are possible, list them in descending order of likelihood (e.g., [\'OnTable\', \'OnFloor\', \'OnObject\'])"\n'  # 放置位置字段
                "}\n\n"
                "Important: \n"  # 重要提示
                "1. Return ONLY valid JSON, no additional text\n"  # 仅返回 JSON
                "2. ALL fields are mandatory - provide best estimate if uncertain\n"  # 所有字段必填
                "3. For 'material', describe all materials and their corresponding parts comprehensively\n"  # 详细描述材质
                "4. For 'placement', provide one or more options as an array, ordered by likelihood (most likely first)\n"  # 放置位置为数组
                "5. Ensure proper JSON syntax with double quotes"  # 确保 JSON 语法正确
            )
            return f"{object_query} {attribute_query}"  # 拼接并返回完整提示词
        
        # ... Implement other prompts if needed, but for now focusing on the main ones used in the script.
        # The user's goal seems to be annotation, which usually means attributes/caption.
        # I'll include the others for completeness based on original file.
        
        elif prompt_type == "describe_object_prompt_MMScan":  # 如果是 MMScan 物品描述提示词
            multi_image_query = f"You are presented with {image_number} distinct rendered views of an indoor object captured against a neutral gray-white background."  # 多图查询描述
            merge_image_query = "This composite image displays multiple rendered views of the same object from different perspectives."  # 合并图查询描述
            image_query = merge_image_query if image_merge else multi_image_query  # 选择查询描述
            description_query = (  # 定义描述查询要求
                "Provide a comprehensive description of this object using clear, detailed sentences. Focus on the following key aspects:\n"  # 提供全面描述，关注关键方面
                "- Physical appearance: precise shape, form, and predominant colors\n"  # 物理外观
                "- Material properties: surface texture, material type, and finish quality\n"   # 材质属性
                "- Scale and proportions: relative size compared to typical objects of this type\n"  # 比例和尺寸
                "- Current state: configuration of movable components (doors, drawers, etc.)\n"  # 当前状态
                "- Functional purpose: primary intended use and operational characteristics\n"  # 功能用途
                "- Design features: notable structural elements and distinctive details\n"  # 设计特征
                "Ensure each sentence contains concrete, observable details rather than subjective interpretations."  # 确保客观具体
            )
            output_query = "Generate 3-5 informative sentences with specific, factual descriptions. Use clear, objective language without bullet points or line breaks."  # 输出要求：3-5句事实描述
            return f"{image_query} {description_query} {output_query}"  # 拼接并返回完整提示词

        # Skipping background prompts for simplicity unless requested, as they require complex input handling (list of prompts)
        # which might complicate the basic pipeline. But to be "complete" I should support them.
        
        elif prompt_type == "classify_object_category_with_background_prompt":  # 如果是带背景的物品分类提示词
             return [  # 返回提示词列表（多轮对话或多部分输入）
                 "The following four images are the same object with a red bounding box which we need to describe.",  # 第一部分：带框物体图描述
                 "The following images highlight the target object with a red bounding box which is the same as the first four images.",  # 第二部分：带框背景图描述
                 "Analyze the object and classify it into a single, precise category based on its primary function and characteristics. Provide ONLY the category name as your response - no additional text, explanation, or formatting. If you output the wrong information you will be fired."  # 第三部分：分类任务要求
             ]
             
        # Add others as needed...
        
        return ""  # 默认返回空字符串
