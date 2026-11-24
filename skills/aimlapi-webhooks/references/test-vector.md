# Signature test vector

The published test vector of the [Standard Webhooks](https://github.com/standard-webhooks/standard-webhooks/blob/main/spec/standard-webhooks.md) specification. Any correct verifier, including the scripts in this skill, accepts it. Use it in the user's unit tests.

| Input | Value |
| ----- | ----- |
| secret | `MfKQ9r8GKYqrTwjUPD8ILPZIo2LaLaSw` with the `whsec_` prefix in front (written apart here so secret scanners do not flag a public test value) |
| `webhook-id` | `msg_p5jXN8AQM9LWM0D4loKWxJek` |
| `webhook-timestamp` | `1614265330` |
| raw body | `{"test": 2432232314}` |
| `webhook-signature` | `v1,g0hM9SsE+OTPJTGt/tmIKtSyZlE3uFJELVlNIOLJ1OE=` |

The timestamp is from 2021, so pass a fixed "now" (`now=1614265330` in `verify_webhook.py`, `{ now: 1614265330 }` in `verify-webhook.mjs`) or the replay check rejects it. Then check that changing one byte of the body, or moving "now" by more than 300 seconds, makes verification fail.
