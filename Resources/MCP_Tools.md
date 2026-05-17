# MCP Tools Catalog

Complete catalog of currently available tools in this repository.

## Totals

- **Catalyst Center tools:** `26` (`22` declarative + `4` explorer)

## Cisco Catalyst Center Tools

### Declarative Tools (`22`)

| # | Tool | Category | Description |
|---|---|---|---|
| 1 | `get_site_count` | inventory | Get total count of sites across the network |
| 2 | `get_sites` | inventory | Get detailed site information |
| 3 | `get_site_topology` | inventory | Get network topology for sites |
| 4 | `get_network_devices_count` | inventory | Get total count of network devices |
| 5 | `get_network_devices` | inventory | Get detailed network device information |
| 6 | `get_compliance_detail` | inventory | Get device compliance status and details |
| 7 | `get_issues_count` | assurance | Get total count of issues |
| 8 | `get_issues` | assurance | Get issue details for selected filters |
| 9 | `get_issue_details` | assurance | Get full details for an issue ID |
| 10 | `get_clients_count` | assurance | Get total count of clients |
| 11 | `get_clients` | assurance | Get detailed client analytics and health data |
| 12 | `get_interfaces_count` | assurance | Get total count of interfaces |
| 13 | `get_device_interfaces` | assurance | Get interface statistics for a device |
| 14 | `run_read_only_commands` | operations | Execute read-only CLI commands on devices |
| 15 | `get_task_status` | operations | Get status of a specific task |
| 16 | `get_task_detail` | operations | Get detailed task information and results |
| 17 | `download_file` | operations | Download files by ID |
| 18 | `execute_issue_suggested_actions` | operations | Execute suggested actions for an issue |
| 19 | `get_business_api_execution_results` | operations | Get business API execution status by ID |
| 20 | `get_config_changes` | operations | Run predefined commands to identify config changes |
| 21 | `get_clusters` | administration | List available Catalyst Center clusters |
| 22 | `help` | administration | Usage guidance and AI flow suggestions |

### Explorer / Dynamic API Tools (`4`, GET-only execution)

| # | Tool | Description |
|---|---|---|
| 23 | `explore_catalyst_api_endpoints` | Search endpoints by natural language |
| 24 | `execute_catalyst_api_endpoint` | Execute dynamic endpoint calls (**GET-only**) |
| 25 | `get_catalyst_endpoint_info` | Get endpoint details and parameters |
| 26 | `get_catalyst_explorer_analytics` | View explorer usage and success analytics |

## Key Usage Notes

### Catalyst Center

- Use `cluster='all'` when you need network-wide visibility.
- Run `get_clusters` first to discover valid cluster names.
- Use `get_config_changes` for predefined drift checks (commands auto-selected).
- Use `run_read_only_commands` for custom CLI diagnostics.
- For uncovered APIs, use: `explore_*` -> `get_*_endpoint_info` -> `execute_*_api_endpoint`.