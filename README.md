# Controlled AI Access to Marketing Data via MCP

A read-only MCP (Model Context Protocol) server exposing structured marketing analytics to AI assistants via PostgreSQL.

## Overview

This server gives an AI assistant structured, read-only access to a marketing 
analytics database — campaigns, audiences, conversions — without exposing a 
raw SQL interface.

The core design question is: how do you let an LLM query production data 
without trusting it to write safe SQL? The answer here is to never expose SQL 
at all. The model calls named tools with typed parameters; the server handles 
the queries. The PostgreSQL role is read-only, and Python enforces the same 
constraint at session level — so there is no bypass path through the model.

Data access is scoped to five explicit tools covering the most common 
analytics workflows: campaign performance, channel comparison, trend analysis, 
and anomaly detection.

## Demo
Checking the MCP server is available before querying:

<img src="docs/screenshots/MCP_Claude_connector.png" width="450"/>

Claude calling the MCP tools and returning a structured analysis on the data given:

<img src="docs/screenshots/MCP_claude_answer.png" width="450"/>

## Stack

| Component | Technology |
|-----------|-----------|
| MCP server | Python 3.12 + MCP Python SDK |
| Database | PostgreSQL 16 |
| Orchestration | Docker Compose |
| Data | Synthetic dataset generated at init |

## MCP Tools

| Tool | Description |
|------|-------------|
| `list_campaigns` | All campaigns with channel, status and budget |
| `get_campaign_summary` | Aggregated KPIs for a given campaign |
| `compare_channels` | CTR and conversion rate by channel |
| `detect_underperforming_campaigns` | Campaigns below a CTR threshold |
| `get_daily_trend` | Daily clicks and conversions for a campaign |

## Security Design

- No arbitrary SQL exposed to the LLM
- PostgreSQL role with `SELECT` only
- Session-level `default_transaction_read_only=on`
- All queries are parameterised (no string interpolation)

## Quick Start

**Prerequisites:** Docker >= 24 and Docker Compose v2

```bash
docker compose up --build
```

This spins up a PostgreSQL 16 instance pre-loaded with synthetic data, 
and the MCP server on top of it.

To verify the data is loaded:

```bash
docker exec marketing_db psql -U analyst -d marketing -c "SELECT name, channel, status FROM campaigns;"
```

The MCP server communicates over **stdio** — connect any compatible client 
(Claude Desktop, custom stdio client) to the `mcp_server` container.

To verify both containers are running:
```bash
docker compose ps
```

## Project Structure

```
├── db/
│   └── init.sql          # Schema + synthetic data
├── mcp_server/
│   ├── db.py             # Database connection layer
│   └── server.py         # MCP tools definition
├── docker-compose.yml
├── Dockerfile
└── requirements.txt
```
## File Reference

| File | Role |
|---|---|
| `docker-compose.yml` | Orchestrates PostgreSQL and the MCP server |
| `db/init.sql` | Schema + 6 campaigns + ~400 rows of daily metrics |
| `mcp_server/db.py` | Read-only connection layer with parameterised queries |
| `mcp_server/server.py` | 5 predefined MCP tools — no arbitrary SQL exposed |
| `Dockerfile` | Minimal Python image |
| `README.md` | Documentation |