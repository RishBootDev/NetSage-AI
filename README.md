# NetSage AI

AI-assisted troubleshooting helper for Cisco-style Packet Tracer lab problems. It reads symptoms, topology notes, and show-command evidence, proposes a likely diagnosis, runs deterministic rule checks, and keeps a human reviewer in the approval loop.

## What is included

- `cases.csv` - 30 network troubleshooting cases across VLAN, DHCP, DNS, routing, ACL, NAT, wireless, and security issues.
- `prompts/diagnose_prompt.md` - JSON-only diagnosis prompt with worked examples.
- `prompts/human_review_prompt.md` - reviewer prompt for accepting, editing, or rejecting AI output.
- `src/rule_checker.py` - deterministic checks for duplicate IPs, wrong masks, gateway mismatch, interface down, missing VLANs, and missing routes.
- `src/diagnose_cases.py` - local AI-style diagnosis runner that writes responses and human review records.
- `src/build_dashboard.py` - dashboard generator.
- `sample_lab_snapshot.json` - sample structured lab facts used by the checker.
- `ai_responses.csv`, `review_log.csv`, `responsible_ai_log.md`, `sample_checker_output.txt`, and `dashboard.html` - generated project evidence.
- `demo_walkthrough.md` - 5 to 10 minute demo video script and checklist.

## Run the project

Use Python 3.10+ from the project folder:

```powershell
python src\rule_checker.py --cases cases.csv --snapshot sample_lab_snapshot.json
python src\diagnose_cases.py --cases cases.csv --out ai_responses.csv --review-out review_log.csv --responsible-out responsible_ai_log.md
python src\build_dashboard.py --cases cases.csv --reviews review_log.csv --responses ai_responses.csv --out dashboard.html
```

Open `dashboard.html` in a browser to view issue coverage, severity, AI/human agreement, and a demo case.

## Human review policy

NetSage never auto-applies fixes. Every diagnosis must be marked:

- `Accepted` when the AI root cause and action are correct.
- `Edited` when the diagnosis is close but needs a safer or more precise correction.
- `Rejected` when the AI diagnosis is misleading or unsupported by the evidence.

The reviewer record is the final authority for fixes and verification.
