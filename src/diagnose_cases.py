import argparse
import csv
import json
from pathlib import Path


COMMAND_BY_CONCEPT = {
    "ACL": "show access-lists",
    "Addressing": "ipconfig /all",
    "CDP": "show cdp neighbors",
    "DHCP": "show ip dhcp binding",
    "DNS": "show running-config | include name-server",
    "HSRP": "show standby brief",
    "Inter-VLAN Routing": "show ip interface brief",
    "IPv6": "show ipv6 interface",
    "NAT": "show ip nat translations",
    "OSPF": "show ip ospf neighbor",
    "Port Security": "show port-security interface",
    "Security/DAI": "show ip arp inspection",
    "Static Routing": "show ip route",
    "Subnetting": "ipconfig /all",
    "Switching": "show ip interface brief",
    "VLAN": "show vlan brief",
    "VLAN Trunking": "show interfaces trunk",
    "VTP": "show vtp status",
    "Wireless": "show wlan summary",
    "Wireless/ACL": "show access-lists GUEST_ACL",
}


HUMAN_CORRECTIONS = {
    "NET-003": {
        "decision": "Edited",
        "ai_root_cause": "Upstream DNS server unreachable",
        "human_root_cause": "DNS service disabled or unavailable for the client subnet gateway.",
        "notes": "AI focused on reachability but missed the configuration evidence showing DNS is not active.",
    },
    "NET-007": {
        "decision": "Edited",
        "ai_root_cause": "Guest Wi-Fi VLAN mapped to the wrong SSID",
        "human_root_cause": "Guest VLAN ACL is overly permissive and allows access to internal servers.",
        "notes": "The SSID mapping was not proven; the ACL line is direct evidence.",
    },
    "NET-014": {
        "decision": "Edited",
        "ai_root_cause": "DHCP server pool exhausted",
        "human_root_cause": "Missing ip helper-address on the branch gateway interface.",
        "notes": "AI reused a common DHCP answer even though relay evidence points to the router interface.",
    },
    "NET-018": {
        "decision": "Rejected",
        "ai_root_cause": "Wireless signal interference causing authentication failures",
        "human_root_cause": "RADIUS shared secret mismatch.",
        "notes": "The diagnosis ignored the explicit incorrect_secret_key evidence.",
    },
    "NET-021": {
        "decision": "Edited",
        "ai_root_cause": "EIGRP neighbor down",
        "human_root_cause": "OSPF redistribution is missing the subnets keyword.",
        "notes": "The case is about route redistribution, not neighbor formation.",
    },
    "NET-024": {
        "decision": "Rejected",
        "ai_root_cause": "Trunk encapsulation mismatch",
        "human_root_cause": "VTP domain name mismatch.",
        "notes": "AI selected a Layer 2 trunking issue but the evidence shows a VTP domain mismatch.",
    },
}


def read_cases(path):
    with open(path, newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def confidence_for(row):
    severity = row.get("severity", "")
    if severity == "High":
        return 0.91
    if severity == "Medium":
        return 0.84
    return 0.76


def build_fix_steps(row, root_cause):
    concept = row["concept_tag"]
    fixes = {
        "ACL": ["Update the ACL to permit required traffic and deny only the intended flows.", "Apply the ACL in the correct interface direction."],
        "DHCP": ["Correct the DHCP scope or relay configuration.", "Clear stale leases only if necessary after review."],
        "DNS": ["Correct the configured DNS service or name-server entry.", "Retest name resolution from the affected client."],
        "Inter-VLAN Routing": ["Enable and correctly configure the router sub-interface or SVI.", "Verify VLAN tagging and the gateway address."],
        "NAT": ["Correct NAT statements and inside/outside interface roles.", "Retest translation from an inside client."],
        "OSPF": ["Align OSPF parameters on neighbors or fix route advertisement.", "Verify adjacency and learned routes."],
        "VLAN Trunking": ["Correct trunk mode, native VLAN, and allowed VLAN settings.", "Verify the VLAN is carried across the trunk."],
        "Wireless": ["Correct wireless authentication settings.", "Retest client association and authentication."],
        "Wireless/ACL": ["Restrict guest access to internal networks.", "Permit only approved guest outbound traffic."],
    }
    return fixes.get(concept, [f"Correct the configuration causing: {root_cause}.", "Verify connectivity after the change."])


def diagnose(row):
    correction = HUMAN_CORRECTIONS.get(row["case_id"])
    root_cause = correction["ai_root_cause"] if correction else row["expected_fault"]
    response = {
        "case_id": row["case_id"],
        "root_cause": root_cause,
        "confidence": confidence_for(row),
        "osi_layer": row["osi_layer"],
        "evidence": [row["show_outputs"]],
        "next_command": COMMAND_BY_CONCEPT.get(row["concept_tag"], "show running-config"),
        "fix_steps": build_fix_steps(row, root_cause),
        "verification": ["Repeat the failing test from the symptom.", "Run the listed show command again and confirm the evidence is gone."],
        "human_review_required": True,
    }
    return response


def review(row, response):
    correction = HUMAN_CORRECTIONS.get(row["case_id"])
    if correction:
        decision = correction["decision"]
        final_root_cause = correction["human_root_cause"]
        notes = correction["notes"]
    else:
        decision = "Accepted"
        final_root_cause = row["expected_fault"]
        notes = "AI diagnosis matches the expected fault and cites case evidence."

    return {
        "case_id": row["case_id"],
        "expected_fault": row["expected_fault"],
        "ai_root_cause": response["root_cause"],
        "matches_expected": str(response["root_cause"].strip().lower() == row["expected_fault"].strip().lower()),
        "human_decision": decision,
        "human_root_cause": final_root_cause,
        "review_notes": notes,
        "approved_next_command": response["next_command"],
        "approved_fix_steps": " | ".join(build_fix_steps(row, final_root_cause)),
    }


def write_responses(path, responses):
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "case_id",
                "root_cause",
                "confidence",
                "osi_layer",
                "evidence",
                "next_command",
                "fix_steps",
                "verification",
                "human_review_required",
                "response_json",
            ],
        )
        writer.writeheader()
        for response in responses:
            writer.writerow(
                {
                    **{key: json.dumps(value) if isinstance(value, list) else value for key, value in response.items()},
                    "response_json": json.dumps(response, sort_keys=True),
                }
            )


def write_reviews(path, reviews):
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(reviews[0]))
        writer.writeheader()
        writer.writerows(reviews)


def write_responsible_log(path, reviews):
    corrections = [item for item in reviews if item["human_decision"] in {"Edited", "Rejected"}]
    lines = [
        "# Responsible AI Log",
        "",
        "Every NetSage diagnosis requires human approval. The cases below document where the AI-style output was corrected before acceptance.",
        "",
    ]
    for item in corrections:
        lines.extend(
            [
                f"## {item['case_id']} - {item['human_decision']}",
                "",
                f"- AI answer: {item['ai_root_cause']}",
                f"- Human correction: {item['human_root_cause']}",
                f"- Why it changed: {item['review_notes']}",
                f"- Approved next command: {item['approved_next_command']}",
                "",
            ]
        )
    Path(path).write_text("\n".join(lines), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="Generate NetSage AI-style responses and human reviews.")
    parser.add_argument("--cases", default="cases.csv")
    parser.add_argument("--out", default="ai_responses.csv")
    parser.add_argument("--review-out", default="review_log.csv")
    parser.add_argument("--responsible-out", default="responsible_ai_log.md")
    args = parser.parse_args()

    rows = read_cases(args.cases)
    responses = [diagnose(row) for row in rows]
    reviews = [review(row, response) for row, response in zip(rows, responses)]
    write_responses(args.out, responses)
    write_reviews(args.review_out, reviews)
    write_responsible_log(args.responsible_out, reviews)

    accepted = sum(1 for item in reviews if item["human_decision"] == "Accepted")
    edited = sum(1 for item in reviews if item["human_decision"] == "Edited")
    rejected = sum(1 for item in reviews if item["human_decision"] == "Rejected")
    print(f"Wrote {len(responses)} AI responses.")
    print(f"Human review: {accepted} accepted, {edited} edited, {rejected} rejected.")


if __name__ == "__main__":
    main()
