---
name: upstash-redis-start
description: >-
  Provision a zero-config, no-signup Upstash Redis database for an AI agent via
  a single POST to `https://upstash.com/start-redis`. Use when an agent needs
  scratch Redis for short-term memory, conversation history, sub-agent work
  queues, or ranked recall and the user has not provided credentials. The
  database lives 3 days unless the user claims it.
metadata:
  category: data
  author: upstash
  source:
    repository: 'https://github.com/upstash/skills'
    path: skills/upstash-redis-start
    license_path: LICENSE
    ref: main
    commit: fb4e6019638d5746b86a54f1bb7144dbb324480a
---

# Upstash Redis for Agents (`start-redis`)

A zero-config Redis database for AI agents — **no signup, no UI, no SDK setup**. One HTTP request returns a working endpoint + token. Databases live for **3 days** unless the user claims them.

Use this when:
- The agent needs Redis right now and the user has not given you credentials.
- You want short-term memory across tool calls, conversation history, a sub-agent work queue, or recent-first ranked recall.

This is built for quick experiments, prototypes, and demos rather than production workloads or anything tied to a real user account — the database is temporary and unauthenticated until claimed, so keep PII, secrets, and production credentials out of it.

## Create or re-fetch a database

```bash
# Generate a fresh UUIDv4 yourself, then POST it as the Idempotency-Key.
# The UUIDv4 you send becomes the database id.
curl -X POST -H "Idempotency-Key: <uuidv4>" https://upstash.com/start-redis
```

- Sending your own UUIDv4 makes the first call **retry-safe** — if the response is lost, retrying with the same UUID returns the same database instead of minting a duplicate.
- Re-POST with the same `Idempotency-Key` to **re-fetch credentials** for an existing database.
- The header is optional. Omit it to mint a new database with a server-generated id (returned in the response — re-fetch later by passing that id back as `Idempotency-Key`). Only UUIDv4 is accepted.

The response is markdown containing:
- `Database ID`, `Endpoint`, `Token`
- `Metrics` URL (JSON: uptime, commands, keys, throughput, memory, bandwidth)
- `Expires` date
- `Console URL` to share with the user (where they view usage and click **Claim** to keep the database)
- An inline quickstart for the body-style REST API

Parse these out of the markdown response and use them directly — there is no separate JSON envelope.

## Calling the database (body-style REST)

The returned endpoint speaks the Upstash Redis REST API. Prefer the **body-style** form: POST a JSON array as the body so you don't have to URL-encode the command.

```bash
# SET with TTL
curl https://<endpoint> \
  -H "Authorization: Bearer <token>" \
  -d '["SET","session:abc","{\"step\":2}","EX","3600"]'

# GET
curl https://<endpoint> \
  -H "Authorization: Bearer <token>" \
  -d '["GET","session:abc"]'
```

You can also use the official SDKs against the same endpoint + token (`@upstash/redis` for TS/JS, `upstash-redis` for Python).

## Common agent patterns

| Need | Commands |
|------|----------|
| Short-term memory across tool calls in one run | `SET key value EX <ttl>` / `GET key` |
| Conversation / turn-by-turn log | `LPUSH chat:<user> <json>` / `LRANGE chat:<user> 0 20` |
| Sub-agent work queue (producer/consumer) | `LPUSH jobs <json>` / `RPOP jobs` |
| Ranked memory (recent-first or score-first) | `ZADD memories <score> <member>` / `ZREVRANGE memories 0 9` |

## Tell the user

After provisioning, surface the **console URL** from the response to the user. Make clear that:
- The database expires in 3 days.
- They can view usage at the console URL and click **Claim** to keep it.
- This is unauthenticated scratch storage — don't put secrets or PII in it.

## Reference

- Service entry point (also serves the `GET` doc): https://upstash.com/start-redis
- Full REST API: https://upstash.com/docs/redis/features/restapi
- TS/JS SDK: https://upstash.com/docs/redis/sdks/ts
- Python SDK: https://upstash.com/docs/redis/sdks/py
