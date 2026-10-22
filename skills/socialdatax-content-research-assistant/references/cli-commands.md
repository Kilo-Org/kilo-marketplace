# Command and MCP reference

<!-- AUTO-GENERATED from socialdatax-skill-source. Do not edit directly; run `node scripts/generate_socialdatax_skills.mjs`. -->

Current platform support:

- Xiaohongshu / XHS / RedNote search hot list through `xhs_get_search_hot_list`.
- Douyin / 抖音 hot-search through `douyin_get_hot_search_list`.
- Kuaishou / 快手 hot-search through `kuaishou_get_hot_search_list`.
- Zhihu / 知乎 hot list through `zhihu_get_hot_list`.
- Weibo / 微博 hot-search through `weibo_get_hot_search_list`.
- Toutiao / 今日头条 hot-search through `toutiao_get_hot_search_list`.
- WeChat Channels / 视频号 hot-search through `wechat_get_hot_search_list`.
- Xiaohongshu / XHS / RedNote notes through `xhs_search_notes`.
- Douyin / 抖音 works, including video and image/text posts, through `douyin_search_videos`.
- Kuaishou / 快手 works and short videos through `kuaishou_search_videos`.
- Bilibili / 哔哩哔哩 / B站 videos and articles through `bilibili_search_videos` and `bilibili_search_articles`.
- Zhihu / 知乎 answers, articles, and videos through `zhihu_search_content`.
- Instagram posts through `instagram_search_posts`.
- X / Twitter posts through `x_search_posts`.
- YouTube videos through `youtube_search_videos`.
- TikTok videos and image posts through `tiktok_search_posts`.
- Weibo / 微博 posts through `weibo_search_posts`.
- Toutiao / 今日头条 posts through `toutiao_search_posts`.
- WeChat Channels / 视频号 videos through `wechat_search_videos`.
- Xiaohongshu / XHS / RedNote notes through the `xhs_get_note_detail_by_*` tools.
- Douyin / 抖音 works, including video and image/text posts, through the `douyin_get_video_detail_by_*` tools.
- Kuaishou / 快手 works through the `kuaishou_get_video_detail_by_*` tools.
- Bilibili / 哔哩哔哩 / B站 videos, articles, and dynamics through the `bilibili_get_content_detail_by_*` tools.
- Zhihu / 知乎 answers, articles, and videos through `zhihu_get_content_detail_by_url`.
- Instagram posts through the `instagram_get_post_detail_by_*` tools.
- X / Twitter posts through the `x_get_post_detail_by_*` tools.
- YouTube videos through `youtube_get_video_detail_by_url`.
- TikTok videos and image posts through `tiktok_get_post_detail_by_url`.
- Weibo / 微博 posts through the `weibo_get_post_detail_by_*` tools.
- Toutiao / 今日头条 posts through the `toutiao_get_post_detail_by_*` tools.
- WeChat Channels / 视频号 video and image-post details through the `wechat_get_video_detail_by_*` tools.
- WeChat Official Account / 微信公众号 articles through `wechat_get_mp_article_detail_by_url` and `wechat_get_mp_article_stats_by_url`.
- Xiaohongshu / XHS / RedNote notes through the `xhs_get_note_comments_by_*` and `xhs_get_note_sub_comments_by_comment_id` tools.
- Douyin / 抖音 works, including video and image/text posts, through the `douyin_get_video_comments_by_*` and `douyin_get_video_comment_replies_by_comment_id` tools.
- Kuaishou / 快手 works through the `kuaishou_get_video_comments_by_*` and `kuaishou_get_video_comment_replies_by_comment_id` tools.
- Bilibili / 哔哩哔哩 / B站 comments through the `bilibili_get_content_comments_by_*` and `bilibili_get_content_comment_replies_by_comment_id` tools.
- Zhihu / 知乎 comments through `zhihu_get_content_comments_by_url` and `zhihu_get_comment_replies_by_url`.
- Instagram comments through `instagram_get_post_comments_by_post_url` and `instagram_get_post_comment_replies_by_comment_id`.
- X / Twitter comments through the `x_get_post_comments_by_*` and `x_get_post_comment_replies_by_comment_id` tools.
- YouTube comments through `youtube_get_video_comments_by_url` and `youtube_get_video_comment_replies`.
- TikTok comments through the `tiktok_get_post_comments_by_*` and `tiktok_get_post_comment_replies` tools.
- Weibo / 微博 posts through the `weibo_get_post_comments_by_*` and `weibo_get_post_comment_replies_by_comment_id` tools.
- Toutiao / 今日头条 posts through the `toutiao_get_post_comments_by_*` and `toutiao_get_post_comment_replies_by_comment_id` tools.
- WeChat Channels / 视频号 videos through the `wechat_get_video_comments_by_*` and `wechat_get_video_comment_replies_by_comment_id` tools.
- Xiaohongshu / XHS / RedNote creators through the `xhs_get_user_info_by_*` tools.
- Douyin / 抖音 creators through the `douyin_get_user_info_by_*` tools.
- Kuaishou / 快手 creators through the `kuaishou_get_user_info_by_*` tools.
- Kuaishou / 快手 creator discovery through `kuaishou_search_users` before profile lookup when only an account keyword or niche is known.
- Bilibili / 哔哩哔哩 / B站 creators through the `bilibili_get_user_info_by_*` tools.
- Zhihu / 知乎 creators through `zhihu_get_user_info_by_profile_url`.
- Instagram creators through the `instagram_get_user_info_by_*` tools.
- X / Twitter creators through the `x_get_user_info_by_*` tools.
- YouTube channels through `youtube_get_channel_info_by_url`.
- TikTok creators through the `tiktok_get_user_info_by_*` tools.
- Weibo / 微博 creators through the `weibo_get_user_info_by_*` tools.
- Toutiao / 今日头条 creators through the `toutiao_get_user_info_by_*` tools.
- WeChat Channels / 视频号 creators through `wechat_get_user_info_by_url` for video or image-post links or share text, or `wechat_get_user_info_by_user_id` when a `v2_...@finder` user_id is already known.
- Xiaohongshu / XHS / RedNote creator notes through the `xhs_get_user_posted_notes_by_*` tools.
- Douyin / 抖音 creator works, including video and image/text posts, through the `douyin_get_user_posted_videos_by_*` tools.
- Douyin / 抖音 creator short-drama series through the `douyin_get_user_series_by_*` tools.
- Kuaishou / 快手 creator works through the `kuaishou_get_user_posted_videos_by_*` tools.
- Bilibili / 哔哩哔哩 / B站 creator videos, articles, and dynamics through the `bilibili_get_user_posted_*` tools.
- Zhihu / 知乎 creator articles through `zhihu_get_user_posted_articles_by_profile_url`.
- Instagram creator posts through the `instagram_get_user_posts_by_*` tools.
- X / Twitter creator posts through the `x_get_user_posts_by_*` tools.
- YouTube channel videos and Shorts through `youtube_get_user_posted_videos_by_channel_url`.
- TikTok creator posts through the `tiktok_get_user_posts_by_*` tools.
- Weibo / 微博 creator posts through the `weibo_get_user_posts_by_*` tools.
- Toutiao / 今日头条 creator posts through the `toutiao_get_user_posts_by_*` tools, optionally filtered by `content_type` (`all`, `article`, `video`, or `micro_post`).
- WeChat Channels / 视频号 creator videos and image posts through the `wechat_get_user_posted_videos_by_*` tools; the user_id entrypoint requires a `v2_...@finder` user_id.
- Haokan / 好看视频 video discovery, details, comments/replies, creator profiles and creator videos; X creator-authored replies via `x user-replies`.

## Preferred Direct CLI

Prefer the direct CLI when the agent can run shell commands. It does not require MCP server configuration:

```bash
npx -y socialdatax-skills@0.2.58 xhs hot-search --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 xhs search --keyword "<keyword>" --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 xhs search --keyword "<keyword>" --pages 3 --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 xhs detail --note-id "<note_id>" --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 xhs comments --note-id "<note_id>" --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 xhs comments --note-id "<note_id>" --all --include-replies --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 xhs user-info --user-id "<user_id>" --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 xhs user-posts --user-id "<user_id>" --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 xhs user-posts --user-id "<user_id>" --all --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 douyin hot-search --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 douyin search --keyword "<keyword>" --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 douyin search --keyword "<keyword>" --pages 3 --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 douyin detail --aweme-id "<aweme_id>" --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 douyin comments --aweme-id "<aweme_id>" --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 douyin comments --aweme-id "<aweme_id>" --all --include-replies --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 douyin user-info --sec-user-id "<sec_user_id>" --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 douyin user-posts --sec-user-id "<sec_user_id>" --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 douyin user-posts --sec-user-id "<sec_user_id>" --all --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 kuaishou hot-search --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 kuaishou search --keyword "<keyword>" --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 kuaishou search --keyword "<keyword>" --pages 3 --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 kuaishou user-search --keyword "<creator_keyword>" --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 kuaishou detail --photo-id "<photo_id>" --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 kuaishou comments --photo-id "<photo_id>" --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 kuaishou comments --photo-id "<photo_id>" --all --include-replies --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 kuaishou user-info --user-id "<user_id>" --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 kuaishou user-posts --user-id "<user_id>" --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 kuaishou user-posts --user-id "<user_id>" --all --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 bilibili search-videos --keyword "<keyword>" --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 bilibili search-articles --keyword "<keyword>" --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 bilibili detail --content-id "<content_id>" --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 bilibili comments --content-id "<content_id>" --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 bilibili user-info --user-id "<user_id>" --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 bilibili user-videos --user-id "<user_id>" --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 bilibili user-articles --user-id "<user_id>" --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 bilibili user-dynamics --user-id "<user_id>" --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 zhihu hot-list --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 zhihu search --keyword "<keyword>" --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 zhihu search --keyword "<keyword>" --pages 3 --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 zhihu detail --content-url "<zhihu_content_url_or_share_text>" --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 zhihu comments --content-url "<zhihu_content_url_or_share_text>" --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 zhihu user-info --profile-url "<profile_url_or_share_text>" --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 zhihu user-posts --profile-url "<profile_url_or_share_text>" --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 zhihu user-posts --profile-url "<profile_url_or_share_text>" --all --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 instagram search --keyword "<keyword>" --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 instagram search --keyword "<keyword>" --pages 3 --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 instagram detail --post-id "<post_id>" --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 instagram comments --post-url "<instagram_post_url_or_share_text>" --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 instagram user-info --username "<username>" --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 instagram user-posts --username "<username>" --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 instagram user-posts --username "<username>" --all --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 x search --keyword "<keyword>" --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 x search --keyword "<keyword>" --pages 3 --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 x detail --post-id "<post_id>" --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 x comments --post-id "<post_id>" --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 x user-info --username "<username>" --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 x user-posts --username "<username>" --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 x user-posts --username "<username>" --all --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 youtube search --keyword "<keyword>" --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 youtube search --keyword "<keyword>" --pages 3 --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 youtube detail --url "<youtube_video_url>" --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 youtube comments --url "<youtube_video_url>" --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 youtube channel-info --channel-url "<youtube_channel_url>" --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 youtube user-posts --channel-url "<youtube_channel_url>" --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 youtube user-posts --channel-url "<youtube_channel_url>" --all --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 tiktok search --keyword "<keyword>" --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 tiktok search --keyword "<keyword>" --pages 3 --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 tiktok detail --url "<tiktok_post_url_or_share_text>" --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 tiktok comments --post-id "<post_id>" --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 tiktok user-info --tiktok-id "<tiktok_id>" --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 tiktok user-posts --tiktok-id "<tiktok_id>" --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 tiktok user-posts --tiktok-id "<tiktok_id>" --all --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 weibo hot-search --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 weibo search --keyword "<keyword>" --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 weibo search --keyword "<keyword>" --pages 3 --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 weibo detail --post-id "<post_id>" --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 weibo comments --post-id "<post_id>" --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 weibo comments --post-id "<post_id>" --all --include-replies --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 weibo user-info --user-id "<user_id>" --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 weibo user-posts --user-id "<user_id>" --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 weibo user-posts --user-id "<user_id>" --all --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 toutiao hot-search --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 toutiao search --keyword "<keyword>" --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 toutiao search --keyword "<keyword>" --pages 3 --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 toutiao detail --post-id "<post_id>" --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 toutiao comments --post-id "<post_id>" --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 toutiao comments --post-id "<post_id>" --all --include-replies --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 toutiao user-info --user-id "<user_id>" --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 toutiao user-posts --user-id "<user_id>" --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 toutiao user-posts --user-id "<user_id>" --all --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 wechat hot-search --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 wechat search --keyword "<keyword>" --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 wechat search --keyword "<keyword>" --pages 3 --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 wechat detail --encrypted-object-id "<encrypted_object_id>" --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 wechat comments --object-id "<object_id>" --object-nonce-id "<object_nonce_id>" --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 wechat comments --object-id "<object_id>" --object-nonce-id "<object_nonce_id>" --all --include-replies --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 wechat user-info --user-id "<v2_finder_user_id>" --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 wechat user-posts --user-id "<v2_finder_user_id>" --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 wechat user-posts --user-id "<v2_finder_user_id>" --all --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 xhs detail --url "<note_url_or_share_text>" --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 xhs comments --url "<note_url_or_share_text>" --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 xhs user-info --profile-url "<profile_url_or_share_text>" --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 xhs user-posts --profile-url "<profile_url_or_share_text>" --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 douyin detail --url "<douyin_content_url_or_share_text>" --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 douyin share-link --aweme-id "<aweme_id>" --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 douyin share-link --url "<douyin_content_url_or_share_text>" --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 douyin comments --url "<douyin_content_url_or_share_text>" --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 douyin user-info --profile-url "<profile_url_or_share_text>" --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 douyin user-posts --profile-url "<profile_url_or_share_text>" --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 douyin user-series --sec-user-id "<sec_user_id>" --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 douyin user-series --sec-user-id "<sec_user_id>" --all --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 douyin user-series --profile-url "<profile_url_or_share_text>" --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 xhs sub-comments --note-id "<note_id>" --comment-id "<comment_id>" --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 douyin replies --aweme-id "<aweme_id>" --comment-id "<comment_id>" --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 kuaishou user-search --keyword "<creator_keyword>" --pages 3 --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 kuaishou detail --url "<kuaishou_content_url_or_share_text>" --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 kuaishou comments --url "<kuaishou_content_url_or_share_text>" --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 kuaishou user-info --profile-url "<profile_url_or_share_text>" --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 kuaishou user-posts --profile-url "<profile_url_or_share_text>" --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 kuaishou replies --photo-id "<photo_id>" --comment-id "<comment_id>" --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 bilibili detail --url "<bilibili_content_url_or_share_text>" --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 bilibili comments --url "<bilibili_content_url_or_share_text>" --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 bilibili replies --comment-object-id "<comment_object_id>" --comment-object-type "<comment_object_type_integer>" --comment-id "<comment_id>" --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 bilibili reactions --post-id "<post_id>" --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 bilibili reactions --url "<bilibili_opus_or_dynamic_url_or_share_text>" --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 bilibili user-info --profile-url "<profile_url_or_share_text>" --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 bilibili user-videos --profile-url "<profile_url_or_share_text>" --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 bilibili user-articles --profile-url "<profile_url_or_share_text>" --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 bilibili user-dynamics --profile-url "<profile_url_or_share_text>" --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 bilibili download --url "<bilibili_video_url_or_share_text>" --output-dir ./downloads --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 zhihu replies --content-url "<zhihu_content_url_or_share_text>" --comment-id "<comment_id>" --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 instagram detail --post-url "<instagram_post_url_or_share_text>" --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 instagram replies --post-id "<post_id>" --comment-id "<comment_id>" --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 instagram user-info --profile-url "<profile_url_or_share_text>" --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 instagram user-posts --profile-url "<profile_url_or_share_text>" --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 x detail --post-url "<x_post_url_or_share_text>" --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 x comments --post-url "<x_post_url_or_share_text>" --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 x replies --post-id "<post_id>" --comment-id "<comment_id>" --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 x user-info --user-id "<user_id>" --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 x user-info --profile-url "<profile_url_or_share_text>" --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 x user-posts --user-id "<user_id>" --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 x user-posts --profile-url "<profile_url_or_share_text>" --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 youtube replies --reply-token "<reply_token>" --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 tiktok comments --url "<tiktok_post_url_or_share_text>" --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 tiktok replies --post-id "<post_id>" --comment-id "<comment_id>" --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 tiktok user-info --profile-url "<profile_url_or_share_text>" --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 tiktok user-posts --profile-url "<profile_url_or_share_text>" --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 weibo detail --post-url "<weibo_post_url_or_share_text>" --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 weibo comments --post-url "<weibo_post_url_or_share_text>" --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 weibo likers --post-id "<post_id>" --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 weibo reposts --post-id "<post_id>" --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 weibo user-info --profile-url "<profile_url>" --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 weibo user-posts --profile-url "<profile_url>" --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 weibo replies --post-id "<post_id>" --comment-id "<comment_id>" --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 toutiao detail --url "<toutiao_content_url_or_share_text>" --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 toutiao comments --url "<toutiao_content_url_or_share_text>" --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 toutiao user-info --profile-url "<profile_url_or_share_text>" --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 toutiao user-posts --profile-url "<profile_url_or_share_text>" --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 toutiao replies --comment-id "<comment_id>" --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 wechat detail --url "<wechat_work_url_or_share_text>" --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 wechat article --url "<mp_article_url_or_share_text>" --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 wechat article-stats --url "<mp_article_url_or_share_text>" --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 wechat comments --url "<wechat_video_url_or_share_text>" --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 wechat user-info --url "<wechat_work_url_or_share_text>" --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 wechat user-posts --url "<wechat_work_url_or_share_text>" --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 wechat replies --object-id "<object_id>" --object-nonce-id "<object_nonce_id>" --comment-id "<comment_id>" --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 xhs search --keyword "<keyword>" --since-days 7 --pages 2 --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 douyin search --keyword "<keyword>" --since-days 7 --pages 2 --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 kuaishou search --keyword "<keyword>" --since-days 7 --pages 2 --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 weibo search --keyword "<keyword>" --since-days 7 --pages 2 --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 wechat search --keyword "<keyword>" --since-days 7 --pages 2 --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 xhs user-posts --user-id "<user_id>" --since-days 30 --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 douyin user-posts --sec-user-id "<sec_user_id>" --since-days 30 --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 kuaishou user-posts --user-id "<user_id>" --since-days 30 --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 weibo user-posts --user-id "<user_id>" --since-days 30 --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 wechat user-posts --user-id "<v2_finder_user_id>" --since-days 30 --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 account balance --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 docs search --query "<query>" --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 docs operation --operation-id "<operation_id>" --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 docs openapi --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 douyin user-search --keyword "<keyword>" --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 douyin user-info --douyin-id "<douyin_id>" --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 weibo likers --url "<post_url>" --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 weibo reposts --url "<post_url>" --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 xhs search-suggestions --keyword "<keyword>" --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 xhs user-search --keyword "<keyword>" --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 xhs product-search --keyword "<keyword>" --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 xhs product-detail --sku-id "<sku_id>" --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 xhs product-detail --url "<url>" --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 xhs product-reviews --sku-id "<sku_id>" --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 xhs product-review-replies --review-id "<review_id>" --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 xhs product-review-reply-replies --review-id "<review_id>" --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 xhs topic-notes --url "<topic_url>" --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 xhs topic-notes --page-id "<page_id>" --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 douyin product-search --keyword "<keyword>" --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 douyin product-detail --product-id "<product_id>" --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 douyin product-detail --url "<url>" --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 wechat share-link --object-id "<object_id>" --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 haokan search --keyword "<keyword>" --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 haokan user-search --keyword "<keyword>" --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 haokan search-suggestions --keyword "<keyword>" --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 haokan hot-search --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 haokan detail --video-id "<video_id>" --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 haokan detail --url "<video_url>" --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 haokan comments --video-id "<video_id>" --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 haokan comments --url "<video_url>" --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 haokan replies --video-id "<video_id>" --comment-id "<comment_id>" --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 haokan replies --url "<video_url>" --comment-id "<comment_id>" --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 haokan user-info --user-id "<user_id>" --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 haokan user-info --profile-url "<profile_url>" --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 haokan user-posts --user-id "<user_id>" --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 haokan user-posts --profile-url "<profile_url>" --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 x user-replies --user-id "<user_id>" --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 x user-replies --username "<username>" --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
npx -y socialdatax-skills@0.2.58 x user-replies --profile-url "<profile_url>" --pretty --source-client socialdatax-skills --source-platform github --source-skill socialdatax-content-research-assistant
```

## MCP Tools

MCP tools matching the direct CLI commands above:

- XHS: `xhs_get_search_hot_list`, `xhs_search_notes`, `xhs_get_note_detail_by_note_id`, `xhs_get_note_comments_by_note_id`, `xhs_get_user_info_by_user_id`, `xhs_get_user_posted_notes_by_user_id`, `xhs_get_note_detail_by_note_url`, `xhs_get_note_comments_by_note_url`, `xhs_get_user_info_by_profile_url`, `xhs_get_user_posted_notes_by_profile_url`, `xhs_get_note_sub_comments_by_comment_id`, `xhs_search_suggestions`, `xhs_search_users`, `xhs_search_products`, `xhs_get_product_detail_by_sku_id`, `xhs_get_product_detail_by_url`, `xhs_get_product_reviews`, `xhs_get_product_review_replies`, `xhs_get_product_review_reply_replies`, `xhs_get_topic_notes_by_topic_url`, `xhs_get_topic_notes_by_page_id`
- DOUYIN: `douyin_get_hot_search_list`, `douyin_search_videos`, `douyin_get_video_detail_by_aweme_id`, `douyin_get_video_comments_by_aweme_id`, `douyin_get_user_info_by_sec_user_id`, `douyin_get_user_posted_videos_by_sec_user_id`, `douyin_get_video_detail_by_url`, `douyin_get_video_share_link_by_aweme_id`, `douyin_get_video_share_link_by_url`, `douyin_get_video_comments_by_url`, `douyin_get_user_info_by_profile_url`, `douyin_get_user_posted_videos_by_profile_url`, `douyin_get_user_series_by_sec_user_id`, `douyin_get_user_series_by_profile_url`, `douyin_get_video_comment_replies_by_comment_id`, `douyin_search_users`, `douyin_get_user_info_by_douyin_id`, `douyin_search_products`, `douyin_get_product_detail_by_product_id`, `douyin_get_product_detail_by_url`
- KUAISHOU: `kuaishou_get_hot_search_list`, `kuaishou_search_videos`, `kuaishou_search_users`, `kuaishou_get_video_detail_by_photo_id`, `kuaishou_get_video_comments_by_photo_id`, `kuaishou_get_user_info_by_user_id`, `kuaishou_get_user_posted_videos_by_user_id`, `kuaishou_get_video_detail_by_url`, `kuaishou_get_video_comments_by_url`, `kuaishou_get_user_info_by_profile_url`, `kuaishou_get_user_posted_videos_by_profile_url`, `kuaishou_get_video_comment_replies_by_comment_id`
- BILIBILI: `bilibili_search_videos`, `bilibili_search_articles`, `bilibili_get_content_detail_by_id`, `bilibili_get_content_comments_by_id`, `bilibili_get_user_info_by_user_id`, `bilibili_get_user_posted_videos_by_user_id`, `bilibili_get_user_posted_articles_by_user_id`, `bilibili_get_user_posted_dynamics_by_user_id`, `bilibili_get_content_detail_by_url`, `bilibili_get_content_comments_by_url`, `bilibili_get_content_comment_replies_by_comment_id`, `bilibili_get_content_likes_and_reposts_by_post_id`, `bilibili_get_content_likes_and_reposts_by_url`, `bilibili_get_user_info_by_profile_url`, `bilibili_get_user_posted_videos_by_profile_url`, `bilibili_get_user_posted_articles_by_profile_url`, `bilibili_get_user_posted_dynamics_by_profile_url`, `bilibili_get_video_download_links`
- ZHIHU: `zhihu_get_hot_list`, `zhihu_search_content`, `zhihu_get_content_detail_by_url`, `zhihu_get_content_comments_by_url`, `zhihu_get_user_info_by_profile_url`, `zhihu_get_user_posted_articles_by_profile_url`, `zhihu_get_comment_replies_by_url`
- INSTAGRAM: `instagram_search_posts`, `instagram_get_post_detail_by_post_id`, `instagram_get_post_comments_by_post_url`, `instagram_get_user_info_by_username`, `instagram_get_user_posts_by_username`, `instagram_get_post_detail_by_post_url`, `instagram_get_post_comment_replies_by_comment_id`, `instagram_get_user_info_by_profile_url`, `instagram_get_user_posts_by_profile_url`
- X: `x_search_posts`, `x_get_post_detail_by_post_id`, `x_get_post_comments_by_post_id`, `x_get_user_info_by_username`, `x_get_user_posts_by_username`, `x_get_post_detail_by_post_url`, `x_get_post_comments_by_post_url`, `x_get_post_comment_replies_by_comment_id`, `x_get_user_info_by_user_id`, `x_get_user_info_by_profile_url`, `x_get_user_posts_by_user_id`, `x_get_user_posts_by_profile_url`, `x_get_user_replies_by_user_id`, `x_get_user_replies_by_username`, `x_get_user_replies_by_profile_url`
- YOUTUBE: `youtube_search_videos`, `youtube_get_video_detail_by_url`, `youtube_get_video_comments_by_url`, `youtube_get_channel_info_by_url`, `youtube_get_user_posted_videos_by_channel_url`, `youtube_get_video_comment_replies`
- TIKTOK: `tiktok_search_posts`, `tiktok_get_post_detail_by_url`, `tiktok_get_post_comments_by_post_id`, `tiktok_get_user_info_by_tiktok_id`, `tiktok_get_user_posts_by_tiktok_id`, `tiktok_get_post_comments_by_url`, `tiktok_get_post_comment_replies`, `tiktok_get_user_info_by_profile_url`, `tiktok_get_user_posts_by_profile_url`
- WEIBO: `weibo_get_hot_search_list`, `weibo_search_posts`, `weibo_get_post_detail_by_post_id`, `weibo_get_post_comments_by_post_id`, `weibo_get_user_info_by_user_id`, `weibo_get_user_posts_by_user_id`, `weibo_get_post_detail_by_post_url`, `weibo_get_post_comments_by_post_url`, `weibo_get_post_liker_list_by_post_id`, `weibo_get_post_repost_list_by_post_id`, `weibo_get_user_info_by_profile_url`, `weibo_get_user_posts_by_profile_url`, `weibo_get_post_comment_replies_by_comment_id`, `weibo_get_post_liker_list_by_post_url`, `weibo_get_post_repost_list_by_post_url`
- TOUTIAO: `toutiao_get_hot_search_list`, `toutiao_search_posts`, `toutiao_get_post_detail_by_post_id`, `toutiao_get_post_comments_by_post_id`, `toutiao_get_user_info_by_user_id`, `toutiao_get_user_posts_by_user_id`, `toutiao_get_post_detail_by_url`, `toutiao_get_post_comments_by_url`, `toutiao_get_user_info_by_profile_url`, `toutiao_get_user_posts_by_profile_url`, `toutiao_get_post_comment_replies_by_comment_id`
- WECHAT: `wechat_get_hot_search_list`, `wechat_search_videos`, `wechat_get_video_detail_by_encrypted_object_id`, `wechat_get_video_comments_by_object_id`, `wechat_get_user_info_by_user_id`, `wechat_get_user_posted_videos_by_user_id`, `wechat_get_video_detail_by_url`, `wechat_get_mp_article_detail_by_url`, `wechat_get_mp_article_stats_by_url`, `wechat_get_video_comments_by_url`, `wechat_get_user_info_by_url`, `wechat_get_user_posted_videos_by_url`, `wechat_get_video_comment_replies_by_comment_id`, `wechat_get_video_share_url_by_object_id`
- SOCIALDATAX: `socialdatax_get_points_balance`
- SEARCH: `search_api_docs`
- GET: `get_api_operation`, `get_openapi_spec`
- HAOKAN: `haokan_search_videos`, `haokan_search_users`, `haokan_search_suggestions`, `haokan_get_hot_search_list`, `haokan_get_video_detail_by_video_id`, `haokan_get_video_detail_by_url`, `haokan_get_video_comments_by_video_id`, `haokan_get_video_comments_by_url`, `haokan_get_comment_replies_by_video_id`, `haokan_get_comment_replies_by_url`, `haokan_get_user_info_by_user_id`, `haokan_get_user_info_by_url`, `haokan_get_user_posted_videos_by_user_id`, `haokan_get_user_posted_videos_by_profile_url`

Use the automatically listed MCP tools above as the source of truth for tool names. Pick the narrowest tool for the user's platform and task. For search pagination, omit `page_token` on the first request and pass only the complete returned `next_page_token` when continuing the same chain.
For XHS keyword completion, use `xhs_search_suggestions`; use `xhs_search_notes` or `xhs_search_products` when the user needs note or product results.
For XHS creator discovery, products, or topic pages, use `xhs_search_users`, `xhs_search_products`, or `xhs_get_topic_notes_by_topic_url` / `xhs_get_topic_notes_by_page_id`; use `xhs_get_product_detail_by_sku_id` for a known sku_id and `xhs_get_product_detail_by_url` for a product URL, then use `xhs_get_product_reviews`, `xhs_get_product_review_replies`, and `xhs_get_product_review_reply_replies` for review threads.
For Douyin products, use `douyin_search_products` by keyword; use `douyin_get_product_detail_by_product_id` for a known product_id or `douyin_get_product_detail_by_url` for a product URL.

XHS search parameter naming reminder: direct CLI uses `--sort-type`, `--publish-time-range`, and `--note-type`; the `xhs_search_notes` MCP tool uses `sort_type`, `publish_time_range`, and `note_type`. Do not pass `sortType`, `publishTimeRange`, or `noteType`.
