# mcp-marketing-postgres-server

A read-only MCP (Model Context Protocol) server exposing structured marketing analytics to AI assistants via PostgreSQL.

## Overview

This project demonstrates how to build a controlled, production-safe MCP server that gives an AI assistant access to a relational database — without exposing arbitrary SQL execution.

All data access is mediated through five predefined tools. The database role is read-only at the PostgreSQL level and enforced again at the session level in Python.

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

```bash
docker compose up --build
```

Connect any MCP-compatible client to the `mcp_server` container via stdio.

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