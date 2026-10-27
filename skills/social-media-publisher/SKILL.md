---
name: social-media-publisher
description: "Publish and schedule social media posts to Instagram, TikTok, X (Twitter), Threads, LinkedIn, Facebook Pages, YouTube Shorts and Bluesky from OpenClaw, Hermes, Claude Code or Codex. One post adapted to each network's limits, cross-posted now or scheduled up to 30 days ahead, with a per-network delivery receipt, via the 1Social MCP server (OAuth, no API key). Use to post on social media, cross-post, schedule posts, plan a content calendar, or check what was published."
license: MIT
metadata:
  category: productivity
  openclaw:
    emoji: "📣"
    homepage: "https://1social.dev/mcp?ref=skill"
  hermes:
    tags: ["social-media", "scheduler", "cross-posting", "instagram", "tiktok", "linkedin", "x", "twitter", "threads", "facebook", "youtube", "bluesky"]
    category: social-media
  source:
    repository: 'https://github.com/sultanlive/1social-skills'
    path: skills/social-media-publisher
    ref: main
    commit: efdac26e16e74382cef21ede0501beee48b0371f
---

# Cross-posting with 1Social

1Social publishes one post to every network the user has connected, and reports per network what actually reached it. Your job is to make one idea fit each network's rules.

## Setup (once)

These steps drive the 1Social MCP server. If tools such as `list_accounts` are not available, connect it first. Sign-in is OAuth in the browser; there is no API key to store. Ask the user before running these commands — the login step opens a page where they sign in to 1Social themselves.

- **OpenClaw:** `openclaw mcp set 1social '{"url":"https://mcp.1social.dev/mcp","transport":"streamable-http","auth":"oauth"}'`, then `openclaw mcp login 1social`. Check with `openclaw mcp doctor 1social --probe`.
- **Hermes:** add to `~/.hermes/config.yaml`:
  ```yaml
  mcp_servers:
    1social:
      url: "https://mcp.1social.dev/mcp"
      auth: oauth
  ```
  then `hermes mcp login 1social` (on a headless host: `hermes mcp login 1social --flow device`).
- **Claude Code:** `claude mcp add --transport http 1social https://mcp.1social.dev/mcp`
- **Any other client:** https://1social.dev/mcp lists the setup for each one.

The user needs a 1Social account. New accounts start with a free trial; publishing after it needs a paid plan (https://1social.dev/pricing).

## Workflow

1. **Find the account.** Call `list_accounts`. It returns the connected channels with their ids, each network's live limits, the plan and the remaining monthly quota. If no matching account is connected, tell the user to connect one at https://1social.dev/app — connecting needs a browser and cannot be done from chat. If `list_accounts` reports a limit that differs from this skill, trust `list_accounts`.
2. **Draft for the network.** Write the post to the rules below. A post is a list of `segments`; each segment is `{ text, mediaIds? }`.
3. **Attach media.**
   - The user attached a file in chat → put it in `media`.
   - You have a public https link → put it in `mediaUrls`.
   - You only have a file on disk (OpenClaw, Hermes, Claude Code, Codex or another CLI agent) → call `upload_media` and follow the upload steps its description gives, then put the returned `publicUrl` in `mediaUrls`. A localhost URL never works. Before that, show the user exactly which files you will upload and wait for a yes: an upload gets a public link at once, and declining the post afterwards does not remove the file.
4. **Preview.** Call `preview_post` with the channel ids and the draft. It is free and publishes nothing. Fix every issue it reports and preview again.
5. **Confirm with the user.** Show the final text, the account it goes to, the media, and when it will go out. Publishing is public and some networks cannot take a post down, so wait for a clear yes.
6. **Publish or schedule.** Call `publish_post`. `scheduledAt: null` publishes now; a UTC ISO-8601 timestamp such as `2026-11-03T07:00:00Z` schedules it (in the future, at most 30 days ahead). Convert the user's local time to UTC yourself, and if they name a time without a timezone, ask which one. Set an `idempotencyKey` (a stable string of 8–128 characters for this draft) so a repeated call cannot publish twice.
7. **Report honestly.** The result is a per-network receipt. Report each network exactly as returned. `unknown` means 1Social genuinely could not tell whether the post went out — say so, never call it a success or a failure.

## Adapting one post to several networks

| Network | Text limit | Media | Threads | Delete from 1Social |
|---|---|---|---|---|
| Bluesky | 300 per post | optional | native | yes |
| X (Twitter) | 280 per post | optional, images ≤ 5 MB | native | yes |
| Threads | 500 | optional | joined into one post | no |
| LinkedIn | 3,000 | optional | joined into one post | yes |
| Facebook (Pages) | 63,206 | optional | joined into one post | yes |
| Instagram | 2,200 | **required**, 4:5 to 1.91:1 | joined into one post | no |
| TikTok | 2,200 | **required**, video or JPEG photos | joined into one post | no |
| YouTube Shorts | title 100, description 5,000 bytes | **one vertical video ≤ 3 min** | — | no |

- Pick the channels with the user, then check the strictest limit among them. A 280-character X post and a 3,000-character LinkedIn post are different posts — if the networks differ a lot, offer to publish separate versions as separate posts rather than cutting everything to the shortest limit.
- If any selected network requires media (Instagram, TikTok, YouTube Shorts), ask for it before drafting. YouTube Shorts takes only one vertical video of up to 3 minutes.
- Segments become a native thread on X and Bluesky and are joined into one post everywhere else; preview_post says which will happen per network.
- Instagram, TikTok, Threads and YouTube posts cannot be deleted through 1Social, so confirm with the user before publishing there.

## Content calendars

For a week or month of posts, draft the whole plan first and get the user's approval, then schedule each post with its own `publish_post` call and its own `scheduledAt` (at most 30 days ahead). Check the remaining monthly quota from `list_accounts` before scheduling many posts.

## After publishing

- **Check status:** `list_posts` (give a `postId` for one post). It includes stored engagement metrics where the network reports them.
- **Change a scheduled post:** `update_post`. Only works before the post has gone out.
- **Unschedule:** `cancel_post`. Use this, not `delete_post`, for a post that has not been published.
- **Delete a published post:** `delete_post`, only after the user confirms. Report per network what actually came down: Instagram, TikTok, Threads and YouTube posts stay live and only the user can remove them.
- **A delivery failed:** `retry_delivery` retries one network and spends quota again. It is refused for permanent failures such as a revoked connection — then the user must reconnect at https://1social.dev/app.
- **A delivery is `unknown`:** ask the user to look at the network. Only when they tell you whether the post is live, call `confirm_delivery` with their answer. Never guess, and never `retry_delivery` with `force` without asking — it may publish a second copy.
