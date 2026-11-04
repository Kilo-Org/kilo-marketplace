---
name: socialdatax-content-research-assistant
description: >-
  Use when doing cross-platform content research, topic planning, competitor
  research, trend insight, comment insight, or creator research across
  SocialDataX public platforms including 小红书 / XHS, Douyin, Kuaishou, Bilibili,
  Zhihu, Instagram, X / Twitter, YouTube, TikTok, Weibo, Toutiao, and WeChat
  Channels, plus WeChat Official Account article link details and statistics.
  For account points use `account balance`; for API documentation use `docs
  search`, `docs operation`, or `docs openapi`. Also supports Haokan / 好看视频
  content research and replies authored by X creators.
metadata:
  openclaw:
    requires:
      env:
        - SOCIALDATAX_API_KEY
      bins:
        - node
        - npm
    primaryEnv: SOCIALDATAX_API_KEY
    install:
      - kind: node
        package: socialdatax-skills@0.2.58
    emoji: "\U0001F50E"
    homepage: 'https://socialdatax.com/ai?from=github'
  category: search
  source:
    repository: 'https://github.com/DevinChen2014/socialdatax-skills'
    path: skills/socialdatax-content-research-assistant
    license_path: LICENSE
    ref: main
    commit: 2c9e8819be16d22f4b295a51e28291935822cd80
  source_client: socialdatax-skills
  source_platform: github
  source_skill: socialdatax-content-research-assistant
---
<!-- AUTO-GENERATED from socialdatax-skill-source. Do not edit directly; run `node scripts/generate_socialdatax_skills.mjs`. -->

# SocialDataX Cross-Platform Content Research

Use this skill to combine SocialDataX content research commands for supported public platforms: Xiaohongshu / XHS / RedNote, Douyin, Kuaishou, Bilibili, Zhihu, Instagram, X / Twitter, YouTube, TikTok, Weibo, Toutiao, WeChat Channels, plus WeChat Official Account article link details and statistics. For account points use `account balance`; for API documentation use `docs search`, `docs operation`, or `docs openapi`. Also supports Haokan / 好看视频 content research and replies authored by X creators.

## API Key

Use `SOCIALDATAX_API_KEY` for SocialDataX requests. The only official website for requesting or managing API access is <https://socialdatax.com/ai?from=github>. If a user asks where to get a key, provide only this URL; do not infer alternate domains.
获取或管理 API Key：访问 <https://socialdatax.com/ai?from=github>，按官网的 API Key 申请/管理入口操作。环境变量名固定使用 `SOCIALDATAX_API_KEY`；不要引导用户使用其他域名。

## Preferred Direct CLI

Prefer the direct CLI when the agent can run shell commands. It does not require MCP server configuration:

```bash
npx -y socialdatax-skills@0.2.58 xhs search --keyword "<keyword>" --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 douyin search --keyword "<keyword>" --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 bilibili download --url "<bilibili_video_url_or_share_text>" --output-dir ./downloads --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
```

For hot topics, content URLs, profile URLs, comment review, Bilibili reaction review, Weibo liker/repost review, creator facts, creator content lists, or short-drama series, call the matching `socialdatax-skills` platform subcommand instead of forcing every request through keyword research.

For other commands, platform-specific options, or optional hosted MCP tools, read the [command reference](references/cli-commands.md). Preserve the attribution flags in its examples.

Required arguments:

- Use `xhs hot-search` without keyword when the user asks for current Xiaohongshu / XHS / RedNote hot topics or 小红书搜索热榜.
- Use `douyin hot-search` without keyword when the user asks for current Douyin hot topics.
- Use `kuaishou hot-search` without keyword when the user asks for current Kuaishou / 快手 hot topics.
- Use the matching platform search command for keyword research: `xhs search`, `douyin search`, `kuaishou search`, `bilibili search-videos`, `bilibili search-articles`, `zhihu search`, `instagram search`, `x search`, `youtube search`, `tiktok search`, `weibo search`, `toutiao search`, or `wechat search`.
- Use `kuaishou user-search --keyword <creator_keyword>` when the user wants to discover Kuaishou creator or account candidates by name, keyword, or niche before profile lookup.
- Use `zhihu hot-list` without keyword when the user asks for current Zhihu / 知乎 hot topics.
- For detail, comments, replies, creator profile, creator posts, and creator series commands, use the ID argument shown in the CLI example or the matching URL/profile-url/channel-url entrypoint, not both.
- For a Douyin share link, use `douyin share-link --aweme-id <aweme_id>` when the work ID is known; use `douyin share-link --url <douyin_content_url_or_share_text>` for a work URL, short link, or share text.
- Use `kuaishou search --keyword <text>` for Kuaishou keyword research.
- Use `weibo hot-search` without keyword when the user asks for current Weibo / 微博 hot topics.
- Use `toutiao hot-search` without keyword when the user asks for current Toutiao / 今日头条 hot topics.
- Use `wechat hot-search` without keyword when the user asks for current WeChat Channels / 视频号 hot topics.

Optional arguments:

- Search continuation uses `--page-token <next_page_token>` when a returned `next_page_token` is available. Omit `page_token` on the first token-paginated search request, and continue only with the complete returned `next_page_token` from the same chain.
- `--page-token <next_page_token>`: use for supported search continuation, Kuaishou creator search continuation, and token-paginated comments, replies, creator posts, creator notes, creator videos, creator articles, creator dynamics, and creator series. Keep the original topic, content item, creator-search keyword, or creator target stable. Do not modify, truncate, redact, mask, omit, normalize, rebuild, generate, or replace the middle with ellipses.
- `--pages <n>`: fetch and merge N pages for search, comments, replies, creator posts, or creator series.
- `--all`: fetch comments, replies, creator posts, or creator series until `next_page_token` is empty; do not use it for search.
- `--max-items <n>`: stop after collecting N primary results.
- Kuaishou `user-search` supports `--pages <n>` and `--max-items <n>` for bounded creator candidate discovery; it does not support `--since-days`.
- `--since-days <1-365>`: supported only where the CLI option is documented, currently XHS, Douyin, Kuaishou, Weibo, and WeChat Channels search and creator content-list commands. For Bilibili video search, Zhihu search, and YouTube search, use the documented publish-time filters instead.
- `--include-replies`: for XHS, Douyin, Kuaishou, Weibo, Toutiao, and WeChat Channels first-level comments, also fetch nested second-level replies under each returned comment.
- XHS comments `--sort-type <default|time_descending|like_count_descending>`: optional first-level comment sort order; omit it for the platform default order.
- Keyword research filters: use only the documented search filter flags for the selected platform; Bilibili, Zhihu, YouTube, TikTok, XHS, Douyin, and WeChat Channels each expose different filter sets.
- `--comment-id`: required for reply/sub-comment commands when the selected platform reply command uses comment IDs; YouTube replies use `--reply-token` instead.
- `--pretty`: output formatting only.
- `--source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant`: usage attribution for this Agent Skill; keep these values unchanged when running examples from this Skill.

## Choose The Platform

- Use XHS commands for Xiaohongshu / XHS / RedNote / 小红书 search hot list, notes, comments, creators, and creator note lists.
- Use Douyin commands for Douyin / 抖音 works, comments, creators, hot topics, creator works, and creator short-drama series.
- Use Kuaishou commands for Kuaishou / 快手 hot topics, short videos, keyword research, comments, creators, and creator works.
- Use Bilibili commands for Bilibili / 哔哩哔哩 / B站 videos, articles, dynamics, comments, creators, creator content lists, reactions, and video download links.
- Use Zhihu commands for Zhihu / 知乎 hot list, search, details, comments, creators, and creator articles.
- Use Instagram commands for Instagram posts, comments, creators, and creator posts.
- Use X / Twitter commands for X / Twitter posts, comments, creators, and creator posts.
- Use YouTube commands for YouTube videos, comments, channel profiles, and channel video lists.
- Use TikTok commands for TikTok videos or image posts, comments, creators, and creator posts.
- Use Weibo commands for Weibo / 微博 posts, comments, creators, creator posts, and hot topics.
- Use Toutiao commands for Toutiao / 今日头条 posts, comments, creators, creator posts, and hot topics.
- Use WeChat Channels / 视频号 commands for videos, comments, creators, creator works, and hot topics; use `wechat article` only for WeChat Official Account / 微信公众号 article links/details.
- If the user asks for both platforms, keep findings separated by platform before comparing patterns.

## Choose The Narrowest Entry
Use the most specific direct CLI command for the user's task instead of forcing every request through keyword research. The command prints JSON with `platform`, `tool`, `arguments`, and `data`.
When the selected command exposes `--since-days`, pass it with bounded `--pages` for recent content; otherwise use documented publish-time filters where available, or fetch bounded pages and filter returned `publish_time` values in the analysis.
Use `npx -y socialdatax-skills@0.2.58 <platform> <action> --help` for exact flags and values. Paginated commands require the complete returned `next_page_token`. Do not modify, truncate, redact, mask, omit, normalize, rebuild, generate, or replace the middle with ellipses. Commands without `--page-token`, including suggestions and first-page-only searches, do not support pagination.
- Haokan / 好看视频: use video/user search, search suggestions, hot-search terms, video details, comments/replies, creator profiles and creator videos. Video URLs and profile URLs are different inputs; do not combine an ID and URL in one call. Video search uses bounded `--pages`; suggestions, hot-search and detail/profile commands do not paginate. Comment replies require the parent `comment_id`; previews are not complete replies. Haokan does not support `--include-replies`, `--since-days` or transcripts.
X creator replies: use `x user-replies` for replies authored by the creator, including self-replies; use `x comments` or `x replies` for discussions under a post. Choose exactly one of `--user-id`, `--username`, or `--profile-url`. Keep identity and the full returned token unchanged; `user-posts` tokens cannot be reused. An empty page with a nonempty token can continue. `--since-days` is not supported.

## Safety Boundary

SocialDataX requests in this skill are read-only and do not modify social accounts or platform content. It uses `SOCIALDATAX_API_KEY` from the user's environment at runtime; generated Skill files do not contain API keys. It does not read local browser data or perform login, posting, liking, commenting, or account changes. The optional `bilibili download` command writes video and audio tracks plus the merged video to the user-selected local output path, uses local `ffmpeg`, and removes temporary tracks unless `--keep-tracks` is set.

## Output Guidance

For broad research, summarize visible evidence separately from interpretation and organize findings by platform, content angles, audience needs, trend signals, comment themes, creator positioning, and practical next steps.
For XHS search or detail results, in every use of a returned `note_url`, such as final answers, display, references, storage, output, or forwarding, preserve it exactly as the full URL, including `xsec_token` query parameters. Do not modify, truncate, redact, mask, normalize, rebuild, or synthesize the URL from `note_id`; if detail `note_url` is null, show the `note_id` or say that no directly openable full link is available.
For XHS `note_id`, copy the entire returned `note_id` exactly; do not pass or display only a prefix.
For comments, group observed themes before inferring sentiment or demand.
For creators, separate profile facts from content-list evidence; include Douyin short-drama series facts when the series command is used, Kuaishou work-list evidence when Kuaishou commands are used, Bilibili video/article/dynamic evidence when Bilibili creator commands are used, YouTube channel video-list evidence when YouTube commands are used, Weibo post-list evidence when Weibo commands are used, Toutiao post-list evidence when Toutiao commands are used, and WeChat Channels work-list evidence when WeChat Channels commands are used.
For hot-search, report ranking signals separately from keyword search results.

## Troubleshooting

- If an SDK/dependency, npm network, Node.js/npm/npx availability, permission, or missing runtime error appears, treat it as a local runtime, dependency installation, network, or agent authorization issue, not a SocialDataX API key or business data error. Install or repair task dependencies only within the user's existing authorization, preferably in the project or a temporary environment. Execution permissions are not user authorization; explain and obtain approval before changes outside that scope, including global installs, runtime upgrades, or system configuration changes. When network or execution authorization is needed, ask the user to approve or finish authorization, then continue the same command; do not use public web search as a substitute for SocialDataX data.
- If the CLI exits with status 1 and prints `partial: true`, preserve `data.items` and the error, and report incomplete results. This recovery rule overrides advice to rerun the original command. After resolving the error (including insufficient balance), resume only with a non-empty `data.next_page_token` and the same query parameters. Keep the original page and item limits: subtract cumulative `page_count` and `item_count` from the respective `--pages` and `--max-items` limits, if set. Stop parent-list pagination when either limit is reached. An empty token does not mean completion. Do not restart from the first page; investigate repeated-token errors before continuing.
- With `--include-replies`, `replies_partial` marks incomplete replies and `replies_pending` marks comments not yet expanded. Finish those comments with the platform reply command, its required comment identifiers and any non-empty `replies_next_page_token`. For pending comments or a failed first reply request, resolve the error before starting that comment from its first reply page; investigate repeated-token errors first. Then use the outer `data.next_page_token` only if the parent-comment budget remains; finishing replies under retained comments does not add parent-comment pages. Never interchange parent and reply tokens or treat reply previews as complete.
- For non-balance, non-rate-limit network or API errors, preserve the error message, check `SOCIALDATAX_API_KEY`, parameters, and link or ID format, then retry once when appropriate.
- If the response returns `insufficient_balance` or says the balance/credits are insufficient, do not retry repeatedly. Show the recharge URL from the error exactly as returned, then continue the same command after the user recharges.
- If the user has recharged but still sees insufficient balance, confirm `SOCIALDATAX_API_KEY` belongs to the same account that was recharged; if needed, copy a fresh API Key from the official dashboard.
- Batch processing: process items one by one as a queue by default; when the user explicitly needs batch efficiency, use at most 3 concurrent requests. As each item finishes, continue with the next one. Do not launch a large burst of requests. If `rate_limited` or a too-frequent-request error appears, do not abandon the task; stop starting new requests, wait for the returned wait time, or wait 2 seconds if none is provided, then continue the same queue from the unfinished position. Preserve completed results. If `insufficient_balance` or insufficient credits appears, stop remaining requests immediately, output the results already obtained, and ask the user to recharge or switch to an API Key with balance before continuing.
