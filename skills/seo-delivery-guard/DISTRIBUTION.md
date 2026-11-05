# Distribution

SEO Delivery Guard uses one frozen public source for every channel. Platform-specific metadata or archive layout may vary, but behavior, version, license, identity, and public content must remain identical.

## Channel classes

- Public source: GitHub as the global canonical repository and Gitee as the China mirror.
- Discovery and marketplaces: Skills.sh, ModelScope Skills Center, SkillHub, QoderWork, Kilo Marketplace, and any later channel with a verified official submission path.
- Compatible clients: clients that load portable `SKILL.md` packages but do not provide a separately verified public marketplace.
- Candidate channels: platforms whose current public submission or anonymous verification path has not been confirmed.

The exact enabled list is maintained privately and revalidated against current official platform rules on every release. Submission, local installation, review, and public publication are different states and must be reported separately.

Before any channel is marked `published`, freeze an immutable version and source revision, create the declared public artifact, record its file list, size, and SHA-256, verify anonymous access where the channel is public, install the remote artifact into an isolated supported client, and confirm actual discovery and invocation. A README, repository, tag, Release, uploaded archive, or successful submission alone is not publication proof.

The official website and canonical public repository must link to each other's exact product pages using ordinary crawlable HTTPS links. Do not publish a repository-specific URL, download command, version, checksum, compatibility claim, marketplace badge, or availability statement until that target has been read back and verified.

Private development controls, `AGENTS.md`, `.internal/`, CI configuration, credentials, platform adapters, policy snapshots, and release evidence are never part of the public repository or installable package.
