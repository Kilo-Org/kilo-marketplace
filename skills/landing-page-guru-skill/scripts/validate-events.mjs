import { addCheck, isMain, loadContract, parseArgs, readJSON, reportFor, writeReport } from './lib/common.mjs';

const states = new Set(['granted', 'denied', 'withdrawn', 'not-required']);
const kinds = new Set(['form-submit', 'cta-click', 'page-view']);
const outcomes = new Set(['accepted', 'rejected', 'timeout', 'duplicate', 'invalid', 'none']);
const opaque = value => typeof value === 'string' && /^[a-zA-Z0-9_-]{1,100}$/.test(value);
const personal = value => /@|bearer\s|https?:\/\/|(?:\+?\d[\s().-]*){9,}/i.test(String(value));

function permitted(definition, action, contract) {
  return definition.permission === 'none' || !contract.privacy.analyticsRequiresPermission || action.permission === 'granted';
}

function matches(definition, action) {
  if (definition.trigger === 'form-accepted') return action.kind === 'form-submit' && action.outcome === 'accepted';
  if (definition.trigger === 'submit-attempt') return action.kind === 'form-submit' && action.outcome !== 'invalid';
  return definition.trigger === action.kind;
}

export function validateEvents(contract, trace) {
  const report = reportFor(contract, 'validate-events', 'supplied-trace');
  report.limitations.push('Checks only the supplied trace. It does not establish live collection, storage, attribution, or causal conversion lift.');
  if (!trace || trace.schemaVersion !== '1.0' || trace.pageId !== contract.pageId || trace.environment !== contract.environment || !['synthetic', 'browser-observed'].includes(trace.source) || !Array.isArray(trace.actions) || !Array.isArray(trace.events)) {
    addCheck(report, 'trace-shape', false, 'Versioned trace matching the contract and declared source', 'Missing or inconsistent trace metadata');
    return report;
  }
  report.evidenceSource = trace.source;
  const actions = new Map();
  let malformed = false;
  for (const action of trace.actions) {
    if (!action || !opaque(action.id) || actions.has(action.id) || !kinds.has(action.kind) || !outcomes.has(action.outcome) || !states.has(action.permission) || (action.conversionId !== null && !opaque(action.conversionId)) || (action.kind === 'form-submit' && action.outcome === 'accepted' && !opaque(action.conversionId))) malformed = true;
    else actions.set(action.id, action);
  }
  addCheck(report, 'trace-actions', !malformed, 'Unique actions with valid outcomes, permissions, and opaque acceptance IDs', malformed ? 'Malformed or duplicate action metadata' : `${actions.size} actions inspected`);
  if (malformed) return report;
  if (!actions.size) {
    addCheck(report, 'trace-coverage', 'not-tested', 'At least one observed action', 'Empty trace cannot verify event behavior');
    return report;
  }
  const definitions = new Map(contract.events.map(event => [event.name, event]));
  const seenEventIds = new Set();
  const seenConversions = new Set();
  const actual = new Map();
  let unknown = 0, forbidden = 0, leaked = 0, repeated = 0, invalid = 0;
  for (const event of trace.events) {
    if (!event || !opaque(event.eventId) || !opaque(event.actionId) || !states.has(event.permission) || !event.properties || typeof event.properties !== 'object' || Array.isArray(event.properties)) { invalid++; continue; }
    const definition = definitions.get(event.name);
    const action = actions.get(event.actionId);
    if (!definition || !action) { unknown++; continue; }
    if (event.permission !== action.permission || !permitted(definition, action, contract) || !matches(definition, action)) forbidden++;
    if (seenEventIds.has(event.eventId)) repeated++;
    seenEventIds.add(event.eventId);
    if (definition.deduplication === 'conversion') {
      if (!opaque(event.conversionId) || event.conversionId !== action.conversionId) invalid++;
      const key = `${event.name}:${event.conversionId}`;
      if (seenConversions.has(key)) repeated++;
      seenConversions.add(key);
    }
    const safe = Object.entries(event.properties).every(([key, value]) => definition.properties.includes(key) && ['string', 'number', 'boolean'].includes(typeof value) && !personal(value));
    if (!safe) leaked++;
    const key = `${event.name}:${event.actionId}`;
    actual.set(key, (actual.get(key) ?? 0) + 1);
  }
  addCheck(report, 'known-events', unknown === 0 && invalid === 0, 'Every event maps to a known action and valid identifier', `${unknown} unknown mappings; ${invalid} malformed events`);
  addCheck(report, 'permission-and-outcome', forbidden === 0, 'No events for forbidden permissions or wrong outcomes', `${forbidden} semantic violations`);
  addCheck(report, 'property-allowlist', leaked === 0, 'Only allowlisted scalar properties without apparent personal data', `${leaked} unsafe property sets; values omitted`);
  addCheck(report, 'deduplication', repeated === 0, 'Unique event IDs and at most one acceptance per conversion', `${repeated} duplicate identity observations`);
  let missing = 0, extra = 0;
  const expectedConversions = new Set();
  for (const action of actions.values()) {
    for (const definition of definitions.values()) {
      let expected = matches(definition, action) && permitted(definition, action, contract) ? 1 : 0;
      if (expected && definition.deduplication === 'conversion') {
        const identity = `${definition.name}:${action.conversionId}`;
        if (expectedConversions.has(identity)) expected = 0;
        expectedConversions.add(identity);
      }
      const count = actual.get(`${definition.name}:${action.id}`) ?? 0;
      missing += Math.max(0, expected - count);
      extra += Math.max(0, count - expected);
    }
  }
  addCheck(report, 'expected-event-counts', missing === 0 && extra === 0, 'Events match eligible actions exactly', `${missing} missing; ${extra} unexpected`);
  const needsPermission = contract.events.some(event => event.permission === 'analytics') && contract.privacy.analyticsRequiresPermission;
  const coveredStates = new Set(trace.actions.map(action => action.permission));
  const uncovered = needsPermission ? contract.privacy.permissionStates.filter(state => !coveredStates.has(state)) : [];
  addCheck(report, 'permission-coverage', uncovered.length ? 'not-tested' : needsPermission ? 'pass' : 'not-applicable', 'Configured permission states appear in the trace', `${uncovered.length} configured states untested`);
  const acceptedRule = contract.events.some(event => event.trigger === 'form-accepted');
  const requiredOutcomes = ['accepted', 'rejected', 'timeout', 'duplicate'];
  const missingOutcomes = acceptedRule ? requiredOutcomes.filter(outcome => !trace.actions.some(action => action.kind === 'form-submit' && action.outcome === outcome)) : [];
  addCheck(report, 'acceptance-coverage', missingOutcomes.length ? 'not-tested' : acceptedRule ? 'pass' : 'not-applicable', 'Success, rejection, timeout, and duplicate actions are represented', `${missingOutcomes.length} outcomes untested`);
  return report;
}

async function main() {
  const options = parseArgs(process.argv.slice(2), { '--help': 'boolean', '--contract': 'value', '--trace': 'value', '--output': 'value' });
  if (options.help) {
    console.log('Usage: node validate-events.mjs --contract contract.json --trace trace.json [--output report.json]\nChecks supplied test actions/events; never contacts a collector.\nTrace: {schemaVersion:"1.0",pageId,environment,source:"synthetic"|"browser-observed",actions:[{id,kind,outcome,permission,conversionId}],events:[{name,actionId,eventId,conversionId,permission,properties}]}\nActions are chronological. kind: form-submit|cta-click|page-view. outcome: accepted|rejected|timeout|duplicate|invalid|none. permission: granted|denied|withdrawn|not-required.\nExit: 0 complete within scope, 1 failed check, 2 incomplete coverage, 3 invalid input. Reports omit raw values.');
    return;
  }
  if (!options.contract || !options.trace) throw new Error('Required: --contract and --trace');
  const contract = await loadContract(options.contract);
  process.exitCode = await writeReport(validateEvents(contract, await readJSON(options.trace)), options.output);
}

if (isMain(import.meta.url)) main().catch(() => { console.error('Event check failed to read valid inputs. Check paths, JSON, contract schema, and --help. No input values were logged.'); process.exitCode = 3; });
