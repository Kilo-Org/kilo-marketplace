# AI Pass integration skill

The official single-skill distribution repository for the flagship
[`aipass-integration`](https://aipass.one/skills/aipass-integration/SKILL.md) agent workflow.

AI Pass lets applications offer text, image, speech, and multi-model AI while end users fund their
own usage. Apps keep their existing host, authentication, deployment, and billing; AI Pass Spaces
is optional.

This small repository exists for agent marketplaces and installers that import one skill from a
public GitHub repository. The complete reviewed workflow is bundled at the repository root as
`SKILL.md`, `references/`, `assets/`, and `agents/`; it does not download replacement instructions
at runtime.

## Install

### Manus

Open **Skills**, select **+ Add → Import from GitHub**, and paste:

```text
https://github.com/aipass-one/aipass-integration-skill
```

### Bolt.new

Open the workspace **Skills library** or a project's **Settings → Skills**, select
**Add skill → From GitHub**, paste the same repository URL, and choose `aipass-integration`.

### Agent Skills installers

```bash
npx skills add aipass-one/aipass-integration-skill
```

With the current GitHub CLI Agent Skills commands:

```bash
gh skill install aipass-one/aipass-integration-skill aipass-integration
```

The open Agent Skills layout is also discovered natively when copied into a supported project or
user skill directory, including `.agents/skills/aipass-integration/` for GitHub Copilot, Codex,
Gemini CLI, OpenCode, and Windsurf. Platform-specific directories are supported too.

The complete multi-skill package and source history live at
[`aipass-one/skill`](https://github.com/aipass-one/skill).

## Updates

Releases are versioned so agents and reviewers can inspect exactly which workflow they install.
Update through the installer you used, or compare the next release before upgrading. The public
AI Pass documentation remains useful reference material, but it never replaces this installed
skill's instructions at runtime.

## Security

The skill never asks users to paste passwords, cookies, OAuth tokens, provider keys, wallet
credentials, device codes, or setup grants. Project setup authorization cannot spend wallet funds;
paid verification requires separate user approval.

## License

MIT
