import os
import json
from radon.complexity import cc_visit

def analyze_code_file(filepath):
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

def analyze_folder(folder_path):
    all_results = []
    for root, _, files in os.walk(folder_path):
        for file in files:
            if file.endswith(".py"):
                filepath = os.path.join(root, file)
                result = analyze_code_file(filepath)
                all_results.append(result)
    return all_results

def main():
    results = analyze_folder("src")

    with open("metrics_code.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)


if __name__ == '__main__':
    main()