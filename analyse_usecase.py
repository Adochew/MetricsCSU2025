import xml.etree.ElementTree as ET
import argparse
import json

def parse_usecase_xmi(filename):
    tree = ET.parse(filename)
    root = tree.getroot()

    actors = {}
    usecases = {}
    associations = []

    for elem in root.findall(".//packagedElement"):
        # 处理带命名空间的属性：xmi:type, xmi:id
        xmi_type = elem.attrib.get('{http://schema.omg.org/spec/XMI/2.1}type') or elem.attrib.get('xmi:type')
        xmi_id = elem.attrib.get('{http://schema.omg.org/spec/XMI/2.1}id') or elem.attrib.get('xmi:id')
        name = elem.attrib.get('name', '')

        if xmi_type == 'uml:Actor':
            actors[xmi_id] = name
        elif xmi_type == 'uml:UseCase':
            usecases[xmi_id] = name
        elif xmi_type == 'uml:Association':
            ends = elem.findall('ownedEnd')
            for end in ends:
                actor_or_usecase_id = end.attrib.get('type')
                associations.append(actor_or_usecase_id)

    return actors, usecases, associations

def compute_usecase_metrics(actors, usecases, associations):
    # Use Case Weights (simplified): assume all use cases are average (weight 10)
    usecase_weight = 10
    uucw = len(usecases) * usecase_weight

    # Actor Weights (simplified): assume all actors are average (weight 2)
    actor_weight = 2
    uaw = len(actors) * actor_weight

    # ======== 使用结构性指标估算 TCF 和 EF ========
    # TCF = 0.6 + (0.4 * scale), scale ∈ [0, 1]
    tcf_score = (len(usecases) / 20) + (len(associations) / 30)
    tcf_score = min(tcf_score, 1.0)
    tcf_value = round(0.6 + (0.4 * tcf_score), 2)

    # EF = 1.4 - (0.6 * scale), scale ∈ [0, 1]
    ef_score = (len(actors) / 10) + (len(usecases) / 20)
    ef_score = min(ef_score, 1.0)
    ef_value = round(1.4 - (0.6 * ef_score), 2)

    # Unadjusted Use Case Points (UUCP)
    uucp = uaw + uucw

    # Use Case Points (UCP)
    ucp = uucp * tcf_value * ef_value

    return {
        "ActorCount": len(actors),
        "UseCaseCount": len(usecases),
        "AssociationCount": len(associations),
        "UAW": uaw,
        "UUCW": uucw,
        "UUCP": uucp,
        "TCF": tcf_value,
        "EF": ef_value,
        "UCP": round(ucp, 2)
    }


def main(input_path="user1.xml", output_path="metrics_usecase.json"):
    actors, usecases, associations = parse_usecase_xmi(input_path)
    metrics = compute_usecase_metrics(actors, usecases, associations)

    print(json.dumps(metrics, indent=2, ensure_ascii=False))
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="user1.xml", help="输入XMI文件路径")
    parser.add_argument("--output", default="metrics_usecase.json", help="输出JSON路径")
    args = parser.parse_args()
    
    main(args.input, args.output)