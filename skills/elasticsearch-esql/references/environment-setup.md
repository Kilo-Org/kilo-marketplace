# Environment Configuration

Elasticsearch connection is configured via environment variables. Run `node scripts/esql.js test` to verify the
connection. If the test fails, suggest these setup options to the user, then stop. Do not try to explore further until a
successful connection test.

> **Elastic Cloud Serverless:** After connecting, inspect `GET /`. If `build_flavor` is `"serverless"`, do **not** use
> `version.number` to decide which ES|QL features are allowed — Serverless tracks current GA and preview ES|QL, and the
> reported version follows the main-line / next-minor line (semver-only clients may see it as “latest”). Prefer
> `build_flavor` for detection and gating. For the full rules (including self-managed and snapshot builds), read
> **Cluster Detection** in [SKILL.md](../SKILL.md) and the **Serverless** callout in
> [ES|QL Version History](esql-version-history.md).

## Option 1: Elastic Cloud (recommended for production)

```bash
export ELASTICSEARCH_CLOUD_ID="deployment-name:base64encodedcloudid"
export ELASTICSEARCH_API_KEY="base64encodedapikey"
```

## Option 2: Direct URL with API Key

```bash
export ELASTICSEARCH_URL="https://elasticsearch:9200"
export ELASTICSEARCH_API_KEY="base64encodedapikey"
```

## Option 3: Basic Authentication

```bash
export ELASTICSEARCH_URL="https://elasticsearch:9200"
export ELASTICSEARCH_USERNAME="elastic"
read -r -s -p "Elasticsearch password: " ELASTICSEARCH_PASSWORD
printf '\n'
export ELASTICSEARCH_PASSWORD
```

## Option 4: Local Development with start-local

For local development and testing, [start-local](https://github.com/elastic/start-local) can create Elasticsearch and
Kibana containers with Docker or Podman. It downloads code and creates containers, volumes, credentials, and local
files: obtain the user's explicit consent for the reviewed source/ref and those effects before downloading or running it.
Never pipe a network response directly to a shell.

Use a pinned release or commit, inspect the script, and verify it against a checksum obtained through a trusted release
page or an organization security review:

```bash
START_LOCAL_REF="<PINNED_RELEASE_OR_COMMIT>"
EXPECTED_SHA256="<TRUSTED_SHA256>"
DOWNLOAD_DIR=$(mktemp -d)
SCRIPT="$DOWNLOAD_DIR/start-local.sh"

curl --fail --location --proto '=https' --tlsv1.2 \
  --output "$SCRIPT" \
  "https://raw.githubusercontent.com/elastic/start-local/${START_LOCAL_REF}/start-local.sh"
chmod 0600 "$SCRIPT"

# Review the complete file and its requested Docker/Podman resources.
less "$SCRIPT"
printf '%s  %s\n' "$EXPECTED_SHA256" "$SCRIPT" | sha256sum --check --strict

# Run only after checksum verification and a second explicit execution consent.
sh "$SCRIPT"
rm -f "$SCRIPT"
rmdir "$DOWNLOAD_DIR"
```

Do not execute the script if a trusted expected checksum is unavailable or verification fails. Instead, follow the
manual, pinned installation instructions in the official repository and have the downloaded files reviewed.

After installation completes, Elasticsearch runs at `http://localhost:9200` and Kibana at `http://localhost:5601`. The
script generates a random password for the `elastic` user and an API key, both stored in the `.env` file inside the
created `elastic-start-local` folder; keep that file mode `0600` and out of version control.

To configure the environment variables for this skill, source the `.env` file and export the connection settings:

```bash
source elastic-start-local/.env
export ELASTICSEARCH_URL="$ES_LOCAL_URL"
export ELASTICSEARCH_API_KEY="$ES_LOCAL_API_KEY"
```

Then run `node scripts/esql.js test` to verify the connection.

## Optional: Skip TLS verification (development only)

```bash
export ELASTICSEARCH_INSECURE="true"
```
