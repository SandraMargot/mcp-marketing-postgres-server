import json
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types
from mcp_server.db import query

app = Server("marketing-postgres-mcp")


@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="list_campaigns",
            description="Return all campaigns with their channel, status, budget and date range.",
            inputSchema={"type": "object", "properties": {}, "required": []},
        ),
        types.Tool(
            name="get_campaign_summary",
            description="Return aggregated metrics (impressions, clicks, conversions, spend) for a specific campaign.",
            inputSchema={
                "type": "object",
                "properties": {
                    "campaign_id": {"type": "integer", "description": "Campaign ID"}
                },
                "required": ["campaign_id"],
            },
        ),
        types.Tool(
            name="compare_channels",
            description="Compare average CTR and conversion rate across all marketing channels.",
            inputSchema={"type": "object", "properties": {}, "required": []},
        ),
        types.Tool(
            name="detect_underperforming_campaigns",
            description="List campaigns where CTR is below a given threshold (default 2%).",
            inputSchema={
                "type": "object",
                "properties": {
                    "ctr_threshold": {
                        "type": "number",
                        "description": "CTR threshold as a percentage (e.g. 2.0 means 2%). Defaults to 2.0.",
                    }
                },
                "required": [],
            },
        ),
        types.Tool(
            name="get_daily_trend",
            description="Return daily clicks and conversions for a campaign over its full run.",
            inputSchema={
                "type": "object",
                "properties": {
                    "campaign_id": {"type": "integer", "description": "Campaign ID"}
                },
                "required": ["campaign_id"],
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:

    if name == "list_campaigns":
        rows = query(
            """
            SELECT id, name, channel, status, budget_usd,
                   start_date, end_date
            FROM campaigns
            ORDER BY start_date DESC
            """
        )

    elif name == "get_campaign_summary":
        campaign_id = int(arguments["campaign_id"])
        rows = query(
            """
            SELECT
                c.name,
                c.channel,
                c.status,
                SUM(m.impressions)  AS total_impressions,
                SUM(m.clicks)       AS total_clicks,
                SUM(m.conversions)  AS total_conversions,
                ROUND(SUM(m.spend_usd)::numeric, 2) AS total_spend_usd,
                ROUND(
                    100.0 * SUM(m.clicks) / NULLIF(SUM(m.impressions), 0),
                    2
                ) AS ctr_pct,
                ROUND(
                    100.0 * SUM(m.conversions) / NULLIF(SUM(m.clicks), 0),
                    2
                ) AS conversion_rate_pct
            FROM campaigns c
            JOIN daily_metrics m ON m.campaign_id = c.id
            WHERE c.id = %s
            GROUP BY c.name, c.channel, c.status
            """,
            (campaign_id,),
        )

    elif name == "compare_channels":
        rows = query(
            """
            SELECT
                c.channel,
                COUNT(DISTINCT c.id)                    AS campaigns,
                ROUND(
                    100.0 * SUM(m.clicks) / NULLIF(SUM(m.impressions), 0),
                    2
                ) AS avg_ctr_pct,
                ROUND(
                    100.0 * SUM(m.conversions) / NULLIF(SUM(m.clicks), 0),
                    2
                ) AS avg_conversion_rate_pct,
                ROUND(SUM(m.spend_usd)::numeric, 2) AS total_spend_usd
            FROM campaigns c
            JOIN daily_metrics m ON m.campaign_id = c.id
            GROUP BY c.channel
            ORDER BY avg_ctr_pct DESC
            """
        )

    elif name == "detect_underperforming_campaigns":
        threshold = float(arguments.get("ctr_threshold", 2.0))
        rows = query(
            """
            SELECT
                c.id,
                c.name,
                c.channel,
                c.status,
                ROUND(
                    100.0 * SUM(m.clicks) / NULLIF(SUM(m.impressions), 0),
                    2
                ) AS ctr_pct
            FROM campaigns c
            JOIN daily_metrics m ON m.campaign_id = c.id
            GROUP BY c.id, c.name, c.channel, c.status
            HAVING
                100.0 * SUM(m.clicks) / NULLIF(SUM(m.impressions), 0) < %s
            ORDER BY ctr_pct ASC
            """,
            (threshold,),
        )

    elif name == "get_daily_trend":
        campaign_id = int(arguments["campaign_id"])
        rows = query(
            """
            SELECT
                date,
                clicks,
                conversions,
                spend_usd
            FROM daily_metrics
            WHERE campaign_id = %s
            ORDER BY date ASC
            """,
            (campaign_id,),
        )

    else:
        return [types.TextContent(type="text", text=f"Unknown tool: {name}")]

    return [types.TextContent(type="text", text=json.dumps(rows, indent=2, default=str))]


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())