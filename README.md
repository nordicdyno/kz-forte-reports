# Forte Bank Statement Parser & Reporter

A personal tool for parsing **ForteBank** (Kazakhstan) PDF card statements and generating spending reports grouped by MCC categories — available as a CLI and as an **MCP server** for AI agents.

Drop your monthly PDF statements into the `statements/` folder, then either run the CLI or let an AI agent analyze your spending via MCP.

## Features

- Parses ForteBank card statement PDFs (table extraction via `pdfplumber`)
- Categorizes transactions using **MCC codes** (Merchant Category Codes)
- Groups spending into high-level categories: Food & Dining, Transport, Shopping, Health & Beauty, Entertainment, Services, Pets
- Tracks **bonus savings** separately from purchases
- Three report types: **raw** transactions, **MCC** breakdown, **group** breakdown
- ASCII table or simple text output
- Sorting by sum, name, or date
- **MCP server** for integration with AI coding agents

## Project Structure

```
budged/                  # Shared Python library
  __init__.py
  categories.py          # MCC code mappings and spending groups
  parser.py              # PDF parsing and transaction extraction
  aggregator.py          # Spending aggregation by MCC/group
  formatter.py           # ASCII table and text report rendering
reporter.py              # CLI entry point
mcp_server.py            # MCP server entry point
tests/
tools/forte_generator.py # Test PDF generator
```

## Prerequisites

Install [mise](https://mise.jdx.dev/) — a polyglot dev tool manager that handles Python, uv, and task running:

```bash
curl https://mise.run | sh
```

Then activate it in your shell (follow the [getting started guide](https://mise.jdx.dev/getting-started.html) for your shell).

## Quick Start

```bash
git clone <repo-url> && cd budged && mise trust

# mise reads mise.toml and installs Python 3.13 + uv automatically
mise install

# place your ForteBank PDF statements into the statements/ directory
cp ~/Downloads/statement_january.pdf statements/

# run the parser
mise run forte-parse
```

## CLI Usage

### Parse statements

```bash
mise run forte-parse
```

This parses all `*.pdf` files in `statements/` and prints a **group breakdown** as an ASCII table by default.

Pass extra arguments after `--`:

```bash
# raw transaction list sorted by date
mise run forte-parse -- --report raw --sort date

# MCC-level breakdown in simple text format
mise run forte-parse -- --report mcc --format simple

# group breakdown sorted by name
mise run forte-parse -- --report group --sort name
```

#### Options

| Flag               | Values                | Default        | Description                               |
|--------------------|-----------------------|----------------|-------------------------------------------|
| `--report`         | `raw`, `mcc`, `group` | `group`        | Report type                               |
| `--sort`           | `sum`, `name`, `date` | `sum`          | Sort order (`date` only applies to `raw`) |
| `--format`         | `ascii`, `simple`     | `ascii`        | Output format                             |
| `--statements-dir` | path                  | `./statements` | Directory with PDF files                  |

### Run tests

```bash
mise run test
```

---

## MCP Server

The MCP server exposes the same parsing and analytics as the CLI, letting AI agents work with your bank statements conversationally.

### Available Tools

| Tool                       | Description                                                       |
|----------------------------|-------------------------------------------------------------------|
| `list_statements`          | List PDF files in a directory (default: `./statements`)           |
| `parse_invoice`            | Parse a PDF and return all transactions as structured JSON        |
| `spending_summary`         | Get categorized spending breakdown (by group or MCC)              |
| `raw_transactions_report`  | Get a formatted table of all individual transactions              |
| `get_categories`           | Return the MCC code and category group definitions                |

### Running the MCP Server Standalone

```bash
# via mise
mise run mcp

# or directly
uv run python mcp_server.py
```

This starts an stdio-based MCP server that any compatible client can connect to.

---

## Connecting to AI Agents

### Claude Code

Add to your project's `.mcp.json` (create it in the project root if it doesn't exist):

```json
{
  "mcpServers": {
    "budged": {
      "command": "uv",
      "args": ["run", "--directory", "/absolute/path/to/budged", "python", "mcp_server.py"]
    }
  }
}
```

Replace `/absolute/path/to/budged` with the actual path to this project.

Then just ask Claude Code things like:
- *"List my bank statements"*
- *"Parse the January statement and show me where I spent the most"*
- *"Give me a spending breakdown by category for statement_january.pdf"*

### Cursor

Add to `.cursor/mcp.json` in your home directory or project root:

```json
{
  "mcpServers": {
    "budged": {
      "command": "uv",
      "args": ["run", "--directory", "/absolute/path/to/budged", "python", "mcp_server.py"]
    }
  }
}
```

The tools will appear in Cursor's agent mode automatically.

### Claude Desktop

Open **Settings → Developer → Edit Config** and add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "budged": {
      "command": "uv",
      "args": ["run", "--directory", "/absolute/path/to/budged", "python", "mcp_server.py"]
    }
  }
}
```

Restart Claude Desktop. The budged tools will be available in conversation.

### Cline (VS Code)

Open Cline's MCP settings (`Cline → MCP Servers → Configure`) and add:

```json
{
  "mcpServers": {
    "budged": {
      "command": "uv",
      "args": ["run", "--directory", "/absolute/path/to/budged", "python", "mcp_server.py"]
    }
  }
}
```

### Continue.dev

Add to your `~/.continue/config.yaml`:

```yaml
mcpServers:
  - name: budged
    command: uv
    args:
      - run
      - --directory
      - /absolute/path/to/budged
      - python
      - mcp_server.py
```

### Any MCP-Compatible Client (Generic stdio)

The server uses **stdio transport** by default. Launch it as a subprocess and communicate via stdin/stdout using the [MCP protocol](https://modelcontextprotocol.io/):

```bash
uv run --directory /absolute/path/to/budged python mcp_server.py
```

### Testing with MCP Inspector

You can test the tools interactively with the official MCP Inspector:

```bash
cd /path/to/budged
npx -y @modelcontextprotocol/inspector uv run python mcp_server.py
```

This opens a web UI where you can call each tool and inspect the results.

---

## Example Conversations with an Agent

Once connected, you can ask your AI agent:

> **You:** List my bank statements.
>
> **Agent:** *(calls `list_statements`)* You have 2 PDF statements in `./statements/`:
> - statement_january.pdf
> - statement_february.pdf

> **You:** Show me a spending breakdown for January.
>
> **Agent:** *(calls `spending_summary` with `pdf_path="statements/statement_january.pdf"`)* Here's your January spending by category:
> - Food & Dining: -9,190.00 KZT
> - Shopping: -34,290.00 KZT
> - Transport: -7,800.00 KZT
> - ...

> **You:** What were my largest individual purchases?
>
> **Agent:** *(calls `parse_invoice`)* Your top purchases were:
> 1. Technodom (Department Stores): -15,000 KZT on Jan 27
> 2. ZARA (Clothing): -8,900 KZT on Jan 24
> 3. ...
