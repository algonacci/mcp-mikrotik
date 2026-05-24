# mcp-mikrotik
MCP server to give clients direct MikroTik RouterOS terminal-style access through a single MCP tool.

## Available Tool

- `mikrotik_terminal`

This tool accepts:
- `host`
- `username`
- `password` (can be an empty string if the router has no password)
- `command`

## Command Examples

```text
/system/resource/print
/ip/service/print
/ip/service/set numbers=telnet disabled=yes
/ip/service/set [find name=telnet] disabled=yes
/interface/disable numbers=ether2
/ip/firewall/filter/add chain=input action=drop comment="Block input"
```

All arguments after the command path must use `key=value` format.

## Run

```bash
python server.py
```
