#!/usr/bin/env python3
"""
server.py

MCP server for multi-site-monitor. This is the first tool going in —
get_site_economics. list_sites, get_pagespeed_report, get_gsc_data, and
get_ga4_data get added to this same file as they're built in later steps.

Requires: pip install mcp
"""

import json
import os
import sys

from mcp.server.mcpserver import MCPServer

CONFIG_FILE = "config.json"

mcp = MCPServer("multi-site-monitor")


def load_config() -> dict:
    if not os.path.exists(CONFIG_FILE):
        sys.exit(
            f"Missing {CONFIG_FILE}. Copy config.json.example to {CONFIG_FILE} "
            "and fill in your site details."
        )
    with open(CONFIG_FILE) as f:
        return json.load(f)


@mcp.tool()
def get_site_economics(site: str) -> dict:
    """
    Return the monthly cost, revenue, and profit/loss for a given site,
    plus any notes. Site must be one of the sites listed under
    site_economics in config.json (aireadypage, tracycarpetcare,
    hypicsmodapk).
    """
    config = load_config()
    economics = config.get("site_economics", {})

    if site not in economics:
        return {
            "error": f"No economics data for '{site}'. Known sites: {list(economics.keys())}"
        }

    data = economics[site]
    cost = data.get("monthly_cost", 0)
    revenue = data.get("monthly_revenue", 0)

    return {
        "site": site,
        "monthly_cost": cost,
        "monthly_revenue": revenue,
        "monthly_profit": round(revenue - cost, 2),
        "notes": data.get("notes", ""),
    }


if __name__ == "__main__":
    mcp.run()
