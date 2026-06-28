"""MCP server exposing claim-history tools (same contract as prod Oracle views)."""

from __future__ import annotations

import asyncio

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

from mcp_server.stores.factory import get_claim_store

server = Server("claim-history")


@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="get_claim_summary",
            description="Medicare classifier features for a claim (V_CLAIM_SUMMARY_FOR_AI)",
            inputSchema={
                "type": "object",
                "properties": {"claim_id": {"type": "string"}},
                "required": ["claim_id"],
            },
        ),
        Tool(
            name="get_payment_summary",
            description="Payment summary for a claim (V_PAYMENT_SUMMARY_FOR_AI)",
            inputSchema={
                "type": "object",
                "properties": {"claim_id": {"type": "string"}},
                "required": ["claim_id"],
            },
        ),
        Tool(
            name="get_reserve_context",
            description="Reserve model features (V_RESERVE_CONTEXT_FOR_AI)",
            inputSchema={
                "type": "object",
                "properties": {"claim_id": {"type": "string"}},
                "required": ["claim_id"],
            },
        ),
        Tool(
            name="get_claimant_context",
            description="Aggregated claimant history, no raw PHI (V_CLAIMANT_CONTEXT_FOR_AI)",
            inputSchema={
                "type": "object",
                "properties": {"claim_id": {"type": "string"}},
                "required": ["claim_id"],
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    store = get_claim_store()
    claim_id = arguments["claim_id"]
    if name == "get_claim_summary":
        data = store.get_claim_summary(claim_id)
    elif name == "get_payment_summary":
        data = store.get_payment_summary(claim_id)
    elif name == "get_reserve_context":
        data = store.get_reserve_context(claim_id)
    elif name == "get_claimant_context":
        data = store.get_claimant_context(claim_id)
    else:
        raise ValueError(f"Unknown tool: {name}")
    return [TextContent(type="text", text=str(data))]


async def main() -> None:
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
