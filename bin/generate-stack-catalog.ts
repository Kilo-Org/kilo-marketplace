#!/usr/bin/env npx tsx
/**
 * Validate and generate the Kilo Stack catalog served artifact.
 *
 * Reads `stack/catalog.yaml`, enforces integrity rules (resource ID existence,
 * taxonomy structure, trust-policy compliance), stamps `curated: true` on all
 * associations, and writes the serve artifact to `stack/marketplace.json`.
 *
 * Usage: npx tsx bin/generate-stack-catalog.ts [--check]
 *   --check  Exit with a non-zero code if the artifact would change (CI mode).
 *
 * Environment:
 *   KILO_MARKETPLACE_STRICT  If set, reject resources not in the marketplace MCP/skill
 *                            inventories (for post-seeding validation). By default,
 *                            unknown IDs are logged as warnings only.
 */

import * as fs from "fs"
import * as path from "path"
import * as yaml from "yaml"
import { repoPathFromBin, listVisibleDirectories, loadMcpIds } from "./marketplace-generator-utils.ts"

const CHECK_MODE = process.argv.includes("--check")
const STRICT = Boolean(process.env.KILO_MARKETPLACE_STRICT)

const catalogPath = repoPathFromBin("stack", "catalog.yaml")
const artifactPath = repoPathFromBin("stack", "marketplace.json")
const mcpsDir = repoPathFromBin("mcps")
const skillsDir = repoPathFromBin("skills")

// ── Types (loose — validated manually below) ─────────────────────────────────

interface CatalogAssociation {
  ref: string
  default: boolean
  curated?: boolean
  trust: string
  maturity: string
  source: string
  rationale: string
  warnings: string[]
  deprecated?: boolean
  replacement?: string
}

interface CatalogTechnology {
  id: string
  name: string
  resources: CatalogAssociation[]
}

interface CatalogPlacement {
  technology: string
  note?: string
}

interface CatalogCategory {
  id: string
  name: string
  technologies: CatalogPlacement[]
  categories: CatalogCategory[]
}

interface CatalogResource {
  ref: string
  id: string
  kind: "skill" | "mcp"
  name: string
  trust: string
  maturity: string
  source: string
  warnings: string[]
}

interface CatalogVertical {
  id: string
  name: string
  technologies: CatalogTechnology[]
  categories: CatalogCategory[]
}

interface Catalog {
  revision: string
  verticals: CatalogVertical[]
  resources: CatalogResource[]
}

// ── Validation ───────────────────────────────────────────────────────────────

const VALID_MATURITY = new Set(["stable", "preview", "beta", "experimental", "alpha", "unsupported"])
const VALID_TRUST = new Set(["official", "provider", "community"])
const KEBAB = /^[a-z0-9]+(?:-[a-z0-9]+)*$/
const REVISION = /^\d{4}-\d{2}-\d{2}\.\d+$/
const HTTPS = /^https:\/\//
const QUALIFIED_REF = /^(?:skill|mcp):[a-z0-9]+(?:-[a-z0-9]+)*$/

function requireKebab(value: unknown, path: string): string {
  if (typeof value !== "string" || !KEBAB.test(value)) {
    throw new Error(`${path}: expected kebab-case string, got ${JSON.stringify(value)}`)
  }
  return value
}

function requireString(value: unknown, path: string): string {
  if (typeof value !== "string" || !value.trim()) {
    throw new Error(`${path}: expected non-empty string`)
  }
  return value
}

function requireRef(value: unknown, path: string): string {
  if (typeof value !== "string" || !QUALIFIED_REF.test(value)) {
    throw new Error(`${path}: expected qualified ref (skill:id or mcp:id), got ${JSON.stringify(value)}`)
  }
  return value
}

function validateResource(raw: unknown, path: string): CatalogResource {
  if (!raw || typeof raw !== "object" || Array.isArray(raw)) throw new Error(`${path}: expected object`)
  const r = raw as Record<string, unknown>
  const ref = requireRef(r.ref, `${path}.ref`)
  const id = requireKebab(r.id, `${path}.id`)
  if (r.kind !== "skill" && r.kind !== "mcp") throw new Error(`${path}.kind: must be "skill" or "mcp"`)
  if (ref !== `${r.kind}:${id}`) throw new Error(`${path}: ref "${ref}" must match kind:id "${r.kind}:${id}"`)
  if (!VALID_TRUST.has(r.trust as string)) throw new Error(`${path}.trust: invalid value "${r.trust}"`)
  if (!VALID_MATURITY.has(r.maturity as string)) throw new Error(`${path}.maturity: invalid value "${r.maturity}"`)
  if (!HTTPS.test(r.source as string)) throw new Error(`${path}.source: must be an HTTPS URL`)
  requireString(r.name, `${path}.name`)
  if (!Array.isArray(r.warnings)) throw new Error(`${path}.warnings: must be an array`)
  return r as unknown as CatalogResource
}

/**
 * Validate and enrich an association entry.
 * The YAML source only needs  `ref`, `default`, and optionally `rationale`,
 * `deprecated`, and `replacement`. All other fields (trust, maturity, source,
 * warnings) are auto-filled from the resources registry.
 */
function validateAssociation(raw: unknown, path: string, registered: Map<string, CatalogResource>): CatalogAssociation {
  if (!raw || typeof raw !== "object" || Array.isArray(raw)) throw new Error(`${path}: expected object`)
  const a = raw as Record<string, unknown>
  const ref = requireRef(a.ref, `${path}.ref`)
  if (typeof a.default !== "boolean") throw new Error(`${path}.default: must be boolean`)
  const resource = registered.get(ref)
  if (!resource) throw new Error(`${path}: ref "${ref}" is not in the resources registry`)

  // Trust-policy enforcement: only defaultable resources may carry default:true.
  if (a.default === true) {
    const ok =
      resource.kind === "mcp" ||
      (resource.kind === "skill" && resource.trust === "official" && resource.maturity === "stable")
    if (!ok) {
      throw new Error(
        `${path}: ref "${ref}" has default:true but is not a stable official Skill or an MCP (kind=${resource.kind}, trust=${resource.trust}, maturity=${resource.maturity})`,
      )
    }
  }

  // Auto-fill metadata from the resources registry if not provided in the source.
  const trust = typeof a.trust === "string" ? a.trust : resource.trust
  const maturity = typeof a.maturity === "string" ? a.maturity : resource.maturity
  const source = typeof a.source === "string" ? a.source : resource.source
  const warnings = Array.isArray(a.warnings) ? a.warnings as string[] : resource.warnings
  const rationale = typeof a.rationale === "string" && a.rationale.trim()
    ? a.rationale
    : a.default === true
      ? resource.kind === "mcp"
        ? "MCP server enabled by default; complete authentication after installation."
        : "Stable first-party Skill recommended by the Data Engineering catalog."
      : "Optional Skill candidate requiring explicit review and selection."

  return {
    ref,
    default: a.default as boolean,
    trust,
    maturity,
    source,
    rationale,
    warnings,
    ...(a.deprecated !== undefined ? { deprecated: a.deprecated as boolean } : {}),
    ...(a.replacement !== undefined ? { replacement: a.replacement as string } : {}),
  } as unknown as CatalogAssociation
}

function validateCategories(
  cats: unknown[],
  path: string,
  inVertical: Set<string>,
  seen: Set<string>,
  counts: Map<string, number>,
): void {
  for (const cat of cats) {
    if (!cat || typeof cat !== "object" || Array.isArray(cat)) throw new Error(`${path}: category must be an object`)
    const c = cat as Record<string, unknown>
    const id = requireKebab(c.id, `${path}.id`)
    requireString(c.name, `${path}.name`)
    if (seen.has(id)) throw new Error(`${path}: category id "${id}" is duplicated`)
    seen.add(id)
    if (!Array.isArray(c.technologies)) throw new Error(`${path}.technologies: must be an array`)
    const placed = new Set<string>()
    for (const placement of c.technologies as unknown[]) {
      if (!placement || typeof placement !== "object") throw new Error(`${path}: placement must be an object`)
      const p = placement as Record<string, unknown>
      const tech = requireKebab(p.technology, `${path}.technology`)
      if (placed.has(tech)) throw new Error(`${path}: technology "${tech}" placed more than once in category "${id}"`)
      placed.add(tech)
      if (!inVertical.has(tech)) throw new Error(`${path}: technology "${tech}" is not registered in this vertical`)
      counts.set(tech, (counts.get(tech) ?? 0) + 1)
    }
    if (!Array.isArray(c.categories)) throw new Error(`${path}.categories: must be an array`)
    validateCategories(c.categories, `${path}.categories`, inVertical, seen, counts)
  }
}

function validate(catalog: Catalog, mcpIds: Set<string>, skillIds: Set<string>): string[] {
  const warnings: string[] = []

  if (!REVISION.test(catalog.revision)) {
    throw new Error(`revision: must match YYYY-MM-DD.N, got "${catalog.revision}"`)
  }

  // Register all resources
  const registered = new Map<string, CatalogResource>()
  const associated = new Set<string>()
  for (const r of catalog.resources) {
    const res = validateResource(r, `resources.${r.ref}`)
    if (registered.has(res.ref)) throw new Error(`resources: duplicate ref "${res.ref}"`)
    registered.set(res.ref, res)

    // Check existence in marketplace inventories
    if (res.kind === "mcp" && !mcpIds.has(res.id)) {
      const msg = `resources.${res.ref}: MCP id "${res.id}" is not in mcps/`
      if (STRICT) throw new Error(msg)
      else warnings.push(`WARN ${msg}`)
    }
    if (res.kind === "skill" && !skillIds.has(res.id)) {
      const msg = `resources.${res.ref}: Skill id "${res.id}" is not in skills/`
      if (STRICT) throw new Error(msg)
      else warnings.push(`WARN ${msg}`)
    }
  }

  // Validate verticals
  const allTechs = new Map<string, string>() // id → vertical id
  for (const v of catalog.verticals) {
    requireKebab(v.id, `verticals.${v.id}.id`)
    requireString(v.name, `verticals.${v.id}.name`)
    const inVertical = new Set<string>()
    for (const tech of v.technologies) {
      requireKebab(tech.id, `verticals.${v.id}.technologies.${tech.id}.id`)
      requireString(tech.name, `verticals.${v.id}.technologies.${tech.id}.name`)
      if (allTechs.has(tech.id)) {
        throw new Error(`verticals.${v.id}: technology id "${tech.id}" is already registered in vertical "${allTechs.get(tech.id)}"`)
      }
      allTechs.set(tech.id, v.id)
      inVertical.add(tech.id)
      const assocRefs = new Set<string>()
      for (let i = 0; i < tech.resources.length; i++) {
        const a = validateAssociation(tech.resources[i], `verticals.${v.id}.technologies.${tech.id}.resources.${tech.resources[i].ref}`, registered)
        if (assocRefs.has(a.ref)) throw new Error(`verticals.${v.id}.technologies.${tech.id}: ref "${a.ref}" repeated`)
        assocRefs.add(a.ref)
        associated.add(a.ref)
        tech.resources[i] = a
      }
    }
    const catSeen = new Set<string>()
    const catCounts = new Map<string, number>()
    validateCategories(v.categories, `verticals.${v.id}.categories`, inVertical, catSeen, catCounts)
    for (const id of inVertical) {
      if (!catCounts.has(id)) warnings.push(`WARN verticals.${v.id}: technology "${id}" has no category placement`)
    }
  }

  // Every resource must be referenced by at least one technology
  for (const ref of registered.keys()) {
    if (!associated.has(ref)) warnings.push(`WARN resources.${ref}: not associated with any technology`)
  }

  return warnings
}

// ── Main ─────────────────────────────────────────────────────────────────────

const raw = fs.readFileSync(catalogPath, "utf-8")
const parsed = yaml.parse(raw) as Catalog

const mcpIds = loadMcpIds(mcpsDir)
const skillIds = new Set(listVisibleDirectories(skillsDir))

console.log(`\nValidating stack/catalog.yaml (revision: ${parsed.revision})`)
const warnings = validate(parsed, mcpIds, skillIds)
for (const w of warnings) console.log(w)

// Stamp curated:true on all associations before publishing
for (const vertical of parsed.verticals) {
  for (const tech of vertical.technologies) {
    for (const assoc of tech.resources) {
      assoc.curated = true
    }
  }
}

const artifact = JSON.stringify(parsed, null, 2)

if (CHECK_MODE) {
  const existing = fs.existsSync(artifactPath) ? fs.readFileSync(artifactPath, "utf-8") : ""
  if (existing !== `${artifact}\n`) {
    console.error("\nstack/marketplace.json is stale. Run: npx tsx bin/generate-stack-catalog.ts")
    process.exit(1)
  }
  console.log("\nstack/marketplace.json is up to date.")
} else {
  fs.writeFileSync(artifactPath, `${artifact}\n`)
  console.log(`\nWrote stack/marketplace.json (${parsed.verticals.length} vertical(s), ${parsed.resources.length} resource(s))`)
}
