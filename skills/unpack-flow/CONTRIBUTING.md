# Contributing to UnpackFlow

Contributions should preserve the cross-platform command contract, source-archive safety and public-source boundary. Run the relevant synthetic tests, `scripts/check-docs.sh`, both public Skill audits when PowerShell is available, and `scripts/check-anonymization.sh` before submitting a change.

Do not commit private acceptance evidence, infrastructure topology, marketplace coordination notes or VM images. Those records belong to the maintainer's private source repository and are deliberately excluded from public exports.

## Public test-data anonymization baseline

All files shipped in the repository or release archives must use synthetic test fixtures. Public documentation, examples, logs, screenshots, scripts, manifests and regression evidence must not reveal the origin of private test data.

## Allowed fixture vocabulary

Use descriptive synthetic names that communicate the scenario without resembling a real customer, product, order, machine or dated working directory:

| Purpose | Approved example |
|---|---|
| Ordinary archive | `sample-backup.zip` |
| Multipart archive | `sample-multipart.part1.exe` |
| Source context | `legacy-set` |
| Collision-safe output | `sample-backup-legacy-set-unpacked` |
| Unicode path | `示例资料/归档包.zip` |
| Shared fixture root | `/data/unpack-flow-testcases` |

The fixture root is only a public default. Native environments may override it with `UNPACK_FLOW_TEST_ROOT`; their real hostnames and private paths must stay in private operator records.

## Prohibited content

- Customer, game, product, order, ticket or asset identifiers copied from real data.
- Personal names, account names, email addresses or machine numbers used as test cases, except the explicitly published project identity in `PUBLISHER.md`.
- Dated source-folder names copied from an operator workstation.
- Internal host numbers, infrastructure labels, mount points, home directories or private repository URLs.
- Statements that a public fixture was derived from, observed in or copied from a private archive collection.
- Real filenames merely transliterated, abbreviated or partially masked.

## Fixture construction

Generate payload text, filenames and archive layouts from deterministic synthetic inputs. Include only the minimum bytes needed to reproduce the behavior. For multipart and SFX coverage, package inert payloads and never execute the generated executable-shaped archive.

Record the generator, fixture version, size and SHA-256. A public fixture is acceptable only when it can be regenerated without private source files and a repository-wide anonymization scan passes.

## Evidence boundary

Public regression records describe the operating system class, fixture name, checksum result, exit code and output counts. Exact private hostnames, IP addresses, operator paths, VM storage locations and historical archive names belong only in access-controlled operator evidence.
