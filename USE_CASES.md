# Catalyst Center MCP Server — Use Cases

A reference catalogue of things you can ask the Catalyst Center MCP server, validated against a live environment. Each entry includes a sample natural-language prompt, the tools involved, and what you can expect in the response.

---

## Quick Reference

| Category | Use Cases |
|---|---|
| 🏗️ Inventory & Discovery | 4 — devices, sites, SDA fabric, device lookup |
| 🔍 Assurance & Health | 7 — network health, client health, interfaces, issues |
| 🔧 Configuration & Compliance | 4 — drift detection, audit, archive, change history |
| ⚙️ Operations & CLI | 4 — CLI exec, routing diagnostics, issue remediation, path trace |
| 📦 Software & Licensing | 2 — SWIM images, license summary |
| 📡 Wireless | 2 — SSIDs, rogue AP containment |
| 🖥️ Platform & Administration | 3 — version, clusters, API explorer |

---

## Table of Contents

1. [Inventory & Discovery](#1-inventory--discovery)
2. [Assurance & Health](#2-assurance--health)
3. [Configuration & Compliance](#3-configuration--compliance)
4. [Operations & CLI Execution](#4-operations--cli-execution)
5. [Software & Licensing](#5-software--licensing)
6. [Wireless](#6-wireless)
7. [Platform & Administration](#7-platform--administration)

---

## 1. Inventory & Discovery

### List all network devices

> "List all devices in the inventory."

```
→ get_network_devices()
```

Returns hostname, management IP, device family, role, reachability status, and software version for every managed device.

---

### Count and browse sites

> "How many sites are in the inventory?"

```
→ get_site_count()
→ get_sites()             # for full site details
→ get_site_topology()     # for physical hierarchy
```

Returns the total count and a breakdown of areas, buildings, and floors across the network hierarchy.

---

### Explore the SDA fabric topology

> "Show me all SDA fabric sites and which devices are in each fabric."

```
→ execute_catalyst_api_endpoint(path="/dna/intent/api/v1/sda/fabricSites")
→ execute_catalyst_api_endpoint(path="/dna/intent/api/v1/sda/fabricDevices", parameters={"fabricId": "<id>"})
```

Returns fabric site IDs, authentication profiles, Pub/Sub status, and the list of devices per fabric. Roles include border, edge, and map-server.

---

### Look up a specific device

> "Get details for the device at 192.168.255.2."

```
→ get_network_devices(managementAddress="192.168.255.2")
```

Returns the device UUID, model, IOS-XE version, uptime, reachability, and management state — useful as a first step before running CLI commands.

---

## 2. Assurance & Health

### Overall network health score

> "What is the overall health of my network right now?"

```
→ execute_catalyst_api_endpoint(path="/dna/intent/api/v1/network-health")
```

Returns a global health score (0–100) broken down by device category: Access, Distribution, Core, Router, AP, and WLC. Identifies how many devices are Healthy, Fair, Bad, or have No Data.

---

### Client health overview

> "How healthy are my wired and wireless clients?"

```
→ execute_catalyst_api_endpoint(path="/dna/intent/api/v1/client-health")
```

Returns per-type health scores (Wired / Wireless), total client counts, and a breakdown of Good / Fair / Poor / Idle clients. Also reports whether clients use randomised MAC addresses.

---

### Detailed client analytics

> "What is the health of the client at 192.168.40.10? Show me RSSI, data rate, and onboarding time."

```
→ get_clients(ipv4Address="192.168.40.10")
→ get_clients(macAddress="aa:bb:cc:dd:ee:ff")
```

Returns signal strength (RSSI/SNR), negotiated data rate, roaming history, onboarding duration, and per-client health score.

---

### Client count across the network

> "How many clients are connected network-wide right now?"

```
→ get_clients_count()
→ get_clients_count(siteId="<id>")    # scoped to a specific site
```

---

### Interface statistics for a device

> "Show all interfaces with errors or high utilisation on the core switch."

```
→ get_network_devices(managementAddress="<ip>")   # get device UUID
→ get_device_interfaces(deviceId="<uuid>")
```

Returns RX/TX rates, error counters, discard counts, and operational status per interface.

---

### Active issues list

> "Show me all active P1 and P2 issues."

```
→ get_issues(status="active", priority="P1", limit=25)
→ get_issues_count(status="active")
```

Returns issue name, severity, affected device and site, first/last occurrence time, and number of events.

---

### Issue details and remediation steps

> "What is the root cause and fix for issue ID X?"

```
→ get_issue_details(id="<issue-id>")
```

Returns the full description, root cause classification, affected device UUIDs, and a list of suggested CLI commands to diagnose and resolve the issue.

---

## 3. Configuration & Compliance

### Identify devices with config drift

> "Which devices have configuration drift right now?"

```
→ get_compliance_detail(complianceType="RUNNING_CONFIG", complianceStatus="NON_COMPLIANT")
```

Returns device UUIDs and remediation-supported flags for every device where the running config deviates from the intended state (golden config).

---

### Full compliance audit for a device

> "Is device KCSS-EMEA-SDW-RTR compliant across IMAGE, PSIRT, and RUNNING_CONFIG?"

```
→ get_network_devices(managementAddress="<ip>")   # get device UUID
→ execute_catalyst_api_endpoint(path="/dna/intent/api/v1/compliance/<uuid>/detail")
```

Returns pass/fail status across all compliance categories: IMAGE, PSIRT, RUNNING_CONFIG, NETWORK_SETTINGS, and EOX.

---

### Configuration archive history

> "Show the configuration archive history for the FUSION switch."

```
→ get_network_devices(managementAddress="192.168.255.2")
→ execute_catalyst_api_endpoint(path="/dna/intent/api/v1/network-device-config", parameters={"deviceId": "<uuid>"})
```

Returns all archived snapshots with IN_SYNC/OUT_OF_SYNC status, the source of each change (console, VTY, or out-of-band), and the user who made the change.

---

### Detect recent configuration changes

> "What configuration changes happened on these devices recently?"

```
→ get_config_changes(deviceUuids=["<uuid1>", "<uuid2>"])
```

Runs a predefined set of diagnostic commands and returns change logs, login/logout events, and out-of-band activity per device.

---

## 4. Operations & CLI Execution

### Run a read-only CLI command on a device

> "Run 'show ip interface brief | exc una' on the FUSION device."

```
→ get_network_devices(managementAddress="192.168.255.2")    # get UUID
→ run_read_only_commands(deviceUuids=["<uuid>"], commands=["show ip interface brief | exc una"])
→ get_task_detail(taskId="<id>")
→ download_file(fileId="<id>")
```

Executes any read-only IOS/IOS-XE command via Catalyst Center's Command Runner API. Supports multiple devices in parallel.

---

### Run routing and protocol diagnostics

> "Check OSPF neighbours and BGP summary on the border routers."

```
→ get_network_devices()     # filter by role=BORDER_ROUTER
→ run_read_only_commands(deviceUuids=["<uuid1>", "<uuid2>"], commands=[
    "show ip ospf neighbor",
    "show ip bgp summary",
    "show ip route summary"
  ])
```

---

### Execute issue suggested actions

> "Run the Catalyst Center suggested remediation steps for issue ID X."

```
→ execute_issue_suggested_actions(entity_type="issue_id", entity_value="<issue-id>")
```

Automatically executes Catalyst Center's built-in suggested diagnostic commands for the specified issue and returns the results.

---

### Generative troubleshooting flow

> "Run a full investigation on the P1 fabric default route issue."

The server has a built-in AI troubleshooting flow that chains:

```
→ get_issues(status="active")
→ get_site_topology()
→ get_issue_details(id="<id>")
→ execute_issue_suggested_actions(entity_type="issue_id", entity_value="<id>")
→ get_config_changes(deviceUuids=["<affected-devices>"])
→ run_read_only_commands()   # baseline, config, routing, protocol batches
```

---

### Network path trace

> "Does Catalyst Center have an API for network path trace? What parameters does it need?"

```
→ explore_catalyst_api_endpoints(query="network path trace")
→ get_catalyst_endpoint_info(path="/dna/intent/api/v1/flow-analysis")
→ execute_catalyst_api_endpoint(path="/dna/intent/api/v1/flow-analysis", parameters={...})
```

Retrieves existing path trace sessions or triggers a new flow analysis between a source and destination IP.

---

## 5. Software & Licensing

### List available software images

> "What IOS-XE images are available for upgrade? Which ones are Cisco-recommended?"

```
→ execute_catalyst_api_endpoint(path="/dna/intent/api/v1/images")
```

Returns all imported images and Cisco.com-recommended versions, including golden-image status, image type (SMU, APSP, full), and device family compatibility.

---

### Device license summary

> "Show the license summary for all devices — which ones are using DNA Advantage vs Essentials?"

```
→ execute_catalyst_api_endpoint(path="/dna/intent/api/v1/licenses/device/summary", parameters={"sortOrder": "asc"})
→ execute_catalyst_api_endpoint(path="/dna/intent/api/v1/licenses/device/<uuid>/details")
```

Returns per-device license tier, registration status, and compliance state.

---

## 6. Wireless

### List SSIDs configured at a site

> "What SSIDs are configured at the London site?"

```
→ get_sites(name="London")                          # get siteId
→ execute_catalyst_api_endpoint(path="/dna/intent/api/v1/sites/<siteId>/wirelessSettings/ssids")
```

Returns all SSIDs at the site including security profile, band settings, and VLAN assignment.

---

### Check rogue AP containment status

> "Is the rogue AP with MAC AA:BB:CC:DD:EE:FF contained?"

```
→ execute_catalyst_api_endpoint(path="/dna/intent/api/v1/security/rogue/wireless-containment/status/AA:BB:CC:DD:EE:FF")
```

Returns containment status, which WLC is containing it, and per-BSSID containment details.

---

## 7. Platform & Administration

### Catalyst Center version and installed packages

> "What version is Catalyst Center running? What packages are installed?"

```
→ execute_catalyst_api_endpoint(path="/dna/intent/api/v1/dnac-release")
→ execute_catalyst_api_endpoint(path="/dna/intent/api/v1/dnac-packages")
```

Returns the system version, internal build number, and all 47 installed packages with their individual versions.

---

### List available clusters

> "How many Catalyst Center clusters are configured in this MCP server?"

```
→ get_clusters()
```

Returns cluster names, hosts, and connection status for all configured Catalyst Center instances.

---

### Explore unknown API endpoints

> "Is there an API for network bugs or PSIRT advisories?"

```
→ explore_catalyst_api_endpoints(query="network bugs PSIRT security advisory")
→ get_catalyst_endpoint_info(path="<discovered-path>")
```

The API Explorer uses semantic search over 640+ Catalyst Center endpoints from the official Swagger spec. Use it to discover capabilities not covered by the named tools.

---

> **Tip:** For any use case above, you can add `cluster="Portland"` (or any named cluster) to scope results to a specific Catalyst Center instance. Use `cluster="all"` for network-wide aggregated results across all clusters.
