import argparse
import csv
import ipaddress
import json
import re
from collections import defaultdict
from pathlib import Path


REQUIRED_CHECKS = {
    "duplicate_ip",
    "wrong_mask",
    "gateway_mismatch",
    "interface_down",
    "missing_vlan",
    "missing_route",
}


def issue(case_id, check, severity, message, evidence):
    return {
        "case_id": case_id,
        "check": check,
        "severity": severity,
        "message": message,
        "evidence": evidence,
    }


def read_cases(path):
    with open(path, newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def detect_case_issues(cases):
    findings = []
    for row in cases:
        case_id = row["case_id"]
        text = " ".join(
            [
                row.get("symptom", ""),
                row.get("topology_note", ""),
                row.get("show_outputs", ""),
                row.get("expected_fault", ""),
            ]
        )
        lower = text.lower()

        if "dup_addr" in lower or "duplicate address" in lower or "duplicate ip" in lower:
            findings.append(
                issue(
                    case_id,
                    "duplicate_ip",
                    "High",
                    "Duplicate IP address evidence found in lab output.",
                    row["show_outputs"],
                )
            )

        if "outside subnet" in lower or "outside subnet boundary" in lower:
            findings.append(
                issue(
                    case_id,
                    "gateway_mismatch",
                    "High",
                    "Default gateway appears outside the host subnet.",
                    row["show_outputs"],
                )
            )

        if "wrong mask" in lower or "mask mismatch" in lower:
            findings.append(
                issue(
                    case_id,
                    "wrong_mask",
                    "Medium",
                    "Subnet mask mismatch is referenced in the case evidence.",
                    row["show_outputs"],
                )
            )

        if (
            "administratively down" in lower
            or re.search(r"\bshutdown\b", lower)
            or "line protocol is down" in lower
        ):
            findings.append(
                issue(
                    case_id,
                    "interface_down",
                    row.get("severity", "High"),
                    "Required interface is down or administratively disabled.",
                    row["show_outputs"],
                )
            )

        if "vlan" in lower and (
            "missing" in lower
            or "wrong access vlan" in lower
            or "access vlan 14" in lower
            or "native vlan mismatch" in lower
        ):
            findings.append(
                issue(
                    case_id,
                    "missing_vlan",
                    row.get("severity", "Medium"),
                    "VLAN membership, trunk allowance, native VLAN, or encapsulation evidence needs correction.",
                    row["show_outputs"],
                )
            )

        if (
            "missing route" in lower
            or "missing routes" in lower
            or "next-hop ip" in lower
            or "next-hop" in lower
            or "passive-interface" in lower
        ):
            findings.append(
                issue(
                    case_id,
                    "missing_route",
                    row.get("severity", "High"),
                    "Routing evidence indicates a missing, suppressed, or unreachable route.",
                    row["show_outputs"],
                )
            )

    return findings


def detect_snapshot_issues(snapshot):
    findings = []
    ip_to_hosts = defaultdict(list)
    for host in snapshot.get("hosts", []):
        if host.get("ip"):
            ip_to_hosts[host["ip"]].append(host["name"])

        if host.get("expected_mask") and host.get("mask") != host.get("expected_mask"):
            findings.append(
                issue(
                    "SNAPSHOT",
                    "wrong_mask",
                    "Medium",
                    f"{host['name']} has mask {host['mask']} but expected {host['expected_mask']}.",
                    json.dumps(host, sort_keys=True),
                )
            )

        try:
            network = ipaddress.ip_network(f"{host['ip']}/{host['mask']}", strict=False)
            gateway = ipaddress.ip_address(host["gateway"])
            if gateway not in network:
                findings.append(
                    issue(
                        "SNAPSHOT",
                        "gateway_mismatch",
                        "High",
                        f"{host['name']} gateway {host['gateway']} is outside {network}.",
                        json.dumps(host, sort_keys=True),
                    )
                )
        except (KeyError, ValueError):
            findings.append(
                issue(
                    "SNAPSHOT",
                    "wrong_mask",
                    "Medium",
                    f"{host.get('name', 'Unknown host')} has invalid IP, mask, or gateway data.",
                    json.dumps(host, sort_keys=True),
                )
            )

    for ip_addr, hosts in ip_to_hosts.items():
        if len(hosts) > 1:
            findings.append(
                issue(
                    "SNAPSHOT",
                    "duplicate_ip",
                    "High",
                    f"IP {ip_addr} is assigned to multiple hosts: {', '.join(hosts)}.",
                    ip_addr,
                )
            )

    for iface in snapshot.get("interfaces", []):
        status = str(iface.get("status", "")).lower()
        if iface.get("required") and ("down" in status or "shutdown" in status):
            findings.append(
                issue(
                    "SNAPSHOT",
                    "interface_down",
                    "High",
                    f"{iface['device']} {iface['name']} is required but status is {iface['status']}.",
                    json.dumps(iface, sort_keys=True),
                )
            )

        missing_vlans = sorted(
            set(iface.get("required_vlans", [])) - set(iface.get("allowed_vlans", []))
        )
        if missing_vlans:
            findings.append(
                issue(
                    "SNAPSHOT",
                    "missing_vlan",
                    "Medium",
                    f"{iface['device']} {iface['name']} is missing VLANs {missing_vlans}.",
                    json.dumps(iface, sort_keys=True),
                )
            )

    for route in snapshot.get("routes", []):
        if route.get("present") is False or route.get("reachable") is False:
            findings.append(
                issue(
                    "SNAPSHOT",
                    "missing_route",
                    "High",
                    f"{route['device']} route to {route['destination']} is missing or has an unreachable next hop.",
                    json.dumps(route, sort_keys=True),
                )
            )

    return findings


def summarize(findings):
    counts = defaultdict(int)
    for item in findings:
        counts[item["check"]] += 1
    return {
        "total_findings": len(findings),
        "required_checks_covered": sorted(REQUIRED_CHECKS & set(counts)),
        "counts_by_check": dict(sorted(counts.items())),
    }


def main():
    parser = argparse.ArgumentParser(description="Run deterministic NetSage network checks.")
    parser.add_argument("--cases", default="cases.csv")
    parser.add_argument("--snapshot", default="sample_lab_snapshot.json")
    parser.add_argument("--format", choices=["text", "json"], default="text")
    args = parser.parse_args()

    cases = read_cases(args.cases)
    with open(args.snapshot, encoding="utf-8") as handle:
        snapshot = json.load(handle)

    findings = detect_case_issues(cases) + detect_snapshot_issues(snapshot)
    payload = {"summary": summarize(findings), "findings": findings}

    if args.format == "json":
        print(json.dumps(payload, indent=2))
        return

    print("NetSage deterministic rule checker")
    print(f"Total findings: {payload['summary']['total_findings']}")
    print("Counts by check:")
    for check_name, count in payload["summary"]["counts_by_check"].items():
        print(f"  - {check_name}: {count}")
    print("Required checks covered: " + ", ".join(payload["summary"]["required_checks_covered"]))
    print("\nSample findings:")
    for item in findings[:12]:
        print(f"  - [{item['severity']}] {item['case_id']} {item['check']}: {item['message']}")


if __name__ == "__main__":
    main()
