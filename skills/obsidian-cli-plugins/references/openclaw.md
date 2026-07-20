# OpenClaw Compatibility

OpenClaw-compatible installs should expose this skill as:

```text
~/.openclaw/skills/obsidian-cli-plugins/SKILL.md
```

On older OpenClaw or OpenClaw-adjacent runtimes, `~/.cc-switch/skills/obsidian-cli-plugins/SKILL.md` may still be useful as a compatibility copy. Do not assume that path is discoverable. Check the runtime's reported `managedSkillsDir` or run its skill discovery command first.

Use the bundled sync script from the Codex skill source:

```bash
python3 <skill-dir>/scripts/sync_openclaw.py --dry-run
python3 <skill-dir>/scripts/sync_openclaw.py
```

Override the OpenClaw skills directory when needed:

```bash
OPENCLAW_SKILLS_DIR=/path/to/openclaw/skills python3 <skill-dir>/scripts/sync_openclaw.py
python3 <skill-dir>/scripts/sync_openclaw.py --dest /path/to/openclaw/skills
```

If the destination already exists, use `--force`; the script replaces the existing OpenClaw skill copy without creating a backup. Add `--backup` only when a timestamped backup is explicitly needed. Prefer copy mode for cross-platform use. Use `--link` only on systems where symlinks are reliable for the target Agent runtime.

After syncing:

1. Confirm `~/.openclaw/skills/obsidian-cli-plugins/SKILL.md` exists unless an explicit `OPENCLAW_SKILLS_DIR` or `--dest` was used.
2. For legacy runtimes only, optionally confirm `~/.cc-switch/skills/obsidian-cli-plugins/SKILL.md` exists.
3. Restart or refresh OpenClaw if it caches skill discovery.
4. Run OpenClaw's skill discovery/check command when available and verify `obsidian-cli-plugins` is visible.
5. Run `python3 ~/.openclaw/skills/obsidian-cli-plugins/scripts/obsidian_workflows.py doctor`. All executable launchers live under `scripts/`; integrations should not call Python files from the skill root.
6. Configure `OBSIDIAN_VAULT`, `OBSIDIAN_VAULT_PATH`, `OBSIDIAN_CONFIG`, or `OBSIDIAN_BIN` in OpenClaw's shell/session environment when auto-discovery is not enough.

OpenClaw should use the same script contract as Codex: call `doctor` first, prefer JSON outputs, stop on `ok=false`, and do not claim Journals/plugin execution succeeded without `obsidian command` output and file verification.

## Skill and plugin dependency

`obsidian-cli-plugins` is required for the Obsidian side of this workflow. It provides the commands that create notes, copy attachments into record assets, consume staged media, run Git preflight, commit, and sync.

`obsidian-media-claim` is optional. Install it only when OpenClaw channel uploads should be claimed before model dispatch. Its main value is cost and behavior control: media-only uploads are acknowledged and staged without asking the LLM to inspect or reason about the media. The later text instruction can then use this skill's `attachment-pending` and `--staged-attachment` workflow.

Without the plugin, this skill still supports text records, task/project records, same-turn records with explicit readable `--attach` paths, and manually staged media. What is not guaranteed without the plugin is the no-model media-only upload path: OpenClaw may send the upload turn to the model, or the runtime may need another channel-specific guard to stage it.

## Media-only inbound claim guard

On OpenClaw runtimes that send media-only channel messages into the model, install the optional `obsidian-media-claim` plugin before relying on no-model multi-message media workflows. The implementation is packaged as:

```text
obsidian-media-claim
```

It detects media-only inbound events with no user text, claims them before the default LLM reply path, and returns a short acknowledgement so the upload does not spend model tokens. When readable local paths are available, it stages every file with:

```bash
python3 ~/.openclaw/skills/obsidian-cli-plugins/scripts/obsidian_workflows.py attachment-stage --path "<runtime-path>" --type <image|audio|video|file> --label "<filename>" --batch-key "<stable-short-conversation-sender-key>"
```

The guard is intentionally channel-generic: it checks OpenClaw media placeholders, `[Attachment: ...]` markers, and common metadata fields such as `mediaPaths`, `MediaPaths`, `mediaPath`, `MediaPath`, and `mediaList`. Keep the generic path first, and add channel-specific branches only after a verified channel exposes media differently. If the same message also contains user text, do not claim it; let the normal record workflow handle same-turn media plus text.

Required OpenClaw config shape:

```json
{
  "plugins": {
    "entries": {
      "obsidian-media-claim": {
        "enabled": true,
        "hooks": {
          "allowConversationAccess": true,
          "allowPromptInjection": true,
          "timeoutMs": 15000
        },
        "config": {
          "stageAttachments": true,
          "replyDispatchGuard": true,
          "beforeDispatchFallback": true,
          "agentReplyFallback": true,
          "pendingMediaPromptInjection": true,
          "replyContent": "收到媒体，已保存。"
        }
      }
    }
  }
}
```

`allowConversationAccess=true` is required for non-bundled OpenClaw plugins that register conversation-aware typed hooks. `allowPromptInjection=true` keeps the later-text staged-media guidance available. After installation, verify with `openclaw plugins inspect obsidian-media-claim`; the hook list should include `reply_dispatch`, `inbound_claim`, `before_dispatch`, `before_agent_reply`, and `before_prompt_build`.

For file-mode record creation, OpenClaw should first obtain the shared analysis contract, send the returned prompt to its own model, validate/normalize the model JSON, then call the copied Python launcher:

```bash
python3 ~/.openclaw/skills/obsidian-cli-plugins/scripts/obsidian_workflows.py analyze-record --text "<original record content>" --date today --prompt-only
python3 ~/.openclaw/skills/obsidian-cli-plugins/scripts/obsidian_workflows.py analyze-record --text "<original record content>" --date today --analysis-json '<model json>' --normalized-only
python3 ~/.openclaw/skills/obsidian-cli-plugins/scripts/obs_record_sync.py --mode file --period day --date today --text "<original record content>" --topic <kind> --analysis-json '<normalized model json>'
```

If the OpenClaw request includes any uploaded, recorded, or voice-input media/file attachment, it must create the record and attach the file in the same command. Use the same workflow for images, videos, audio, and ordinary files; media type only affects staging metadata and Markdown rendering:

```bash
python3 ~/.openclaw/skills/obsidian-cli-plugins/scripts/obs_record_sync.py --mode file --period day --date today --text "<original record content>" --type mixed --topic <kind> --analysis-json '<normalized model json>' --attach "<runtime-provided first path>" --attach "<runtime-provided second path>" --require-attachment --allow-external-attachments
```

Pass one `--attach` for each uploaded file and create one record for "these/all/above N files" unless the user explicitly asks for separate records. A path supplied by OpenClaw's attachment metadata for the current user message counts as explicit user-provided attachment input, so OpenClaw should pass `--allow-external-attachments` instead of asking a second confirmation question. If OpenClaw can tell that the user supplied media but cannot access a readable local path, it must stop before creating the record and report `attachment-path-unavailable`; it must not create the record first and ask whether to add the already supplied media.

Some OpenClaw channels cannot send media and text in the same message. Those channels are still supported only if OpenClaw can access a readable local file path for the media message:

```bash
python3 ~/.openclaw/skills/obsidian-cli-plugins/scripts/obsidian_workflows.py attachment-stage --path "<runtime-provided first media path>" --type <image|audio|video|file> --label "<filename-1>" --batch-key "<conversation-or-message-group>"
python3 ~/.openclaw/skills/obsidian-cli-plugins/scripts/obsidian_workflows.py attachment-stage --path "<runtime-provided second media path>" --type <image|audio|video|file> --label "<filename-2>" --batch-key "<conversation-or-message-group>"
python3 ~/.openclaw/skills/obsidian-cli-plugins/scripts/obsidian_workflows.py attachment-pending --batch-key "<conversation-or-message-group>" --ttl-hours 48
python3 ~/.openclaw/skills/obsidian-cli-plugins/scripts/obs_record_sync.py --mode file --period day --date today --text "<later text content>" --type mixed --analysis-json '<normalized model json>' --staged-attachment "batch:<conversation-or-message-group>" --require-attachment
```

`attachment-stage` is a private cache step only; it must not create or modify Obsidian notes. Staged media should be obtained by a later `attachment-pending` command and consumed by the later record command, or pruned with `attachment-prune --ttl-hours 48`. If a channel cannot provide a readable local media path and cannot preserve either attachment ids or a stable batch key for the later text request, OpenClaw must return `unsupported-channel-attachment-record` and tell the user this channel/Agent does not support text records with media attachments. It should not create a text-only fallback record unless the user explicitly asks for a text-only record after that warning.

## OpenClaw channel media input matrix

Use this matrix when the user asks which OpenClaw channel can accept several media files plus one text record request from a phone client. The Obsidian record workflow is allowed only when the channel/plugin exposes readable local paths for every media item.

This matrix is operational guidance, not a permanent compatibility promise. Before relying on a positive row after plugin/runtime changes, verify the current channel still exposes readable local paths and update this table. If a row is old or unverified, mark it unknown/unsupported rather than preserving stale support claims.

| Channel | Current local status | Same-turn multi-media + text | Attachment path shape | Decision for this skill |
|---|---:|---:|---|---|
| `wecom` / Enterprise WeChat | enabled on this host | Yes when WeCom exposes readable media paths | plugin downloads media into a `mediaList` | Preferred channel for mobile media records |
| `qqbot` / QQ Bot | enabled on this host | Supported by plugin when QQ exposes readable media paths | media may appear through `MediaPaths`, attachment tags, or local downloaded paths | Supported when every referenced media item has a readable local path |
| `feishu` / Lark | enabled on this host | Do not treat as supported for inbound attachment-backed records | current plugin clearly exposes outbound media capability, but no stable inbound local attachment path contract was verified | Return unsupported unless another layer materializes paths |
| `openclaw-weixin` / WeChat | installed but disabled on this host | Not reliable for multi-media records | protocol has `item_list`, but current code selects only the first downloadable media into `MediaPath` | Do not use for multi-media records; use staging only if readable paths are exposed |
| `telegram` | disabled / not verified on this host | unknown | no local evidence | Do not claim support |

Mobile sending rules:

- Enterprise WeChat: use the phone client's mixed-message editor when available. Put the sentence and all media in the same editor and send once. If the user sends media first and text later, use `attachment-stage`.
- QQ Bot: in mobile QQ, type the sentence first, keep it unsent, then add/select media and send once when QQ exposes readable paths. If QQ splits the content into separate events, use `attachment-stage`.
- File-size limits and channel downgrades matter. WeCom can downgrade oversized media to file or reject it; QQBot has media/file size limits. A failed download, remote-only URL, or path hidden in a forwarded bundle does not satisfy `--require-attachment`.

## Multi-message media then text record workflow

Use this workflow when a channel delivers several media-only messages first, then a later text command such as `把上面三个媒体文件记录到 ob`, `刚才这些附件记录一下`, or `将上传的媒体记录一下`. The goal is one Obsidian file-mode record that contains the user's later text and all referenced media. The media messages themselves are not Obsidian records.

Required capability gate:

1. The Agent runtime must expose a readable local file path for every media message before calling this skill. A URL, opaque media id, base64 blob hidden inside the channel, or expired temporary object is not enough unless the Agent first materializes it as a readable local file.
2. The Agent runtime must provide a stable grouping key across the media messages and the later text message. Prefer conversation id plus sender id plus message group id. If no group id exists, use a short timestamp bucket only when the Agent can verify the staged list before writing. Do not use `default` for cross-message record workflows.
3. The Agent must know whether the later text refers to all pending media or only a count/subset. If the user says `三张图` and five files are staged, ask or fail with an ambiguity message before writing. Do not guess.
4. If any required path or grouping capability is unavailable, stop before writing and report `unsupported-channel-attachment-record` or `attachment-path-unavailable`. Do not create a text-only record as a fallback unless the user explicitly asks for text-only recording after the warning.

Detailed state machine:

1. Media message arrives. Validate that the runtime-provided path exists and is readable. Determine media type as `image`, `audio`, `video`, or `file`; use `mixed` later only for the final record type.
2. Stage only that media file:

   ```bash
   python3 ~/.openclaw/skills/obsidian-cli-plugins/scripts/obsidian_workflows.py attachment-stage --path "<runtime-path-1>" --type <image|audio|video|file> --label "<channel label or filename>" --batch-key "<conversation-sender-group>"
   ```

   The returned `attachment_id` is private cache state. Keep the vault unchanged at this stage, avoid journal-link side effects, and report only that the media was staged for a later record.
3. Repeat staging for every subsequent media-only message under the same `--batch-key`. Preserve the channel order when possible, but never rely on order alone for correctness.
4. When the text message arrives, first list staged media for that key with a command result, not model memory:

   ```bash
   python3 ~/.openclaw/skills/obsidian-cli-plugins/scripts/obsidian_workflows.py attachment-pending --batch-key "<conversation-sender-group>" --ttl-hours 48
   ```

   Do not split the flow by image/video/audio/file unless the user selected a subset that the channel can map exactly. Verify count, labels, types, and freshness against the user's text. If the text says `上面这些媒体`, the expected count is the current unconsumed staged media count for that key. If the text gives a number, the count must match exactly unless the Agent has a reliable channel-side selection mapping. Do not use `attachment-list --batch-key default`, old staged ids from model memory, or direct reads under `~/.cache/obsidian-cli-plugins/staged-attachments`.
5. Analyze the later text as the record utterance. Call `analyze-record --prompt-only`, send the returned prompt/schema to the Agent's own LLM/model, validate with `--normalized-only`, then keep the normalized JSON for `--analysis-json`. The media labels and captions may help metadata, but they must not replace the later text in `--text`.
6. Create one file-mode record and consume the staged media in the same command:

   ```bash
   python3 ~/.openclaw/skills/obsidian-cli-plugins/scripts/obs_record_sync.py --mode file --period day --date today --text "<later text content>" --type mixed --analysis-json '<normalized model json>' --staged-attachment "batch:<conversation-sender-group>" --require-attachment
   ```

   Use explicit `--staged-attachment <attachment_id>` values only when the user selected a known subset. Otherwise consume the `selector` returned by `attachment-pending`, normally `batch:<resolved-batch-key>`.
7. Treat success as all of the following, not merely command exit:
   - returned JSON has `ok=true`;
   - `record_file.path` points to one new QuickAdd `fleeting` record file;
   - `record_file.copied_attachments` count equals the expected staged media count;
   - copied media paths are under the record-local assets folder, normally `00_inbox/fleeting/assets/<record-title>/`;
   - the record body embeds image/audio/video files with Markdown image/embed syntax and links non-media files normally;
   - the target period journal contains exactly one standard Markdown link under `记录`;
   - final Git status is clean and synced after commit and push.
8. Consume or prune staged media only after a successful record write and push. If record creation, attachment copy, Git preflight, commit, or push fails, keep the staged cache available for retry unless the user asks to discard it. Use `attachment-prune --ttl-hours 48` for stale private cache cleanup. `attachment-stage` also prunes expired staged files before saving newly uploaded media so the private cache does not accumulate indefinitely.

Failure handling:

- `attachment-path-unavailable`: media was supplied by the channel, but the Agent cannot access a readable local file path, or the temporary path vanished before staging.
- `unsupported-channel-attachment-record`: the channel/Agent cannot expose readable local media and cannot carry stable attachment ids or a stable `batch-key` into the later text request.
- `ambiguous-staged-attachments`: the later text references `上面/这些/刚才` while multiple pending batches or a count mismatch exists.
- `record-attachment-required`: the final record command would create a media/attachment record without copying at least one real local file.
- `git-preflight-failed`, `unmerged`, or `merge_head`: stop before claiming success; do not describe a local partial note as synced.
- Count mismatch after `record-sync`: do not report success. Report the copied count and expected count, keep staging for retry, and avoid creating another duplicate record unless the user explicitly confirms the retry strategy.

Risks and uncontrollable points:

- Channel behavior is not uniform. Some channels compress images, strip filenames, rewrite metadata, split albums into separate events, or deliver media out of order. The skill can preserve supplied files but cannot recover original quality or ordering not exposed by the channel.
- Some Agent runtimes expose only remote URLs, opaque message ids, or in-memory blobs. This skill intentionally refuses those until the Agent materializes a readable local path, because `--require-attachment` is defined as copying a real local file into the vault.
- Temporary media paths can expire before the user sends the later text. Stage immediately when the media-only event arrives; do not wait for the text command to download or inspect the attachment.
- The phrase `上面这些` is context-dependent. In active group chats or channels with concurrent users, the Agent must scope by sender and conversation, not just the current thread. If two pending batches are plausible, ask or fail before writing.
- Message order can be delayed or retried. A later text command might arrive before all media events are visible to the Agent, or duplicate media events may be delivered. Verify `attachment-pending` and use deduplication only when the runtime provides reliable file identity.
- Media captions, OCR, ASR, and image understanding are optional and may be wrong. They can inform metadata only when available, but the user's later text remains the authoritative `--text` body.
- Staged attachments are private cache files under `~/.cache/obsidian-cli-plugins`; they may contain sensitive media. Keep permissions private, do not echo raw source paths in user-facing summaries, and prune stale batches.
- Large media can hit Git hosting limits or make sync slow. The workflow should still copy and force-add user-supplied media when requested, but a failed push is not success and may require a separate Git/LFS policy decision.
- Obsidian rendering support differs by media type and platform. The skill writes standard Markdown embeds/links; it cannot guarantee that every Obsidian client previews every codec or file format.
- Cross-Agent semantic analysis can differ. The local script only normalizes and validates the shared schema; it cannot force another Agent model to infer the same `kind`, `scene`, or `headline`. Consistency depends on all Agents using the same prompt contract and passing model-produced JSON through `analyze-record --normalized-only`.

For channel robots that deliver several media messages followed by one text command such as `将以上三个媒体文件记录到 ob 中`, use the conversation id, sender id plus timestamp bucket, or another runtime-stable request group as `--batch-key`. Stage every media file under that key, do not semantically analyze only the first file as the whole user intent, then create a file-mode record with `--mode file --text "<later text content>" --staged-attachment batch:<key> --require-attachment`. After the record command returns, verify `len(record_file.copied_attachments)` equals the number of staged files referenced by the user before reporting success.

Before this call, OpenClaw must use its own LLM/model to analyze the whole user utterance and pass the model-produced result through `--analysis-json`. Use only the unified fields from `references/record-body.md`: `kind`, `headline`, `occurred_on`, `time_hints`, `scenes`, `actors`, `insight`, `question`, `reflection`, `next_actions`, and `intent`. Pass the user's original record content in `--text`; do not expand, polish, summarize, translate, or rewrite it before recording. Prefer `headline` built from the core idea, not the full contextual utterance; the script falls back to `question`, then `insight`, then the full `--text` when no headline is provided. Body sections are filled by `fields` plus built-in formatters; appendix keywords such as `source_links` and `reference_links` are reserved for `来源(Source)` and `关联(Reference)`. The validator normalizes known legacy aliases such as `scene`, `time_clues`, and `title` for resilience and returns diagnostics, but OpenClaw prompts must still ask the model for unified names. Do not claim semantic analysis succeeded when the JSON was hand-written, assembled from fixed rules, or manually inferred without a model analysis step. Semantic analysis is metadata only and must not replace the note body. If analysis returns no useful unified fields or the runtime cannot perform model-side analysis, do not block the record write; pass the original `--text` and omit unsupported analysis fields.

It may call `obsidian_workflows.py record-sync` directly when needed, or explicitly local-only `record` for local-only work. It must not create Markdown files directly in `00_inbox/fleeting`, and it must not silently omit `--analysis-json` for record creation. The script renders the QuickAdd `fleeting` template and rejects records when the configured template does not match the default record shape.
