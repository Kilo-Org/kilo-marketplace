import { readFile, mkdir, writeFile } from 'node:fs/promises';
import { realpathSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { pathToFileURL, fileURLToPath } from 'node:url';
import { createRequire } from 'node:module';

export async function readJSON(path) {
  return JSON.parse(await readFile(path, 'utf8'));
}

// Implements only the keywords used in our bundled schema, not a general JSON Schema engine.
export function validateShape(value, schema, root = schema, path = '$', errors = []) {
  if (schema.$ref) {
    const target = schema.$ref.split('/').slice(1).reduce((object, key) => object[key], root);
    return validateShape(value, target, root, path, errors);
  }
  const type = value === null ? 'null' : Array.isArray(value) ? 'array' : typeof value;
  if (schema.type) {
    const types = [].concat(schema.type);
    if (!types.includes(type) && !(types.includes('integer') && Number.isInteger(value))) {
      errors.push(`${path}: invalid type`);
      return errors;
    }
  }
  if ('const' in schema && value !== schema.const) errors.push(`${path}: invalid constant`);
  if (schema.enum && !schema.enum.includes(value)) errors.push(`${path}: invalid option`);
  if (typeof value === 'string') {
    if (schema.minLength && value.length < schema.minLength) errors.push(`${path}: too short`);
    if (schema.pattern && !new RegExp(schema.pattern).test(value)) errors.push(`${path}: invalid format`);
  }
  if (typeof value === 'number') {
    if (schema.minimum !== undefined && value < schema.minimum) errors.push(`${path}: below minimum`);
    if (schema.maximum !== undefined && value > schema.maximum) errors.push(`${path}: above maximum`);
  }
  if (Array.isArray(value)) {
    if (schema.uniqueItems && new Set(value.map(item => JSON.stringify(item))).size !== value.length) errors.push(`${path}: duplicate items`);
    if (schema.items) value.forEach((item, i) => validateShape(item, schema.items, root, `${path}[${i}]`, errors));
  } else if (value && typeof value === 'object') {
    for (const key of schema.required ?? []) if (!Object.hasOwn(value, key)) errors.push(`${path}.${key}: required`);
    for (const [key, item] of Object.entries(value)) {
      if (Object.hasOwn(schema.properties ?? {}, key)) validateShape(item, schema.properties[key], root, `${path}.${key}`, errors);
      else if (schema.additionalProperties === false) errors.push(`${path}: unexpected property`);
      else if (typeof schema.additionalProperties === 'object') validateShape(item, schema.additionalProperties, root, `${path}.*`, errors);
    }
  }
  return errors;
}

export function safeURL(input, base) {
  const url = new URL(input, base);
  if (!['http:', 'https:'].includes(url.protocol) || url.username || url.password) throw new Error('Expected an HTTP(S) URL without credentials');
  if (url.search || url.hash) throw new Error('Test URLs must not contain query strings or fragments');
  return url;
}

export function validateContract(contract, schema) {
  const errors = validateShape(contract, schema);
  if (errors.length) return errors;
  const { form, events, privacy, verification } = contract;
  if (form.mode !== 'unconnected' && !form.destination.endpoint) errors.push('$.form.destination.endpoint: connected mode requires endpoint');
  if (form.mode === 'unconnected' && contract.capabilities.backendAcceptance) errors.push('$.capabilities.backendAcceptance: unavailable in unconnected mode');
  if (form.success.mode === 'redirect' && !form.success.redirectPath) errors.push('$.form.success.redirectPath: required for redirect');
  if (form.responses.retrySafe && !form.responses.idempotencyHeader) errors.push('$.form.responses.idempotencyHeader: helper requires a retry identity header');
  if (form.responses.idempotencyHeader && !/^[a-zA-Z0-9-]+$/.test(form.responses.idempotencyHeader)) errors.push('$.form.responses.idempotencyHeader: invalid header');
  if (new Set(form.fields.map(field => field.name)).size !== form.fields.length) errors.push('$.form.fields: duplicate names');
  if (new Set(events.map(event => event.name)).size !== events.length) errors.push('$.events: duplicate names');
  for (const event of events) {
    if (event.trigger === 'form-accepted' && (event.successPredicate !== 'accepted' || event.deduplication !== 'conversion')) errors.push('$.events: acceptance needs an accepted outcome and conversion deduplication');
    if (event.trigger !== 'form-accepted' && (event.successPredicate !== 'action' || event.deduplication !== 'action')) errors.push('$.events: action event needs action semantics');
    if (event.properties.some(property => /email|phone|name|token|secret|password|message|url|query/i.test(property))) errors.push('$.events: sensitive property in allowlist');
  }
  if (privacy.analyticsRequiresPermission && !privacy.permissionStates.includes('granted')) errors.push('$.privacy.permissionStates: missing granted state');
  try {
    safeURL(verification.target);
    if (form.destination.endpoint) safeURL(form.destination.endpoint, verification.target);
    if (form.success.redirectPath) safeURL(form.success.redirectPath, verification.target);
  } catch { errors.push('$.verification: use HTTP(S) targets without credentials, queries or fragments'); }
  if (verification.browser) {
    for (const field of form.fields.filter(field => field.required && field.type !== 'hidden')) {
      if (!Object.hasOwn(verification.browser.values, field.name)) errors.push('$.verification.browser.values: missing required synthetic field');
    }
    for (const key of Object.keys(verification.browser.values)) if (!form.fields.some(field => field.name === key)) errors.push('$.verification.browser.values: unknown field');
  }
  return errors;
}

export async function loadContract(path) {
  const schema = await readJSON(new URL('../../assets/integration-contract.schema.json', import.meta.url));
  const contract = await readJSON(path);
  const errors = validateContract(contract, schema);
  if (errors.length) throw new Error(`Invalid contract:\n${errors.join('\n')}`);
  return contract;
}

export function parseArgs(argv, permitted) {
  const result = {};
  for (let i = 0; i < argv.length; i++) {
    const name = argv[i];
    if (!Object.hasOwn(permitted, name)) throw new Error(`Unknown option: ${name}`);
    if (permitted[name] === 'boolean') result[name.slice(2)] = true;
    else {
      if (!argv[i + 1] || argv[i + 1].startsWith('--')) throw new Error(`Missing value for ${name}`);
      result[name.slice(2)] = argv[++i];
    }
  }
  return result;
}

export function reportFor(contract, tool, evidenceSource) {
  return { schemaVersion: '1.0', tool, toolVersion: '0.1.0', pageId: contract.pageId, environment: contract.environment, timestamp: new Date().toISOString(), runtime: process.version, evidenceSource, checks: [], limitations: [] };
}

export function addCheck(report, id, passed, expected, observation) {
  report.checks.push({ id, status: typeof passed === 'string' ? passed : passed ? 'pass' : 'fail', expected, observation });
}

export function finishReport(report) {
  report.summary = Object.fromEntries(['pass', 'fail', 'not-tested', 'not-applicable'].map(status => [status, report.checks.filter(check => check.status === status).length]));
  return report;
}

export async function writeReport(report, path) {
  const output = JSON.stringify(finishReport(report), null, 2) + '\n';
  if (path) { await mkdir(dirname(resolve(path)), { recursive: true }); await writeFile(path, output); }
  else process.stdout.write(output);
  return report.summary.fail ? 1 : report.summary['not-tested'] ? 2 : 0;
}

export async function loadBrowser(modulePath) {
  if (modulePath) return import(pathToFileURL(resolve(modulePath)).href);
  const require = createRequire(resolve('package.json'));
  try { return await import(pathToFileURL(require.resolve('playwright')).href); }
  catch { throw new Error('Playwright unavailable; use an existing project installation or --browser-module /path/to/playwright/index.mjs'); }
}

export function isMain(url) {
  if (!process.argv[1]) return false;
  try { return realpathSync(process.argv[1]) === realpathSync(fileURLToPath(url)); }
  catch { return false; }
}
