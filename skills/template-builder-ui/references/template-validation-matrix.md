# Template Validation Matrix

Per-channel rules a Sent template builder UI must enforce client-side, with the surface treatment for each failure mode. Use this as the single source of truth when wiring validators into the editor — the same matrix should drive the submission handler, so a "soft warning" never silently becomes a hard reject downstream.

**Surface treatments** referenced below:

- **Inline error** — red text under the field, focused on save attempt, does not block typing.
- **Blocked save** — the Submit button is disabled until resolved; tooltip explains why.
- **Soft warning** — amber banner or icon, save still allowed, but the tenant must acknowledge.

## Component support matrix (Sent-confirmed)

|  | SMS | RCS | WhatsApp |
|---|:-:|:-:|:-:|
| Header | ❌ | ✅ | ✅ |
| Body | ✅ | ✅ | ✅ |
| Footer | ❌ | ✅ | ✅ |
| Buttons | ❌ | ✅ | ✅ |

Header types (where supported): `TEXT`, `IMAGE`, `VIDEO`, `DOCUMENT`.

Button types (where supported): `QUICK_REPLY`, `URL`, `PHONE_NUMBER`.

Template categories (apply to WhatsApp review; not a Sent enum extension): `UTILITY`, `MARKETING`, `AUTHENTICATION`. No others.

## Character limits (Sent-confirmed)

| Channel | Component | Limit |
|---|---|---|
| SMS | Body | 160 chars per segment (GSM-7); longer messages split |
| WhatsApp | Body | 1028 chars |
| WhatsApp | Header (text) | 60 chars (optional component) |
| WhatsApp | Footer | 60 chars (optional component) |
| RCS | Body | 1028 chars |
| RCS | Header | 60 chars (optional component) |

## SMS

SMS templates support **Body only** — no Header, Footer, or Buttons. All rules below apply to body content.

| Rule | Limit / Behavior | Surface |
|---|---|---|
| Body length (GSM-7) | 160 chars per segment | Inline char + segment counter; soft warning at 4+ segments |
| Body length (UCS-2) | 70 chars per segment (triggered by any non-GSM-7 char, e.g. emoji, curly quotes) | Detect encoding on every keystroke; soft warning at first UCS-2 char ("This template now bills as Unicode — N segments") |
| Total body length | Hard cap at 1600 chars (10 UCS-2 segments) | Blocked save above cap |
| Opt-out language | A2P templates must include `Reply STOP to opt out` (or equivalent) at least once across the campaign's template set | Soft warning per template; campaign-level check elsewhere |
| Link shortening | Public domain shorteners (bit.ly, tinyurl) are heavily filtered by carriers | Soft warning when a known shortener domain appears in the body; suggest the tenant's branded short domain |
| Variable placeholders | Use the placeholder format the SMS template model expects (named or ordinal — see https://docs.sent.dm). Stay consistent across all SMS templates in a project. | Inline error on mismatched placeholder style |
| Sender ID injection | Alphanumeric sender IDs not allowed in US 10DLC | Blocked save if the tenant tries to set a non-numeric sender on a US campaign |
| Public URL preview | Long URLs eat segments fast | Show effective char-with-URL count; soft warning if URL is >40 chars |

For campaign-level filtering rules that gate which SMS templates are sendable, use `sms-10dlc-registration`.

## WhatsApp

Rules are *category-aware* — `UTILITY`, `MARKETING`, and `AUTHENTICATION` each have a different shape. The builder's category picker (per `SKILL.md`) reshapes which validators apply.

| Rule | Limit / Behavior | Surface |
|---|---|---|
| Name format | `^[a-z][a-z0-9_]{0,511}$` | Inline error; auto-snake_case the input |
| Name+language permanence | Treat as immutable as a product-governance choice (the Sent v3 `PUT /v3/templates/{id}` accepts these fields, but the UI should still steer tenants to a versioned `_v2` flow for auditability) | Blocked save when editing; show `_v1` suffix nudge for new versions |
| Body length | 1028 chars across all categories | Inline char counter; blocked save above cap |
| Body required | Required for utility/marketing; auth body is fixed by Meta | Blocked save if empty |
| Header type | One of: none / `TEXT` / `IMAGE` / `VIDEO` / `DOCUMENT` | Radio control — invalid combos unreachable |
| Header (text) length | 60 chars, max 1 variable | Inline error |
| Header (media) sample | Sample upload required at submit | Blocked save without a sample asset |
| Footer length | 60 chars, no variables | Inline error; strip `{{` on paste |
| Buttons — mutually exclusive | `QUICK_REPLY` XOR CTAs (`URL` + `PHONE_NUMBER`). Mixing is a Meta reject. | Top-level button-type radio prevents construction; never allow per-button type picks |
| Quick replies | Max 3, 25 char labels | Add button hidden at 3; inline error on label length |
| CTA buttons | Max 2 total, mix of `URL` + `PHONE_NUMBER` allowed | Add button hidden at 2 |
| URL CTA variables | Max 1 trailing variable, must be the URL suffix (`https://example.com/orders/{{1}}`) | Inline error on inline variables |
| Variable placeholders | `{{n}}` ordinal, monotonically increasing from `{{1}}` | Autocomplete next index; inline error on gaps (`{{1}}` then `{{3}}`) |
| Variable samples | Required at submit, non-empty | Sticky sample editor + blocked save until all filled |
| Sample neutrality | Promotional words in samples (off / sale / free / now / discount / deal …) trigger Meta re-categorization | Soft warning on the offending sample field |
| Authentication body | Fixed copy with `{{1}}` for OTP | Body field becomes read-only when category = `AUTHENTICATION` |
| Authentication buttons | Single Copy code / One-tap button + `code_expiration_minutes` | Component editor swaps shape |

For the category decision tree the picker presents, use `waba-template-author`. Mixed-button policy details remain an external Meta concern — link, do not mirror.

## RCS

RCS templates are richer (rich cards, suggested replies, suggested actions) but the channel mandates an SMS-text fallback for any device that can't render RCS.

| Rule | Limit / Behavior | Surface |
|---|---|---|
| SMS fallback body | Required, follows the SMS rules above | Blocked save without fallback; auto-derive from card title+description as a starting point |
| Body length | 1028 chars | Inline counter |
| Header (text) length | 60 chars | Inline counter |
| Rich card title | 200 chars | Inline counter |
| Rich card description | 2000 chars | Inline counter |
| Card media | Image or video; image ≤ 100 KB for "short height", ≤ 2 MB max; video ≤ 100 MB | Blocked save on oversize; soft warning at >50 KB image for short-height layout |
| Card orientation | Vertical or horizontal | Radio; preview swaps layout |
| Suggested replies | Max 11 across the message; 25 chars each | Add button hidden at 11; inline error on label length |
| Suggested actions | Max 11 across the message (shared cap with replies); types include dial, openUrl, viewLocation, shareLocation, createCalendarEvent | Add button hidden when total = 11 |
| Action URL | Must be HTTPS, valid URL | Inline error |
| Carousel cards | 2-10 cards, all same orientation | Blocked save outside range; orientation locked after first card |
| Variable placeholders | Match Sent's RCS template placeholder format — see https://docs.sent.dm | Inline error on mismatched style |
| Fallback parity | Variables in the rich content must also resolve in the SMS fallback | Soft warning if a variable appears only in one |

For agent-level capability gating that determines whether RCS is an option for a recipient, use `rcs-agent-onboarding`.

## Cross-channel notes

- The builder may target *one channel at a time* — do not let tenants compose a "WhatsApp + RCS combined template" in the same form. Channel selection is the first decision after category (where applicable) and locks the validator set.
- All three channels run validation on every keystroke (debounced) so the submit button reflects current state.
- The matrix is the contract between client validation and server validation — keep it codified (JSON schema or equivalent) and re-export to both sides.
