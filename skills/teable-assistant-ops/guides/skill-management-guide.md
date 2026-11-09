# Skill Management Guide

Managed skills are independent of the current project. Choose scope by intended audience: `user` for personal reuse, `base` or `space` for shared context, and `app`, `cuppyclaw`, or `routine` for one runtime.

## Scope Resolution

- Project and space imports and lists need an explicit scope ID; configured project context is not substituted for it.
- App, CuppyClaw, and routine operations can fall back to `TEABLE_APP_ID`, `TEABLE_BOT_ID`, and `TEABLE_ROUTINE_ID`; pass the ID when environment context could be ambiguous.
- A user-scope list normally shows personal skills. Add project context only when the agent needs skills available through that project.
- Use the available list when looking for chat slash-command exposure; use the managed list when locating a skill to configure.
- Enabled state accepts only the boolean strings `true` and `false`; verify the skill ID before changing it.

## Import Workflow

1. Choose the narrowest scope that should own the skill.
2. Import it, then list that scope to verify ownership and obtain the skill ID.
3. Change enabled state only after verifying the ID and scope.

GitHub imports require a URL to the skill directory, not the repository root. The URL must include `/tree/<ref>/<path>` (or `/blob/<ref>/<path>`):

```bash
teable skill import-github --scope-type base --scope-id bseXXXX --url https://github.com/owner/repo/tree/main/skills/my-skill
```

For local imports, both `.skill` and `.zip` filenames are accepted, but the content must be a valid ZIP archive. Importing does not infer a target from the configured project; scope must be chosen explicitly.
