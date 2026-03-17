import json
import os


def generate_report():
    input_path = "data/cards_compiled.json"
    output_path = "reports/id_mapping_summary.md"

    if not os.path.exists(input_path):
        print(f"Error: {input_path} not found.")
        return

    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    report = "# Card ID Mapping Summary\n\n"
    report += "| Card No | Packed ID | Logic ID | Variant | Name |\n"
    report += "| --- | --- | --- | --- | --- |\n"

    # Members
    members = data.get("member_db", {})
    # Sort by packed ID
    sorted_members = sorted(members.items(), key=lambda x: int(x[0]))

    for str_id, m in sorted_members:
        packed_id = int(str_id)
        logic_id = packed_id & 0x0FFF
        variant = packed_id >> 12
        card_no = m.get("card_no", "N/A")
        name = m.get("name", "N/A")[:20]  # Truncate for table
        report += f"| {card_no} | {packed_id} | {logic_id} | {variant} | {name} |\n"

    os.makedirs("reports", exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"Report generated at {output_path}")


if __name__ == "__main__":
    generate_report()
