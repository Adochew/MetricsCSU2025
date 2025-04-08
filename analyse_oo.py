import os
import argparse
import json
import xml.etree.ElementTree as ET
import ast

# 可选复杂度库（如果需要更准 WMC）
try:
    from radon.complexity import cc_visit
    USE_RADON = True
except ImportError:
    USE_RADON = False

class ClassInfo:
    def __init__(self, id_, name):
        self.id = id_
        self.name = name
        self.attributes = []
        self.methods = []
        self.parent = None
        self.children = []
        self.implements = []
        self.associations = set()
        self.code_methods = {}  # 方法名 -> {'calls': set(), 'fields': set(), 'complexity': int}

    def __repr__(self):
        return f"{self.name}(attr={len(self.attributes)}, meth={len(self.methods)})"

# ---------- 解析 XMI ----------

def parse_xmi(xmi_file):
    tree = ET.parse(xmi_file)
    root = tree.getroot()
    ns = {'uml': 'http://www.eclipse.org/uml2/2.1.0/UML', 'xmi': 'http://schema.omg.org/spec/XMI/2.1'}

    classes = {}
    id_to_name = {}

    for elem in root.findall(".//packagedElement[@xmi:type='uml:Class']", ns):
        cid = elem.attrib['{http://schema.omg.org/spec/XMI/2.1}id']
        name = elem.attrib.get('name', f"Unnamed_{cid}")
        cls = ClassInfo(cid, name)

        for attr in elem.findall('ownedAttribute'):
            cls.attributes.append(attr.attrib.get('name', ''))

        for op in elem.findall('ownedOperation'):
            cls.methods.append(op.attrib.get('name', ''))

        classes[cid] = cls
        id_to_name[cid] = name

    for gen in root.findall(".//generalization"):
        parent_id = gen.attrib.get('general')
        child_id = gen.get('xmi:idref') or gen.get('xmi:id')
        if child_id in classes:
            classes[child_id].parent = parent_id
            if parent_id in classes:
                classes[parent_id].children.append(child_id)

    for assoc in root.findall(".//packagedElement[@xmi:type='uml:Association']", ns):
        for end in assoc.findall('ownedEnd'):
            class_id = end.attrib.get('type')
            if class_id in classes:
                other_ends = [e.attrib['type'] for e in assoc.findall('ownedEnd') if e.attrib['type'] != class_id]
                for oid in other_ends:
                    classes[class_id].associations.add(oid)

    return classes

# ---------- Python 源码分析器 ----------

class MethodAnalyzer(ast.NodeVisitor):
    def __init__(self):
        self.calls = set()
        self.fields = set()

    def visit_Call(self, node):
        if isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name):
            if node.func.value.id == 'self':
                self.calls.add(node.func.attr)
        self.generic_visit(node)

    def visit_Attribute(self, node):
        if isinstance(node.value, ast.Name) and node.value.id == 'self':
            self.fields.add(node.attr)
        self.generic_visit(node)

def analyze_python_sources(src_folder, classes):
    for root, _, files in os.walk(src_folder):
        for file in files:
            if not file.endswith(".py"):
                continue
            with open(os.path.join(root, file), 'r', encoding='utf-8') as f:
                try:
                    source = f.read()
                    tree = ast.parse(source)
                    analyze_module(tree, source, classes)
                except Exception as e:
                    print(f"⚠️ 解析失败：{file} - {e}")

def analyze_module(tree, source, classes):
    class_nodes = [n for n in tree.body if isinstance(n, ast.ClassDef)]
    for cnode in class_nodes:
        class_name = cnode.name
        target = next((c for c in classes.values() if c.name == class_name), None)
        if not target:
            continue
        for func in cnode.body:
            if isinstance(func, ast.FunctionDef):
                analyzer = MethodAnalyzer()
                analyzer.visit(func)
                complexity = 1
                if USE_RADON:
                    try:
                        blocks = cc_visit(ast.unparse(func))
                        complexity = sum(b.complexity for b in blocks)
                    except:
                        pass
                target.code_methods[func.name] = {
                    'calls': analyzer.calls,
                    'fields': analyzer.fields,
                    'complexity': complexity
                }

# ---------- 指标计算器 ----------

def get_dit(cls, classes):
    depth = 0
    while cls.parent:
        parent = classes.get(cls.parent)
        if not parent:
            break
        depth += 1
        cls = parent
    return depth

def compute_metrics(classes):
    result = []
    total_classes = len(classes)
    max_couplings = total_classes * (total_classes - 1)

    for cls in classes.values():
        # CK 度量
        wmc = sum([m['complexity'] for m in cls.code_methods.values()]) if cls.code_methods else len(cls.methods)
        lcom = 0
        if cls.code_methods:
            shared_fields = set()
            for m in cls.code_methods.values():
                shared_fields.update(m['fields'])
            lcom = max(0, len(cls.code_methods) - len(shared_fields))

        ck = {
            'WMC': wmc,
            'DIT': get_dit(cls, classes),
            'NOC': len(cls.children),
            'CBO': len(cls.associations),
            'RFC': len(set().union(*(m['calls'] for m in cls.code_methods.values()))) + len(cls.code_methods),
            'LCOM': lcom
        }

        # LK 度量
        lk = {
            'NOA': len(cls.attributes),
            'NOM': len(cls.methods),
            'SIZE': len(cls.attributes) + len(cls.methods)
        }

        # MOOD 度量
        private_methods = [m for m in cls.methods if m.startswith('_')]
        private_attributes = [a for a in cls.attributes if a.startswith('_')]

        inherited_attrs = []
        inherited_methods = []
        if cls.parent and cls.parent in classes:
            parent = classes[cls.parent]
            inherited_attrs = parent.attributes
            inherited_methods = parent.methods

        mood = {
            'MHF': round(len(private_methods) / len(cls.methods), 2) if cls.methods else 0.0,
            'AHF': round(len(private_attributes) / len(cls.attributes), 2) if cls.attributes else 0.0,
            'MIF': round(len(inherited_methods) / len(cls.methods), 2) if cls.methods else 0.0,
            'AIF': round(len(inherited_attrs) / len(cls.attributes), 2) if cls.attributes else 0.0,
            'CF': round(len(cls.associations) / max_couplings, 2) if max_couplings else 0.0
        }

        result.append({
            'NAME': cls.name,
            'CK': ck,
            'LK': lk,
            'MOOD': mood
        })

    return result


def main(input_path="temp2.xml", output_path="metrics_oo.json"):
    xmi_path = input_path
    # 假设代码实现都在同级目录下的 src 文件夹中
    source_path = os.path.join(os.path.dirname(input_path), "src")

    print("正在解析类图 ...")
    classes = parse_xmi(xmi_path)

    print("分析 Python 实现代码 ...")
    analyze_python_sources(source_path, classes)

    print("计算 CK / LK 指标 ...")
    metrics = compute_metrics(classes)

    print("保存到 JSON 文件 ...")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(metrics, f, indent=2, ensure_ascii=False)

    print(f"\n 完成！共分析 {len(classes)} 个类，指标保存在 {output_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="temp2.xml", help="输入XMI文件路径")
    parser.add_argument("--output", default="metrics_oo.json", help="输出JSON路径")
    args = parser.parse_args()

    main(args.input, args.output)
