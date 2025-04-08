import xml.etree.ElementTree as ET
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

    # Technical Complexity Factor (TCF): placeholder values
    tcf_factor = 0.6
    tcf_value = 0.6  # Normally: TCF = 0.6 + (0.01 * sum of 13 factors)

    # Environmental Factor (EF): placeholder values
    ef_factor = 0.7
    ef_value = 0.7  # Normally: EF = 1.4 + (-0.03 * sum of 8 factors)

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

def main():
    xmi_path = "user1.xml"
    actors, usecases, associations = parse_usecase_xmi(xmi_path)
    metrics = compute_usecase_metrics(actors, usecases, associations)

    print(json.dumps(metrics, indent=2, ensure_ascii=False))

    with open("metrics_usecase.json", "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    main()
