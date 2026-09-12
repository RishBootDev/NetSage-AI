# Responsible AI Log

Every NetSage diagnosis requires human approval. The cases below document where the AI-style output was corrected before acceptance.

## NET-003 - Edited

- AI answer: Upstream DNS server unreachable
- Human correction: DNS service disabled or unavailable for the client subnet gateway.
- Why it changed: AI focused on reachability but missed the configuration evidence showing DNS is not active.
- Approved next command: show running-config | include name-server

## NET-007 - Edited

- AI answer: Guest Wi-Fi VLAN mapped to the wrong SSID
- Human correction: Guest VLAN ACL is overly permissive and allows access to internal servers.
- Why it changed: The SSID mapping was not proven; the ACL line is direct evidence.
- Approved next command: show access-lists GUEST_ACL

## NET-014 - Edited

- AI answer: DHCP server pool exhausted
- Human correction: Missing ip helper-address on the branch gateway interface.
- Why it changed: AI reused a common DHCP answer even though relay evidence points to the router interface.
- Approved next command: show ip dhcp binding

## NET-018 - Rejected

- AI answer: Wireless signal interference causing authentication failures
- Human correction: RADIUS shared secret mismatch.
- Why it changed: The diagnosis ignored the explicit incorrect_secret_key evidence.
- Approved next command: show wlan summary

## NET-021 - Edited

- AI answer: EIGRP neighbor down
- Human correction: OSPF redistribution is missing the subnets keyword.
- Why it changed: The case is about route redistribution, not neighbor formation.
- Approved next command: show ip ospf neighbor

## NET-024 - Rejected

- AI answer: Trunk encapsulation mismatch
- Human correction: VTP domain name mismatch.
- Why it changed: AI selected a Layer 2 trunking issue but the evidence shows a VTP domain mismatch.
- Approved next command: show vtp status
