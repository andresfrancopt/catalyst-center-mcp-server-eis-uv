# Catalyst Center MCP Server — Tutorial

A practical guide to understanding the architecture, setting it up, and getting the most out of it with Claude Desktop.

---

## Table of Contents

1. [What Is This?](#1-what-is-this)
2. [Architecture Overview](#2-architecture-overview)
3. [File Structure](#3-file-structure)
4. [How the MCP Protocol Works](#4-how-the-mcp-protocol-works)
5. [Setup Guide](#5-setup-guide)
6. [Tool Reference](#6-tool-reference)
7. [API Explorer](#7-api-explorer)
8. [Multi-Cluster Support](#8-multi-cluster-support)
9. [Local LLM Offloading](#9-local-llm-offloading)
10. [Example Workflows](#10-example-workflows)
11. [Troubleshooting](#11-troubleshooting)

---

## 1. What Is This?

This project implements a **Model Context Protocol (MCP) server** for Cisco Catalyst Center. It allows an AI assistant (Claude Desktop) to interact with your network infrastructure using natural language — querying device inventory, checking compliance, investigating issues, running CLI commands, and exploring the full Catalyst Center API.

**Key idea:** Claude Desktop acts as the conversational interface and reasoning engine. The MCP server is the bridge to your network — it exposes tools that Claude can call to retrieve real data from Catalyst Center, then reason over and present back to you.

You don't write scripts. You ask questions.

---

## 2. Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                        Your Laptop                          │
│                                                             │
│  ┌──────────────────┐   stdio    ┌───────────────────────┐  │
│  │  Claude Desktop  │ ◄────────► │ catalyst_center_      │  │
│  │  (LLM + UI)      │  (MCP)     │ stdio.py              │  │
│  └──────────────────┘            │ (transport wrapper)   │  │
│                                  └──────────┬────────────┘  │
│                                             │ imports        │
│                                  ┌──────────▼────────────┐  │
│                                  │ catalyst_center_      │  │
│                                  │ core.py               │  │
│                                  │ (all tool logic)      │  │
│                                  └──────────┬────────────┘  │
│                                             │ HTTPS          │
└─────────────────────────────────────────────┼───────────────┘
                                              │
                              ┌───────────────▼──────────────┐
                              │   Cisco Catalyst Center       │
                              │   (on-premises)               │
                              │                               │
                              │  ┌──────────┐ ┌───────────┐  │
                              │  │ Portland │ │ San Jose  │  │
                              │  │ cluster  │ │ cluster   │  │
                              │  └──────────┘ └───────────┘  │
                              └──────────────────────────────┘
```

**The flow for every tool call:**
1. You type a question in Claude Desktop
2. Claude identifies which tool(s) to call
3. Claude calls the MCP server via stdio
4. `catalyst_center_core.py` authenticates to Catalyst Center and makes the API call
5. Raw JSON is returned (optionally summarized by a local LLM first)
6. Claude presents the result conversationally

**Internal caching layers** (transparent to the user):

| Cache | Class | TTL | What it stores |
|-------|-------|-----|----------------|
| Auth tokens | `CatalystCenterTokenManager` | 1 hour | JWT per cluster — re-used across calls |
| Inventory | `CatalystInventoryCache` | 10 min | Device UUID↔hostname/IP, site ID↔name, fabric site IDs |
| Embeddings | file on disk | permanent (rebuilt on swagger change) | Semantic vectors for the API Explorer |

The inventory cache is populated automatically on the first `get_network_devices` or `get_sites` call. Subsequent tool calls that need a device UUID or site ID resolve them from cache — no extra API round-trip. Use `invalidate_inventory_cache` to force a refresh if the device inventory has changed.

### Optional: Local LLM for token efficiency

```
catalyst_center_core.py
        │
        │ raw JSON from CC API
        ▼
  ┌─────────────────┐       POST /v1/chat/completions
  │ _maybe_summarize│ ─────────────────────────────────► Local LLM
  │ (if configured) │ ◄─────────────────────────────────  summary
  └─────────────────┘
        │
        │ compact summary (not raw JSON)
        ▼
   Claude Desktop  ← consumes far fewer tokens
```

---

## 3. File Structure

| File | Role |
|------|------|
| `catalyst_center_core.py` | All tool logic, API calls, authentication, embeddings. Never run directly. |
| `catalyst_center_stdio.py` | Thin wrapper — exposes core over stdio for Claude Desktop |
| `catalyst_center_remote.py` | Thin wrapper — exposes core over streamable HTTP (port 8000) |
| `catalyst_center_enhanced_declarative.py` | Legacy shim — deprecated, routes to current core |
| `download_model.py` | One-time setup: downloads the sentence-transformer model locally |
| `environment.env` | All credentials and configuration |
| `Resources/catalyst_config.yaml` | Declarative tool definitions (endpoints, parameters, descriptions) |
| `Resources/catalyst_center_clusters.yaml` | Multi-cluster configuration |
| `Resources/cc_swagger.json` | Full Catalyst Center OpenAPI spec (used by the API explorer) |
| `embeddings_cache/` | Local model and pre-computed API embeddings cache |
| `logs/catalyst_center_mcp.log` | Server log file |

### Why three Python files instead of one?

The architecture separates **logic** from **transport**:

- `_core.py` — knows everything about Catalyst Center, nothing about transport
- `_stdio.py` — knows how to speak MCP over stdin/stdout, nothing about CC
- `_remote.py` — knows how to speak MCP over HTTP, nothing about CC

This means the same tool logic runs identically whether Claude Desktop launches the server locally or connects to it over the network.

---

## 4. How the MCP Protocol Works

MCP (Model Context Protocol) is an open standard that lets LLMs call external tools. When Claude Desktop starts, it launches `catalyst_center_stdio.py` as a subprocess and:

1. Calls `list_tools()` — the server responds with all 26 tool definitions (name, description, input schema)
2. Claude uses these definitions to understand what capabilities are available
3. When you ask a question, Claude decides which tool(s) to invoke
4. Claude calls `call_tool(name, arguments)` — the server executes the real API call and returns results
5. Claude reasons over the results and answers you

**You never see the raw MCP protocol** — Claude Desktop handles it entirely.

---

## 5. Setup Guide

### Step 1 — Install dependencies

```bash
cd network_platforms_mcp_servers
make install
```

### Step 2 — Configure credentials

```bash
make env
# then edit environment.env with CC_URL, CC_USER, CC_PASS
```

### Step 3 — Download the embedding model (one-time)

The API explorer uses a local sentence-transformer model for natural language search.
It runs fully offline after download — no internet required during normal use.

```bash
# Standard network:
make model

# Corporate/lab network with SSL inspection:
uv run python download_model.py --no-ssl-verify
```

The model (~90MB) is saved to `embeddings_cache/model/all-MiniLM-L6-v2/`.

### Step 4 — Configure clusters (optional)

Edit `Resources/catalyst_center_clusters.yaml` to add your Catalyst Center clusters:

```yaml
catalyst_centers:
  - name: "Portland"
    host: "portland-cc.your-domain.com"
    version: "2.3.7.10"
    location: "Portland"
    enabled: true
  - name: "San Jose"
    host: "sanjose-cc.your-domain.com"
    version: "2.3.7.9"
    location: "San Jose"
    enabled: true
```

### Step 5 — Configure your MCP client

**VS Code Copilot** — add to `.vscode/mcp.json` in your project root:

```json
{
  "servers": {
    "catalyst_center": {
      "type": "stdio",
      "command": "${workspaceFolder}/.venv/bin/python3",
      "args": ["${workspaceFolder}/catalyst_center_stdio.py"]
    }
  }
}
```

**Claude Desktop** — add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "catalyst_center": {
      "command": "/path/to/your/.venv/bin/python3",
      "args": ["/path/to/your/catalyst_center_stdio.py"]
    }
  }
}
```

> Your MCP client (VS Code or Claude Desktop) will automatically start and manage the server process — you do not run `catalyst_center_stdio.py` manually.

### Step 6 — Verify (optional)

Smoke-test the server before wiring it to your MCP client:

```bash
make smoke
```

Expected output includes:
- `Successfully loaded N clusters`
- `Loaded config with 22 declarative tools`
- `Sentence transformer model loaded from local path`
- `Built 640 embeddings`
- `Catalyst MCP server ready!`

---

## 6. Tool Reference

Tools are organized into four categories.

### 📊 Inventory (6 tools)

| Tool | What it does |
|------|-------------|
| `get_site_count` | Total number of sites (filter by name or hierarchy) |
| `get_sites` | Site details — areas, buildings, floors with pagination |
| `get_site_topology` | Network topology diagram data for sites |
| `get_network_devices_count` | Count devices (filter by family, role, reachability) |
| `get_network_devices` | Full device list with IP, model, software version |
| `get_compliance_detail` | Compliance status per device (image, profile, config) |

### 🚨 Assurance (6 tools)

| Tool | What it does |
|------|-------------|
| `get_issues_count` | Count active/resolved issues (filter by site, device, priority) |
| `get_issues` | Issue list with priority, category, affected entity |
| `get_issue_details` | Full details + suggested remediation actions for one issue |
| `get_clients_count` | Count connected clients |
| `get_clients` | Client analytics — health score, RSSI, SNR, onboarding time |
| `get_interfaces_count` | Count interfaces across devices |
| `get_device_interfaces` | Per-interface stats: utilization, errors, duplex, speed |

### ⚙️ Operations (7 tools)

| Tool | What it does |
|------|-------------|
| `run_read_only_commands` | Execute CLI commands on devices (show commands only) |
| `get_task_status` | Check if a background task completed successfully |
| `get_task_detail` | Full task result including output file IDs |
| `download_file` | Retrieve a file by ID (e.g. CLI command output) |
| `execute_issue_suggested_actions` | Trigger CC's automated remediation for an issue |
| `get_business_api_execution_results` | Poll async business API operation status |
| `get_config_changes` | Run predefined commands to detect configuration drift |

### 🔧 Administration (4 tools)

| Tool | What it does |
|------|-------------|
| `get_clusters` | List configured clusters and their status |
| `help` | Usage guidance and suggested AI workflows |
| `invalidate_inventory_cache` | Force a refresh of the device/site inventory cache (useful after topology changes) |

### 🔍 API Explorer (4 tools)

See [Section 7](#7-api-explorer).

---

## 7. API Explorer

The 22 declarative tools cover the most common operations, but Catalyst Center has hundreds of API endpoints. The **API Explorer** gives you access to all of them without requiring code changes.

It works in three steps:

### Step 1 — Discover endpoints

```
You: "What APIs are available for wireless RF profiles?"
→ Claude calls: explore_catalyst_api_endpoints(query="wireless RF profiles")
← Server returns: top matching endpoints ranked by cosine similarity
```

The server encodes your query using the `all-MiniLM-L6-v2` sentence-transformer model and compares it against embeddings pre-built from the full 640-endpoint Catalyst Center Swagger spec. Results are ranked by semantic similarity score.

### Step 2 — Inspect an endpoint

```
You: "What parameters does that RF profile endpoint need?"
→ Claude calls: get_catalyst_endpoint_info(path="/dna/intent/api/v1/wireless/rf-profile")
← Server returns: full parameter list, types, required/optional, description
```

### Step 3 — Execute it

```
You: "Get me all RF profiles"
→ Claude calls: execute_catalyst_api_endpoint(path="/dna/intent/api/v1/wireless/rf-profile")
← Server returns: live data from your Catalyst Center
```

**Security note:** The explorer is intentionally restricted to `GET` operations only. POST/PUT/DELETE endpoints are excluded from discovery and execution. Write operations must go through explicitly defined YAML tools.

### Explorer analytics

```
You: "Which explorer endpoints have I been using most?"
→ Claude calls: get_catalyst_explorer_analytics()
← Server returns: call counts, success rates, and candidates for promotion to YAML tools
```

Endpoints you frequently explore are candidates to be added as first-class declarative tools in `catalyst_config.yaml`.

---

## 8. Multi-Cluster Support

Every tool accepts a `cluster` parameter:

| Value | Behaviour |
|-------|-----------|
| *(omitted)* | Uses the first enabled cluster |
| `"Portland"` | Queries only the Portland cluster |
| `"all"` | Queries all enabled clusters and aggregates results |

When `cluster="all"` is used, the server fans out requests in parallel and returns a combined result:

```json
{
  "network_wide_query": true,
  "total_clusters_queried": 2,
  "results": [
    { "cluster_info": { "name": "Portland" }, "data": { ... } },
    { "cluster_info": { "name": "San Jose" }, "data": { ... } }
  ]
}
```

This gives you a single query for network-wide visibility — e.g. finding all non-compliant devices across every site.

### Authentication

Each cluster maintains its own token manager. Tokens are cached and automatically refreshed before expiry — you never need to manually re-authenticate during a session.

---

## 9. Local LLM Offloading

By default the server returns raw JSON from the Catalyst Center API. For large responses (device lists, compliance reports, network-wide queries), this can consume significant Claude tokens.

When `LOCAL_LLM_URL` is set in `environment.env`, the server inserts a summarization step before returning results to Claude:

1. Raw API response is sent to your local LLM (`POST /v1/chat/completions`)
2. The LLM summarizes it into a compact, human-readable format (≤250 words)
3. Claude receives the summary instead of the raw JSON

**This is transparent to you** — Claude's responses look the same, but token usage drops significantly for large datasets.

### Configuration

```bash
LOCAL_LLM_URL=http://192.168.1.10:11434/v1   # Ollama, LM Studio, vLLM, etc.
LOCAL_LLM_API_KEY=none                        # or your key if required
LOCAL_LLM_MODEL=llama3.1:8b                  # any model on your server
```

### Behaviour

- If `LOCAL_LLM_URL` is **not set**: raw JSON returned (default, identical to original behaviour)
- If the local LLM is **unavailable**: falls back to raw JSON silently (logged as warning)
- Responses larger than 12,000 characters are truncated before sending to the LLM
- Summaries include a footer: `_Summarized by local LLM (model-name)._`

### Compatible servers

Any OpenAI-compatible endpoint works: Ollama, LM Studio, vLLM, LocalAI, llama.cpp server, or a self-hosted API proxy.

### Performance benchmark

The table below shows measured results comparing raw JSON vs. LLM-summarized output for three representative use cases (model: `gemini-3.1-flash-lite` running locally):

| Use case | API fetch | Without LLM | With LLM | Output size reduction |
|---|---|---|---|---|
| `get_network_devices` | 512 ms | ~0 ms / 59,062 chars | 2,447 ms / 1,227 chars | **98%** |
| `get_issues` | 1,498 ms | ~0 ms / 104,836 chars | 2,500 ms / 1,476 chars | **99%** |
| `get_compliance_detail` | 298 ms | ~0 ms / 7,009 chars | 2,040 ms / 1,088 chars | **85%** |

**Quality observations:**
- LLM output is structured markdown with counts, affected device names, severity, and concrete CLI remediation steps — directly actionable
- Correctly identifies P1 issues (e.g. LISP fabric route down) and non-compliant devices, including nuances like `FAILED` EOX checks being a Catalyst Center service issue rather than a device problem
- Large responses (>12,000 chars) are truncated before sending to the LLM — for `get_network_devices` this meant only the first ~7 of 28 devices were summarised

**Recommendations:**
- **Enable** local LLM for assurance and compliance queries (`get_issues`, `get_compliance_detail`, `get_clients`) — summaries are high-value and the raw JSON is very large
- **Disable / skip** for inventory queries where you need full UUIDs or a complete device list — raw JSON gives Claude more complete data to reason about

---

## 10. Example Workflows

These are representative conversations showing what you can ask Claude Desktop once the MCP server is connected.

### Network health overview

> "Give me a summary of the current network health across all clusters."

Claude will call `get_issues_count(cluster="all")`, `get_network_devices_count(cluster="all")`, and `get_clients_count(cluster="all")` to build a combined picture.

---

### Find non-compliant devices

> "Which devices are not compliant with the current image policy in Portland?"

```
→ get_compliance_detail(cluster="Portland", complianceType="IMAGE", complianceStatus="NON_COMPLIANT")
```

---

### Investigate a P1 issue

> "Show me all P1 issues and give me the details and suggested fix for the most critical one."

```
→ get_issues(priority="P1", status="active")
→ get_issue_details(issueId="<id from previous result>")
```

---

### Run a CLI command remotely

> "Run 'show ip interface brief' on device 10.62.185.10"

```
→ get_network_devices(managementIpAddress="10.62.185.10")  # get device ID
→ run_read_only_commands(deviceUuid="<id>", commands=["show ip interface brief"])
→ get_task_status(taskId="<id>")
→ download_file(fileId="<id>")
```

Claude handles the multi-step chain automatically.

---

### Detect configuration drift

> "Check if any devices have configuration changes that differ from their golden config."

```
→ get_config_changes(cluster="all")
```

This tool runs a predefined set of commands designed to surface drift.

---

### Explore an unknown API

> "Does Catalyst Center have an API for network path trace? What parameters does it need?"

```
→ explore_catalyst_api_endpoints(query="network path trace")
→ get_catalyst_endpoint_info(path="/dna/intent/api/v1/flow-analysis")
→ execute_catalyst_api_endpoint(path="/dna/intent/api/v1/flow-analysis", parameters={...})
```

---

### Check interface errors on a specific device

> "Show me all interfaces with errors or high utilization on the core switch at 10.10.1.1"

```
→ get_network_devices(managementIpAddress="10.10.1.1")  # get device UUID
→ get_device_interfaces(deviceId="<uuid>")
```

---

### Network-wide client health

> "How many clients are connected network-wide, and are there any with poor health scores?"

```
→ get_clients_count(cluster="all")
→ get_clients(cluster="all")  # includes health scores, RSSI, onboarding time
```

---

## 11. Troubleshooting

### Server fails to start — missing credentials

```
ValueError: Missing required Catalyst Center credentials
```
Check that `CC_URL`, `CC_USER`, and `CC_PASS` are set in `environment.env`.

---

### Embedding model not found

```
No local sentence transformer model found.
```
Run `make model` (or `uv run python download_model.py --no-ssl-verify` on corporate networks). The API Explorer will be unavailable until the model is present, but all 22 declarative tools still work.

---

### SSL errors during model download

```
[SSL: CERTIFICATE_VERIFY_FAILED]
```
Your network performs SSL inspection. Use:
```bash
uv run python download_model.py --no-ssl-verify
```

---

### Claude Desktop doesn't see the tools

1. Check the path to `python3` and `catalyst_center_stdio.py` in `claude_desktop_config.json`
2. Check `logs/catalyst_center_mcp.log` for startup errors
3. Ensure the venv has all dependencies: `make install`

---

### Cluster not found

```
cluster parameter: use get_clusters to see valid names
```
Call `get_clusters` to see exact cluster names, then use those values (case-insensitive).

---

### Local LLM not responding

The server logs a warning and falls back to raw JSON automatically:
```
LLM summarization failed for 'get_network_devices', returning raw JSON: ...
```
Check that `LOCAL_LLM_URL` is reachable and the model is loaded on your LLM server.

---

### First startup is slow

The first run builds embeddings for all 640 Catalyst Center API endpoints from the Swagger spec. This takes ~10–15 seconds. The result is cached to `embeddings_cache/catalyst_embeddings_*.pkl` — subsequent startups load in under a second.
