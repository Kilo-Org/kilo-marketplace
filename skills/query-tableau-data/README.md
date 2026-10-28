# Query Tableau Data

[![skills.sh](https://img.shields.io/badge/skills.sh-install-purple)](https://skills.sh/Action-Co/skills)

**An agent skill by [The Action Company](https://action.co) that gives AI analysts the ability to explore, understand, and query data inside Tableau Cloud and Server.**

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/Action-Co/skills/a0815cb921f5d741096dcd527df87eb339433920/assets/banners/GitHub%20Banner%20-%20Option%201.svg">
  <source media="(prefers-color-scheme: light)" srcset="https://raw.githubusercontent.com/Action-Co/skills/a0815cb921f5d741096dcd527df87eb339433920/assets/banners/GitHub%20Banner%20-%20Option%201.svg">
  <img alt="Agent Skills by The Action Company" src="https://raw.githubusercontent.com/Action-Co/skills/a0815cb921f5d741096dcd527df87eb339433920/assets/banners/GitHub%20Banner%20-%20Option%201.svg" width="500">
</picture>

---

## The "Last Mile" Problem

When business users think about company data, they rarely think about a warehouse. They think about the dashboard they check every Monday, the data source their team curated with meaningful field names, or the view that already filters to their region. Tableau is the _last mile_ of analytics: the place where raw data is shaped into something decision-makers can use.

This visual and semantic context is enormously valuable, yet most AI analysts rarely use it in their toolkit. They can query a database, but they can't explore what a business team has _already built_ on top of it. They can't discover which data sources are certified, which views are most popular, or what calculations sit on top of the raw tables.

This skill closes that gap. It gives agents the ability to authenticate against Tableau, navigate the data catalog, introspect data source schemas, trace lineage between workbooks and their upstream sources, and query the data, all in code.

> _Note_: this skill requires initial human setup to authenticate to a Tableau environment, jump to the [README.md § HITL](./README.md#tasks-that-require-a-human-in-the-loop-hitl) section for more instructions.

---

## Tasks that Require a Human In The Loop (HITL)

The skill is designed so that agents do all the work. However, initial setup requires human action to authenticate to your Tableau site and enforce your permissions as a user.

### 1. Identify Your Tableau Environment

You need two values that identify your Tableau site:

| Variable | Where to Find It | Example |
|----------|------------------|---------|
| `TABLEAU_SERVER_URL` | The base URL of your Tableau Cloud or Server instance | `https://prod-useast-b.online.tableau.com` (Cloud) or `https://tableau.yourcompany.com` (Server) |
| `TABLEAU_SITE_NAME` | The site's content URL (subpath). Found in your browser URL after `/site/` when logged in. For the Default site on Server, leave empty. | `MarketingTeam` |

> **Tip**: On Tableau Cloud, your server URL includes the pod name (e.g., `prod-useast-b`, `prod-ca-a`). You can find this in your browser address bar when logged in.

### 2. Create a Personal Access Token (PAT)

PAT is the recommended authentication method. It avoids exposing passwords and can be revoked independently of your user account.

1. Log in to your Tableau Cloud or Server site
2. Click your profile icon (top-right) and select **My Account Settings**
3. Scroll to the **Personal Access Tokens** section
4. Enter a **Token Name** (e.g., `agent-skill`) and click **Create new token**
5. **Copy the secret immediately** — it is shown only once and cannot be retrieved later

| Variable | Value |
|----------|-------|
| `PAT_NAME` | The token name you entered (e.g., `agent-skill`) |
| `PAT_VALUE` | The secret string displayed in the creation dialog |

> **Expiration**: PATs expire after 15 consecutive days of non-use. On Tableau Cloud, site admins can configure expiration. On Server, they expire after one year by default. Regenerate if your agent starts getting 401 errors.

### 3. (Alternative) Username & Password

Only use this if PATs are unavailable in your environment. Multi-factor authentication (MFA) on Tableau Cloud **requires** PATs — username/password will not work.

| Variable | Value |
|----------|-------|
| `TABLEAU_USERNAME` | Your Tableau login username |
| `TABLEAU_PASSWORD` | Your Tableau login password |

### 4. (Advanced) API Versions

The REST API version is **auto-negotiated** from the server on session entry — you do not need to set it. The VDS version can be pinned if needed:

| Variable | Description | Default |
|----------|-------------|---------|
| `TABLEAU_VDS_VERSION` | VizQL Data Service version (e.g., `v1`) | `v1` |

### 5. Save Your Credentials

In the skill's root directory (where `.env.template` and `pyproject.toml` live):

```bash
cp .env.template .env
# Edit .env with your values from steps 1-2 above
```

The `.env` file must live in this directory, next to `.env.template`. It is gitignored — never commit credentials to the repository.

### 6. Verify Access

Ask your agent to run the authentication check:

```python
from query_tableau_datasource.config import SdkConfig
from query_tableau_datasource.session import Session
with Session(SdkConfig()) as session:
    print("AUTH OK")
```

If this fails, see [AUTH.md](./docs/api/AUTH.md) for troubleshooting.

![Bar and Whiskers Chart](https://github.com/Action-Co/skills/blob/main/assets/cover/Tableau%20Cover%20-%20(1440x168)%20-%20Transparent%20Background.png?raw=true)

---

## Design

This skill ships documentation ([docs/](./docs/) folder) and working code ([src/](./src/) folder) to help AI agents generate code-based solutions that interact with a Tableau environment.

The provided code is minimal yet built to be ergonomic for coding agents. It abstracts the complexities of authenticating to Tableau and reuses a session across `HTTP` requests to the server. All other operations are modular, so agents can compose them to fit their needs.

Rather than calling predefined tools via JSON, the agent writes and executes code in a persistent session — holding state as variables, composing operations with control flow, and self-debugging from execution feedback.

This implementation lets AI agents do the following:

- Use a `Read-Eval-Print-Loop (REPL)` to progressively explore the Data Catalog for datasources and views. This pattern is like giving agents a lightweight Jupyter notebook, so they can navigate the largest Tableau sites without bloating their context window.
- Write reusable workflows as scripts (in the [scripts/](./scripts/) folder) so the next time data is needed, agents can quickly retrieve it on-demand.
- Incorporate Tableau data in external applications as "Headless BI" by using the `src` code directly or modifying it to meet their needs.

> _Note_: For practical usage and agent instructions, see the [SKILL.md](./SKILL.md) file.


### Why CodeAct Instead of MCP?

We chose a [**CodeAct**](https://arxiv.org/abs/2402.01030) approach for this skill because it gives agents the composability, control flow, and self-debugging capabilities that rigid tool interfaces cannot. Here is how that decision maps to the existing tooling landscape.

MCP is an alternative way to interact with a Tableau environment, but it relies on static tool definitions that make it hard for agents to reliably translate these tool calls into scripts or working application code.

MCP also doesn't provide the control and data flow that you would get from a `REPL` or script. So tool responses are returned directly to the agent context window, causing bloat and reducing reliability in long-running tasks.

MCP **code mode** has been proposed as a way to bridge this gap, but this skill demonstrates that coding agents do not require MCP at all, and in fact perform better when they write code directly. They only need documentation, examples, and some lightweight abstractions. Consider, too, that **code mode** only exposes tool signatures to the agent as callable functions but does not give them full access to the source code, so they can copy and modify it to meet their needs.

MCP adds avoidable overhead and limits what coding agents can do. Concerns such as permissions belong in their own auth layer, not a tool server. A richer paradigm like **CodeAct** models agent tooling more effectively than stretching MCP into a use case it wasn't built for.

---

### CodeAct

This skill is a [**CodeAct**](https://arxiv.org/abs/2402.01030) implementation. Instead of exposing Tableau operations as JSON tool definitions (the MCP pattern), it ships a lightweight SDK that agents import and execute directly. This matters because:

- **Composition through control flow.** Agents loop over datasources, filter results programmatically, and chain operations (inventory → lineage → introspect → query) in a single code block — impossible with one-tool-at-a-time JSON actions.
- **Self-debugging through execution feedback.** When a query fails (wrong field caption, expired token), the agent observes the typed exception, reads the error message, and corrects its next attempt — no human intervention needed.
- **Persistent state through variables.** Catalog metadata, schemas, and query results persist as objects across turns. The agent references them by name rather than re-fetching or parsing tool responses from its context window.

![CodeAct](https://raw.githubusercontent.com/Action-Co/skills/78635a69d82b733f22d61492089c5b810443c655/assets/diagrams/Code%20Act.svg)

> **Figure 1**: Code actions outperform JSON/text tool-calling by up to 20% across 17 LLMs by unifying actions into a single space with native control flow, data flow, and multi-tool composition.
>
> **Source**: [Executable Code Actions Elicit Better LLM Agents (Wang et al., 2024)](https://arxiv.org/abs/2402.01030)

These performance gains compound in multi-turn and long-running tasks. Because the agent holds state as variables in a persistent session, it can build on prior results across turns without re-fetching data or bloating its context window. When a query fails or returns unexpected results, the agent reads the execution feedback, adjusts its code, and retries — all within the same session. This closed feedback loop is what makes long-running exploration (traversing a large catalog, tracing lineage, iterating on a query) reliable in ways that one-shot JSON tool calls cannot match. It also sets up the recursive pattern used in the next section: when the catalog itself is too large to fit in context, the agent uses the same persistent session to decompose the problem into smaller, sequential steps.

![Multi-turn Code Execution](https://raw.githubusercontent.com/Action-Co/skills/78635a69d82b733f22d61492089c5b810443c655/assets/diagrams/Multi-Turn.svg)

> **Figure 3**: Multi-turn interaction with execution feedback. The agent imports libraries, executes, observes errors, and self-debugs — closing the gap between intent and working code without demonstrations.
>
> **Source**: [Executable Code Actions Elicit Better LLM Agents (Wang et al., 2024)](https://arxiv.org/abs/2402.01030)

---

### REPL-Based State Management

Enterprise Tableau sites can have thousands of datasources, tens of thousands of views, and schemas with hundreds of fields. Dumping this into an agent's context window degrades reasoning on even simple tasks.

Instead, this skill treats catalog data as **environment state** — held in variables, never printed in full. The agent:

1. Loads inventory into a variable, prints only counts and filtered summaries
2. Decomposes discovery into sub-tasks (scope → inventory → lineage → introspect)
3. Ingests only the necessary data into context to make decisions

This keeps the context window lean while allowing the agent to do `O(n)` semantic work across the entire site.<sup>[1]</sup>

Research on [Recursive Language Models](https://arxiv.org/abs/2512.24601) demonstrates that managing large inputs as REPL variables — rather than loading them into the context window — is a key technique for scaling beyond context limits. This skill applies that same principle: the agent never dumps the full catalog into its reasoning context, instead probing and filtering as needed.

Notably, the RLM paper finds strong gains even at recursion depth 0 (no sub-calling) simply by offloading state to the REPL. The same applies here: because the agent operates inside a live coding environment, it avoids the overhead of editing files, running scripts, and parsing new output contexts. It iterates forward in the same session — like a Jupyter notebook — progressively filtering, exploring, and making decisions while the full catalog stays safely in variables.

> For a fully recursive implementation that adds programmatic sub-calling on top of this REPL pattern, see the author's reference implementation at [alexzhang13/rlm](https://github.com/alexzhang13/rlm). Individual harnesses implement recursion differently — some use sub-agent delegation, others use the REPL alone.

![RLM_REPL](https://raw.githubusercontent.com/Action-Co/skills/a0815cb921f5d741096dcd527df87eb339433920/assets/diagrams/RLM-RPL.svg)

> **Figure 2**: From the RLM research: loading input as a REPL variable and writing code to peek and decompose. This pattern scales beyond model context limits by keeping the working set in variables rather than in the context window.
>
> **Source**: [Recursive Language Models (Zhang et al., 2026)](https://arxiv.org/abs/2512.24601)

> **Note 1 — `O(n)` in this context.** `O(n)` is Big O notation for *linear complexity*: the amount of semantic work the task itself requires grows in direct proportion to the input size (e.g., OOLONG in the RLM paper requires examining almost every line). This skill's REPL-based approach lets the agent match that task complexity through sequential exploration — decomposing, peeking, and iterating as needed — while keeping the context window constant (`O(1)`) rather than loading everything at once. Unlike compaction (which loses detail) or sub-agent delegation (which adds verbalization overhead), this approach scales reliably because the agent only holds the current step in memory, not the entire catalog.

---

## Further Reading

Built by **[The Action Company](https://action.co)**, an interdependent consultancy that helps organizations make better decisions in complex, fast-moving environments. We turn fragmented details into shared understanding, decisive action, and decision systems that help teams see patterns sooner, align on what matters, and respond to changing conditions.

- **[Our Approach](https://action.co/approach)** — The ACT framework: Advance (data aptitude), Create (compelling data messages), Transform (your organization)
- **[The Action Library](https://action.co/library)** — Thought leadership on Tableau, AI, and the future of analytics
- **[The Real Meaning of Headless BI](https://action.co/the-real-meaning-of-headless-bi)** — Why composable, code-first agent tooling outperforms monolithic platform approaches
- **[Connect With Us](https://action.co/connect)** — Book a chat, subscribe to our newsletter, or drop us a message

---

![Action Co. Cover](https://github.com/Action-Co/skills/blob/main/assets/cover/Action%20-%20LinkedIn%20-%20Company%20Cover%20-%20(1129x192).png?raw=true)
