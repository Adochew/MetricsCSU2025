import os
import argparse
import json
from radon.complexity import cc_visit

def analyze_code_file(filepath):
    """分析单个代码文件"""
    with open(filepath, 'r', encoding='utf-8') as f:
        code = f.read()

    lines = code.split('\n')
    blank_lines = sum(1 for line in lines if line.strip() == "")
    comment_lines = sum(1 for line in lines if line.strip().startswith("#"))
    total_lines = len(lines)
    code_lines = total_lines - blank_lines - comment_lines

    try:
        functions = cc_visit(code)
        cc_scores = [f.complexity for f in functions]
    except Exception:
        functions = []
        cc_scores = []

    cc_total = sum(cc_scores)
    cc_max = max(cc_scores) if cc_scores else 0
    cc_avg = round(cc_total / len(cc_scores), 2) if cc_scores else 0.0

    return {
        "File": filepath,
        "TotalLines": total_lines,
        "BlankLines": blank_lines,
        "CommentLines": comment_lines,
        "CodeLines": code_lines,
        "LogicalLines": len(functions),
        "CyclomaticComplexity": {
            "Total": cc_total,
            "Max": cc_max,
            "Avg": cc_avg,
            "FunctionCount": len(functions)
        }
    }

def main(output_path="metrics_code.json"):
    """分析 src 文件夹下所有 Python 文件"""
    src_dir = "src"
    all_results = []

    if not os.path.exists(src_dir):
        print("⚠️ src 文件夹不存在！")
        return

    for root, _, files in os.walk(src_dir):
        for file in files:
            if file.endswith(".py"):
                filepath = os.path.join(root, file)
                result = analyze_code_file(filepath)
                all_results.append(result)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)

    print(f"分析完成，共分析 {len(all_results)} 个文件，结果保存在 {output_path}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="metrics_code.json", help="输出结果的 JSON 文件路径")
    args = parser.parse_args()

    main(args.output)
