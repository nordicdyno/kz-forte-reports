# Forte Bank Statement Parser & Reporter

A personal CLI tool for parsing **ForteBank** (Kazakhstan) PDF card statements and generating spending reports grouped by MCC categories.

Drop your monthly PDF statements into the `statements/` folder, run a single command, and get a breakdown of where your money went — by merchant category, spending group, or raw transactions.

## Features

- Parses ForteBank card statement PDFs (table extraction via `pdfplumber`)
- Categorizes transactions using **MCC codes** (Merchant Category Codes)
- Groups spending into high-level categories: Food & Dining, Transport, Shopping, Health & Beauty, Entertainment, Services, Pets
- Tracks **bonus savings** separately from purchases
- Three report types: **raw** transactions, **MCC** breakdown, **group** breakdown
- ASCII table or simple text output
- Sorting by sum, name, or date

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

## Usage

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
