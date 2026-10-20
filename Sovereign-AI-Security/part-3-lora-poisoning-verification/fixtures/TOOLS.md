# Declarative Workspace Tool Whitelist (`TOOLS.md`)
- **Enforcement Layer**: OpenClaw Zero-Trust Runtime Gatekeeper
- **Policy**: Explicit Whitelist (Deny All by Default)

## Approved Tools

### `read_local_markdown`
- **Description**: Reads markdown file contents strictly from local workspace vault.
- **Parameters**:
  - `filepath`: string (Required. Relative path within `/workspace/vault/`)

### `query_local_vector_db`
- **Description**: Queries local SQLite vector index without network access.
- **Parameters**:
  - `query_vector`: list of float (Required. 1536-dimensional embedding)
  - `top_k`: integer (Required. Maximum 10 results)

### `format_markdown_report`
- **Description**: Formats analytical findings into compliant markdown report.
- **Parameters**:
  - `content`: string (Required. Markdown text payload)
  - `destination`: string (Required. Target output path)

---

## Prohibited System Operations
Any model output attempting to invoke the following will trip the zero-trust exception handler:
- Shell execution binaries: `curl`, `wget`, `nc`, `netcat`, `nslookup`, `dig`, `bash`, `sh`, `powershell`
- Socket redirects: `/dev/tcp`, `/dev/udp`
- Destructive file commands: `rm -rf`, `del /f`
