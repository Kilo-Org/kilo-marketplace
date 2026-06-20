---
metadata:
  category: business-marketing
  source:
    repository: 'https://github.com/yuanjian068yuan/ppxc-find-customers'
    path: skills/ppxc-find-customers
    license_path: LICENSE
name: ppxc-find-customers
description: Use this skill when the user wants to find customer leads from short-video comments, run a trial-first lead scan, analyze public comments, report the search process transparently, query a customer pool, or prepare outreach scripts with OPC 评论线索雷达.
---
# OPC Comment Lead Radar

Use this skill when the user wants to find customers, discover sales leads, analyze short-video comments, generate customer-discovery keywords, review a customer pool, or prepare outreach scripts with OPC 评论线索雷达.

## Product Name

- Call the capability `OPC 评论线索雷达` or `OPC Comment Lead Radar`.
- Do not call it `PPXC backend`, `local backend`, or `PPXC admin`.
- The MCP package is `ppxc-leads-mcp`.

## Core Rule

Do not ask the user to log in to OPC before scanning. Run a trial-first scan from the user's product or service description plus a platform link or keywords, show the first two complete leads, then ask the user to log in only when they want to save, unlock, or review the full lead list.

Being already logged in does not mean the agent should use the saved product list. If the user says "test it", "find customers", "scan comments", or similar, still collect the product or service context and use the trial path. Only use `list_products` when the user explicitly says they want to use a saved product, query the customer pool, save the full list, or continue historical follow-up.

## Trigger Phrases

- find customer leads
- find buyers for my product
- discover customers from comments
- analyze short-video comments
- generate customer-search keywords
- build a lead list
- review my customer pool
- write outreach scripts
- 找客户
- 获客
- 分析评论区
- 小红书获客
- 抖音获客
- 快手获客

## MCP Install

```json
{
  "mcpServers": {
    "ppxc-find-customers": {
      "command": "npx",
      "args": ["-y", "ppxc-leads-mcp"]
    }
  }
}
```

## Startup Check

When the MCP tools are available, first call `get_workflow_manifest` to read the latest backend workflow. If that tool is unavailable, call `check_status_and_login` with the default status action only. Do not pass `action=login_ppxc` during this startup check.

If the MCP tools are not available, help the user add the MCP configuration and enable or trust the connector in their host. After the connector is enabled, return to the trial-first flow.

## Trial-First Workflow

1. Collect minimal context: product or service name, a short description if available, platform, and either a video/note URL or 1 to 3 search keywords.
2. Do not call `check_status_and_login(action=login_ppxc)` before the scan.
3. Do not call `list_products` just because the account is logged in.
4. Do not require a new user to create a product list before searching.
5. If the user gives a URL, call `analyze_video_comments` with `videoUrl` plus `productName` or `productDescription`.
6. If the user gives keywords, call `search_keyword_for_leads` with `keywords`, `platform`, and `productName` or `productDescription`.
7. If the target platform requires login, ask the user to complete the platform login or verification. This is not OPC login.

## Full Mode

Use full mode only when the user asks to save, unlock, query the customer pool, continue previous leads, or use a saved product.

- Then call `check_status_and_login` with `action=login_ppxc` if needed.
- Call `list_products` only for saved-product or customer-pool work.
- Use `suggest_search_keywords` when a real `productId` exists.
- Use `query_leads`, `mark_lead_feedback`, `update_lead_status`, and `review_followup_queue` for customer-pool review and learning.

## Progress Transparency

Before a search, tell the user it may take a few minutes. Newer MCP versions stream progress events to the agent. When the host shows those events, report the concrete facts to the user: which keyword is being searched, which link is being opened, how many comments were read, and which link failed. Do not summarize vaguely as "still running".

When the tool returns, if `processNarrative` is present, report it in 2 to 5 lines before listing leads. If the user asks for more detail, read `workflowTrace.keywords[].contents[]` and explain which content links were inspected and how many comments were analyzed.

## Result Format

Report results in this order:

1. One-sentence verdict from `summary.verdict`.
2. Transparent process summary from `processNarrative` or `workflowTrace`.
3. Top leads: nickname, intent level, need type, and one original comment quote.
4. Paywall status: if `paywall.locked` is true, say the first two complete leads are visible and the remaining leads can be unlocked after login or plan activation.
5. Backup report: if `reportFile` exists, call it a local temporary battle report backup only. Do not describe the local HTML file as the unlock path.
6. Next action: full list, unlock, save, and history live in the OPC web customer pool.

## Feedback Loop

After reporting leads, ask the user whether any lead is accurate, inaccurate, too broad, buyer-like, or passerby-like. Record the judgment with `mark_lead_feedback`.

When the user reports follow-up progress, update lead status with `update_lead_status`: contacted, converted, not converted, or ignored.

## Safety

- Use only public comments and data the user is authorized to process.
- Do not automate private messaging.
- Do not bypass CAPTCHA or platform verification.
- Do not ask the user to paste passwords, verification codes, API keys, cookies, recovery codes, or payment data.
- If the tool returns `VERIFICATION_REQUIRED`, ask the user to complete the visible verification.
- If the tool returns `DAILY_LIMITED`, tell the user the safe daily quota for that platform is used up.
- If the user reports an error, call `export_diagnostics`.

## Official Setup

https://opc1.me/download/mcp
