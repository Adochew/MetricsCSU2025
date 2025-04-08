import sys

import streamlit as st
import subprocess
import json
import os
import pandas as pd
import shutil
from visualization import show_visualization

st.set_page_config(page_title="Metrics", layout="wide")

st.markdown("""
    <style>
        /* 侧边栏整体右移 */
        section[data-testid="stSidebar"] > div:first-child {
            padding-left: 20px;
            padding-right: 10px;
        }

        /* 给每个侧边栏控件容器增加底部间距 */
        section[data-testid="stSidebar"] .stElementContainer {
            margin-bottom: 1.5rem;
        }
    </style>
""", unsafe_allow_html=True)



# 字段说明字典，根据不同模块分类
FIELD_TOOLTIPS = {
    "用例图分析": {
        "description": "用例图分析主要用于评估系统的功能需求，并通过各种复杂度度量来确定系统的设计和实现复杂性。",
        "UAW": "用例图中的活跃参与者数。",
        "UUCW": "用例图中的用例权重。",
        "UUCP": "用例图中的用例点数。",
        "TCF": "用例图的技术复杂度因子。",
        "EF": "用例图的环境因子。",
        "UCP": "用例点数，用于衡量用例图的复杂度。"
    },
    "类图分析": {
        "description": "类图分析用于评估面向对象系统中的类及其关系的复杂性，通过度量各类的内部和外部结构来帮助理解系统的可维护性。",
        "WMC": "类的复杂度指标，指类中的方法数。",
        "DIT": "类的继承深度。",
        "NOC": "类的子类数量。",
        "CBO": "类的耦合度，即与其他类的关联数。",
        "RFC": "类的响应类数，表示该类调用的其他类的数量。",
        "LCOM": "类的内聚度，表示类的方法之间的关联度。",
        "NOA": "类中属性的数量。",
        "NOM": "类中方法的数量。",
        "SIZE": "类的大小，表示其代码的总行数。",
        "MHF": "类的功能模块的丰富度，值越大，功能越丰富。",
        "AHF": "类的应用功能的丰富度。",
        "MIF": "类的模块化度，值越大，模块化程度越高。",
        "AIF": "类的应用功能的模块化度。",
        "CF": "类的复杂度函数。"
    },
    "代码指标分析": {
        "description": "代码指标分析侧重于源代码的各类度量，例如代码行数、复杂度、注释等，旨在评估代码的质量、可读性和维护性。",
        "File": "文件路径，指示源代码文件的路径。",
        "TotalLines": "文件的总行数。",
        "BlankLines": "文件中的空白行数。",
        "CommentLines": "文件中的注释行数。",
        "CodeLines": "文件中的代码行数。",
        "LogicalLines": "文件中的逻辑行数。",
        "CyclomaticComplexity": "文件的圈复杂度指标，包括总复杂度、最大复杂度、平均复杂度和函数数。",
    }
}



def prepare_src_folder(uploaded_files):
    src_dir = "src"

    # 删除并重建 src 目录
    if os.path.exists(src_dir):
        shutil.rmtree(src_dir)
    os.makedirs(src_dir, exist_ok=True)

    # 保存所有上传文件
    saved_paths = []
    for uploaded_file in uploaded_files:
        save_path = os.path.join(src_dir, uploaded_file.name)
        with open(save_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        saved_paths.append(save_path)

    return saved_paths


# 左侧模块选择
st.sidebar.title("模块选择")
module = st.sidebar.radio(
    "请选择要分析的模块：",
    ["用例图分析", "类图分析", "代码指标分析"]
)

# 各模块对应的脚本路径和默认输出文件名
MODULE_CONFIG = {
    "用例图分析": {
        "script": "analyse_usecase.py",
        "default_output": "metrics_usecase.json",
        "file_type": ["xml"]
    },
    "类图分析": {
        "script": "analyse_oo.py",
        "default_output": "metrics_oo.json",
        "file_type": ["xml"]
    },
    "代码指标分析": {
        "script": "analyse_code.py",
        "default_output": "metrics_code.json",
        "file_type": ["py"]
    }
}

config = MODULE_CONFIG[module]

st.title(f"{module} 模块")

# 显示模块的说明文字
st.markdown(FIELD_TOOLTIPS[module]["description"])

# 上传文件 or 使用已有文件
input_mode = st.radio("选择输入方式", ["上传并扫描", "读取已有JSON文件"])

if input_mode == "上传并扫描":
    if module == "代码指标分析":
        uploaded = st.file_uploader(f"上传文件（类型：{', '.join(config['file_type'])}）", type=config["file_type"], accept_multiple_files=True)
        prepare_src_folder(uploaded)
    else:
        uploaded = st.file_uploader(f"上传文件（类型：{', '.join(config['file_type'])}）", type=config["file_type"])

    if module == "类图分析":
        code_files = st.file_uploader("上传 Python 源代码文件", type=["py"], accept_multiple_files=True)
        if code_files:
            prepare_src_folder(code_files)

    output_path = st.text_input("输出结果保存为（JSON）", value=config["default_output"])

    # 检查是否上传文件，如果没有上传文件则提示报错
    if st.button("开始分析"):
        if uploaded is None:
            st.error("请上传文件进行分析！")
        else:

            if module == "代码指标分析":
                # 执行分析脚本
                result = subprocess.run(
                    [sys.executable, config["script"], "--output", output_path],
                    capture_output=True, text=True
                )

            else:
                # 保存上传文件
                os.makedirs("tmp", exist_ok=True)
                input_path = os.path.join("tmp", uploaded.name)

                with open(input_path, "wb") as f:
                    f.write(uploaded.getbuffer())

                # 执行分析脚本
                result = subprocess.run(
                    [sys.executable, config["script"], "--input", input_path, "--output", output_path],
                    capture_output=True, text=True
                )

            if result.returncode == 0:
                st.success("分析成功 ✅")
                
                # 读取分析结果并展示表格
                with open(output_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                
                # 显示表格
                df = pd.json_normalize(data)
                st.table(df)

                # 显示字段说明，默认展开
                with st.expander("字段说明", expanded=True):
                    for field, tooltip in FIELD_TOOLTIPS[module].items():
                        if field != "description":  # 跳过 description 字段
                            st.markdown(f"**{field}**: {tooltip}")

                # 显示 JSON 数据
                st.subheader("原始 JSON 数据")
                st.json(data)

                show_visualization(df, module)

            else:
                st.error("分析失败 ❌")
                st.text(result.stderr)

elif input_mode == "读取已有JSON文件":
    json_file = st.file_uploader("选择已有 JSON 文件", type=["json"])
    if json_file:
        try:
            data = json.load(json_file)
            st.success("成功读取 JSON 文件 ✅")
            
            # 显示表格
            df = pd.json_normalize(data)
            st.table(df)

            # 可折叠显示字段说明，默认展开
            with st.expander("字段说明", expanded=True):
                for field, tooltip in FIELD_TOOLTIPS[module].items():
                    if field != "description":  # 跳过 description 字段
                        st.markdown(f"**{field}**: {tooltip}")

            # 显示 JSON 数据
            st.subheader("原始 JSON 数据")
            st.json(data)

            show_visualization(df, module)

        except Exception as e:
            st.error("读取失败 ❌")
            st.text(str(e))
