// Verify an AI/ML API webhook (Standard Webhooks). Node 18+, no dependencies.
//
//   import { verify } from "./verify-webhook.mjs";
//   const event = verify(rawBodyBuffer, req.headers, process.env.AIMLAPI_WEBHOOK_SECRET);
//
// `rawBody` must be the exact bytes received (e.g. express.raw({ type: "application/json" })),
// before any JSON parsing.

import { createHmac, timingSafeEqual } from "node:crypto";

export const TOLERANCE_SECONDS = 300;

export class WebhookVerificationError extends Error {}

function header(headers, name) {
  const value = typeof headers.get === "function" ? headers.get(name) : headers[name] ?? headers[name.toLowerCase()];
  if (!value) throw new WebhookVerificationError(`missing ${name} header`);
  return Array.isArray(value) ? value[0] : value;
}

export function sign(secret, msgId, timestamp, body) {
  const encoded = String(secret ?? "").replace(/^whsec_/, "");
  const key = Buffer.from(encoded, "base64");
  if (key.length < 16 || !/^[A-Za-z0-9+/]+={0,2}$/.test(encoded)) {
    // An empty or truncated secret would let anyone forge a signature.
    throw new WebhookVerificationError("the webhook secret is empty, too short or not base64; load the whsec_... value");
  }
  const digest = createHmac("sha256", key)
    .update(Buffer.concat([Buffer.from(`${msgId}.${timestamp}.`), Buffer.from(body)]))
    .digest("base64");
  return `v1,${digest}`;
}

export function verify(rawBody, headers, secret, { now = Date.now() / 1000 } = {}) {
  const body = typeof rawBody === "string" ? Buffer.from(rawBody) : Buffer.from(rawBody);
  const msgId = header(headers, "webhook-id");
  const timestamp = header(headers, "webhook-timestamp");
  const signatures = header(headers, "webhook-signature");

  const ts = Number(timestamp);
  if (!Number.isInteger(ts)) throw new WebhookVerificationError("bad webhook-timestamp");
  if (Math.abs(now - ts) > TOLERANCE_SECONDS) {
    throw new WebhookVerificationError("webhook-timestamp outside the tolerance window");
  }

  const expected = Buffer.from(sign(secret, msgId, timestamp, body).slice(3));
  // During a secret rotation the header carries several space-separated signatures.
  const match = signatures.split(" ").some((candidate) => {
    const [version, value = ""] = candidate.split(",", 2);
    const given = Buffer.from(value);
    return version === "v1" && given.length === expected.length && timingSafeEqual(given, expected);
  });
  if (!match) throw new WebhookVerificationError("no matching signature");
  return JSON.parse(body.toString("utf8"));
}
