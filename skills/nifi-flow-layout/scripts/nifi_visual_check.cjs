#!/usr/bin/env node
const fs = require('fs');
const path = require('path');
let chromium;
try {
  ({ chromium } = require('playwright'));
} catch (e) {
  console.error('Playwright is required for NiFi visual checks. Install it with: npm install -D playwright && npx playwright install chromium');
  console.error(e && e.message ? e.message : e);
  process.exit(2);
}

function arg(name, fallback = undefined) {
  const i = process.argv.indexOf(`--${name}`);
  return i >= 0 ? process.argv[i + 1] : fallback;
}
function has(name) { return process.argv.includes(`--${name}`); }

function readPassphrase() {
  const direct = arg('passphrase');
  if (direct) return direct;
  const file = arg('passphrase-file');
  if (!file) return '';
  const key = arg('passphrase-key');
  const lines = fs.readFileSync(file, 'utf8').split(/\r?\n/).map(s => s.trim());
  if (!key) return lines.find(Boolean) || '';
  for (let i = 0; i < lines.length; i++) {
    if (lines[i].toUpperCase().startsWith(key.toUpperCase())) {
      return lines[i + 2] || lines[i + 1] || '';
    }
  }
  return '';
}

(async () => {
  const url = arg('url');
  if (!url) throw new Error('--url is required');
  const out = arg('out', path.resolve(process.cwd(), 'nifi-layout-screenshot.png'));
  const jsonOut = arg('json');
  const tileGrid = arg('tile-grid', '');
  const tileDir = arg('tile-dir', '');
  const origin = arg('origin') || new URL(url).origin;
  const viewport = { width: Number(arg('width', '1800')), height: Number(arg('height', '1200')) };
  const launch = { headless: !has('headed') };
  const contextOptions = { ignoreHTTPSErrors: true, viewport };
  const p12 = arg('p12');
  if (p12) {
    contextOptions.clientCertificates = [{ origin, pfx: fs.readFileSync(p12), passphrase: readPassphrase() }];
  }
  const cert = arg('cert');
  const key = arg('key');
  if (cert && key) {
    contextOptions.clientCertificates = [{ origin, cert: fs.readFileSync(cert), key: fs.readFileSync(key), passphrase: readPassphrase() }];
  }

  const browser = await chromium.launch(launch);
  const context = await browser.newContext(contextOptions);
  const page = await context.newPage();
  await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 60000 });
  await page.waitForTimeout(Number(arg('wait', '8000')));

  if (has('hide-controls')) {
    await page.addStyleTag({ content: `
      graph-controls,
      .graph-controls,
      navigation-control,
      operation-control {
        display: none !important;
        visibility: hidden !important;
      }
    ` });
    await page.waitForTimeout(300);
  }

  const data = await page.evaluate(() => {
    const box = el => {
      const r = el.getBoundingClientRect();
      return { x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height) };
    };
    const intersects = (a, b, pad = 0) => !(a.x + a.w <= b.x - pad || a.x >= b.x + b.w + pad || a.y + a.h <= b.y - pad || a.y >= b.y + b.h + pad);
    const LABEL_CLEARANCE = 12;
    const COMPONENT_CLEARANCE = 12;
    const LINE_SPACING = 32;
    const rectDistance = (p, r) => {
      const dx = Math.max(r.x - p.x, 0, p.x - (r.x + r.w));
      const dy = Math.max(r.y - p.y, 0, p.y - (r.y + r.h));
      return Math.hypot(dx, dy);
    };
    const rangeOverlap = (a1, a2, b1, b2) => Math.max(0, Math.min(a2, b2) - Math.max(a1, b1));
    const dataIds = el => {
      const d = el.__data__ || {};
      const e = d.entity || {};
      const c = e.component || e || {};
      return {
        sourceId: c.source?.id || c.sourceId || '',
        destId: c.destination?.id || c.destinationId || '',
        sourceGroupId: c.sourceGroupId || c.source?.groupId || '',
        destGroupId: c.destinationGroupId || c.destination?.groupId || ''
      };
    };
    const components = [...document.querySelectorAll('g.component')].map(el => ({
      id: el.id,
      rawId: el.id.replace(/^id-/, ''),
      cls: el.getAttribute('class'),
      text: (el.textContent || '').trim().replace(/\s+/g, ' ').slice(0, 120),
      box: box(el)
    }));
    const labels = [...document.querySelectorAll('g.connection-label-container')].map(el => {
      const g = el.closest('g.connection');
      return {
        id: g?.id || el.id,
        text: (el.textContent || '').trim().replace(/\s+/g, ' ').slice(0, 120),
        box: box(el)
      };
    });
    const connections = [...document.querySelectorAll('g.connection')].map(el => ({
      id: el.id,
      cls: el.getAttribute('class'),
      text: (el.textContent || '').trim().replace(/\s+/g, ' ').slice(0, 120),
      box: box(el),
      ...dataIds(el)
    }));
    const issues = [];
    for (const l of labels) {
      for (const c of components) {
        // A label that is merely flush against a component still hides arrows
        // and looks like an overlap in the NiFi canvas. Use a small positive
        // padding, not a negative tolerance.
        if (intersects(l.box, c.box, 3)) {
          issues.push({ type: 'label_overlaps_component', connection: l.id, component: c.id, label: l.box, componentBox: c.box });
        }
      }
    }
    for (let i = 0; i < labels.length; i++) {
      for (let j = i + 1; j < labels.length; j++) {
        if (intersects(labels[i].box, labels[j].box, -1)) {
          issues.push({ type: 'label_overlaps_label', a: labels[i].id, b: labels[j].id, boxA: labels[i].box, boxB: labels[j].box });
        }
      }
    }
    for (const g of [...document.querySelectorAll('g.connection')]) {
      const ids = dataIds(g);
      const path = g.querySelector('path.connection-path');
      if (!path || !path.getTotalLength) continue;
      const toScreen = p => {
        const svg = path.ownerSVGElement;
        const m = path.getScreenCTM();
        if (!svg || !m) return p;
        const pt = svg.createSVGPoint();
        pt.x = p.x; pt.y = p.y;
        const q = pt.matrixTransform(m);
        return { x: q.x, y: q.y };
      };
      const len = path.getTotalLength();
      const steps = Math.max(12, Math.min(200, Math.ceil(len / 10)));
      const startPoint = toScreen(path.getPointAtLength(0));
      const endPoint = toScreen(path.getPointAtLength(len));
      const nearestComponent = p => {
        let best = null;
        let bestD = Infinity;
        for (const c of components) {
          const d = rectDistance(p, c.box);
          if (d < bestD) { bestD = d; best = c; }
        }
        return bestD <= 70 ? best : null;
      };
      const inferredEndpoints = [nearestComponent(startPoint), nearestComponent(endPoint)].filter(Boolean);
      const endpointComponentsForPath = components.filter(c =>
        c.rawId === ids.sourceId || c.rawId === ids.destId || c.rawId === ids.sourceGroupId || c.rawId === ids.destGroupId ||
        inferredEndpoints.some(e => e.id === c.id)
      );
      const endpointIdsForPath = new Set(endpointComponentsForPath.map(c => c.id));
      const seenCloseLabels = new Set();
      const seenCloseComponents = new Set();
      for (let i = 2; i < steps - 2; i++) {
        const frac = i / steps;
        const p = toScreen(path.getPointAtLength(len * frac));
        const probe = { x: p.x - 1, y: p.y - 1, w: 2, h: 2 };
        for (const l of labels) {
          if (l.id === g.id || seenCloseLabels.has(l.id)) continue;
          const d = rectDistance(p, l.box);
          if (d < LABEL_CLEARANCE) {
            issues.push({
              type: 'path_too_close_to_label',
              connection: g.id,
              labelConnection: l.id,
              clearance: Math.round(d),
              required: LABEL_CLEARANCE,
              at: { x: Math.round(p.x), y: Math.round(p.y) },
              label: l.box
            });
            seenCloseLabels.add(l.id);
          }
        }
        for (const c of components) {
          const rid = c.rawId;
          if (rid === ids.sourceId || rid === ids.destId || rid === ids.sourceGroupId || rid === ids.destGroupId || endpointIdsForPath.has(c.id)) continue;
          if (intersects(probe, c.box, 2)) {
            if (frac < 0.10 || frac > 0.90) continue;
            const nearBoundary =
              Math.abs(p.x - c.box.x) <= 5 ||
              Math.abs(p.x - (c.box.x + c.box.w)) <= 5 ||
              Math.abs(p.y - c.box.y) <= 5 ||
              Math.abs(p.y - (c.box.y + c.box.h)) <= 5;
            issues.push({
              type: nearBoundary ? 'path_touches_component_edge' : 'path_crosses_component',
              connection: g.id,
              component: c.id,
              at: { x: Math.round(p.x), y: Math.round(p.y) }
            });
            i = steps;
            break;
          }
          if (frac >= 0.10 && frac <= 0.90 && !seenCloseComponents.has(c.id)) {
            const d = rectDistance(p, c.box);
            if (d < COMPONENT_CLEARANCE) {
              issues.push({
                type: 'path_too_close_to_component',
                connection: g.id,
                component: c.id,
                clearance: Math.round(d),
                required: COMPONENT_CLEARANCE,
                at: { x: Math.round(p.x), y: Math.round(p.y) }
              });
              seenCloseComponents.add(c.id);
            }
          }
        }
      }
      // Endpoint approach check: a long segment parallel to its own source/target
      // edge reads as a line glued to the processor/port arrow.  The only allowed
      // endpoint contact is a short perpendicular entry/exit.
      const endpointComponents = endpointComponentsForPath;
      if (endpointComponents.length) {
        const endpointNormSeg = (a, b) => {
          if (Math.abs(a.x - b.x) < 2 && Math.abs(a.y - b.y) > 8) return ['v', Math.round((a.x + b.x) / 2), Math.min(a.y, b.y), Math.max(a.y, b.y)];
          if (Math.abs(a.y - b.y) < 2 && Math.abs(a.x - b.x) > 8) return ['h', Math.round((a.y + b.y) / 2), Math.min(a.x, b.x), Math.max(a.x, b.x)];
          return null;
        };
        let prev = toScreen(path.getPointAtLength(0));
        for (let i = 1; i <= Math.max(8, Math.min(240, Math.ceil(len / 8))); i++) {
          const cur = toScreen(path.getPointAtLength((len * i) / Math.max(8, Math.min(240, Math.ceil(len / 8)))));
          const n = endpointNormSeg(prev, cur);
          if (n) {
            for (const c of endpointComponents) {
              const b = c.box;
              let hug = 0;
              let distance = Infinity;
              if (n[0] === 'v') {
                const overlapY = rangeOverlap(n[2], n[3], b.y, b.y + b.h);
                distance = Math.min(Math.abs(n[1] - b.x), Math.abs(n[1] - (b.x + b.w)));
                hug = overlapY;
              } else {
                const overlapX = rangeOverlap(n[2], n[3], b.x, b.x + b.w);
                distance = Math.min(Math.abs(n[1] - b.y), Math.abs(n[1] - (b.y + b.h)));
                hug = overlapX;
              }
              if (distance > 0 && distance < COMPONENT_CLEARANCE && hug > 28) {
                issues.push({
                  type: 'path_too_close_to_endpoint_edge',
                  connection: g.id,
                  component: c.id,
                  clearance: Math.round(distance),
                  required: COMPONENT_CLEARANCE,
                  orientation: n[0]
                });
                i = 9999;
                break;
              }
            }
          }
          prev = cur;
        }
      }
    }
    // Detect the “one thick wire” defect: several connection paths using the same
    // horizontal or vertical segment for a meaningful distance. Intersections are
    // sometimes acceptable; long collinear overlap is not informative.
    const normSeg = (a, b) => {
      if (Math.abs(a.x - b.x) < 2 && Math.abs(a.y - b.y) > 8) return ['v', Math.round((a.x + b.x) / 2), Math.min(a.y, b.y), Math.max(a.y, b.y)];
      if (Math.abs(a.y - b.y) < 2 && Math.abs(a.x - b.x) > 8) return ['h', Math.round((a.y + b.y) / 2), Math.min(a.x, b.x), Math.max(a.x, b.x)];
      return null;
    };
    const overlap = (a, b) => {
      if (!a || !b || a[0] !== b[0] || Math.abs(a[1] - b[1]) > 3) return 0;
      return Math.max(0, Math.min(a[3], b[3]) - Math.max(a[2], b[2]));
    };
    const crossPoint = (a, b, margin = 3) => {
      if (!a || !b || a[0] === b[0]) return null;
      const v = a[0] === 'v' ? a : b;
      const h = a[0] === 'h' ? a : b;
      const x = v[1], y = h[1];
      if (h[2] + margin < x && x < h[3] - margin && v[2] + margin < y && y < v[3] - margin) return { x, y };
      return null;
    };
    const distinctSegPair = (a, b) => a.id !== b.id || Math.abs(a.idx - b.idx) > 2;
    const segs = [];
    for (const g of [...document.querySelectorAll('g.connection')]) {
      const path = g.querySelector('path.connection-path');
      if (!path || !path.getTotalLength) continue;
      const toScreen = p => {
        const svg = path.ownerSVGElement;
        const m = path.getScreenCTM();
        if (!svg || !m) return p;
        const pt = svg.createSVGPoint();
        pt.x = p.x; pt.y = p.y;
        const q = pt.matrixTransform(m);
        return { x: q.x, y: q.y };
      };
      const len = path.getTotalLength();
      const steps = Math.max(8, Math.min(240, Math.ceil(len / 8)));
      let prev = toScreen(path.getPointAtLength(0));
      let segIdx = 0;
      for (let i = 1; i <= steps; i++) {
        const cur = toScreen(path.getPointAtLength((len * i) / steps));
        const n = normSeg(prev, cur);
        if (n) segs.push({ id: g.id, idx: segIdx, seg: n });
        segIdx += 1;
        prev = cur;
      }
    }
    for (let i = 0; i < segs.length; i++) {
      for (let j = i + 1; j < segs.length; j++) {
        if (!distinctSegPair(segs[i], segs[j])) continue;
        const ol = overlap(segs[i].seg, segs[j].seg);
        if (ol > 40) {
          issues.push({ type: 'path_overlaps_path', a: segs[i].id, b: segs[j].id, overlap: Math.round(ol), orientation: segs[i].seg[0] });
          break;
        }
        const a = segs[i].seg, b = segs[j].seg;
        const cross = crossPoint(a, b);
        if (cross) {
          issues.push({ type: 'path_crosses_path', a: segs[i].id, b: segs[j].id, at: { x: Math.round(cross.x), y: Math.round(cross.y) } });
          break;
        }
        if (a[0] === b[0] && Math.abs(a[1] - b[1]) > 0 && Math.abs(a[1] - b[1]) < LINE_SPACING) {
          const near = Math.max(0, Math.min(a[3], b[3]) - Math.max(a[2], b[2]));
          if (near > 35) {
            issues.push({ type: 'paths_too_close_parallel', a: segs[i].id, b: segs[j].id, overlap: Math.round(near), distance: Math.round(Math.abs(a[1] - b[1])), required: LINE_SPACING, orientation: a[0] });
            break;
          }
        }
      }
    }
    return { title: document.title, url: location.href, components, connections, labels, issues };
  });

  await page.screenshot({ path: out, fullPage: false });
  data.screenshot = out;
  data.tiles = [];
  if (tileGrid) {
    const m = tileGrid.match(/^(\d+)x(\d+)$/);
    if (!m) throw new Error('--tile-grid must look like 2x2 or 3x2');
    const cols = Math.max(1, Number(m[1]));
    const rows = Math.max(1, Number(m[2]));
    const dir = tileDir || path.dirname(out);
    fs.mkdirSync(dir, { recursive: true });
    const base = path.basename(out).replace(/\.[^.]+$/, '');
    for (let row = 0; row < rows; row++) {
      for (let col = 0; col < cols; col++) {
        // NiFi canvas is panned by dragging empty canvas space.  Reload before
        // every tile so each pan is relative to the same origin; this keeps
        // evidence deterministic enough for review without depending on private
        // frontend APIs.
        if (row || col) {
          await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 60000 });
          await page.waitForTimeout(Number(arg('wait', '8000')));
          if (has('hide-controls')) {
            await page.addStyleTag({ content: `
              graph-controls, .graph-controls, navigation-control, operation-control {
                display: none !important; visibility: hidden !important;
              }
            ` });
            await page.waitForTimeout(300);
          }
        }
        const dx = -col * Math.floor(viewport.width * 0.72);
        const dy = -row * Math.floor(viewport.height * 0.72);
        if (dx || dy) {
          await page.mouse.move(Math.floor(viewport.width / 2), Math.floor(viewport.height / 2));
          await page.mouse.down();
          await page.mouse.move(Math.floor(viewport.width / 2) + dx, Math.floor(viewport.height / 2) + dy, { steps: 12 });
          await page.mouse.up();
          await page.waitForTimeout(400);
        }
        const tilePath = path.join(dir, `${base}-tile-r${row + 1}-c${col + 1}.png`);
        await page.screenshot({ path: tilePath, fullPage: false });
        data.tiles.push({ row, col, screenshot: tilePath });
      }
    }
  }
  if (jsonOut) fs.writeFileSync(jsonOut, JSON.stringify(data, null, 2));
  console.log(JSON.stringify(data, null, 2));
  await browser.close();
})().catch(e => { console.error(e); process.exit(1); });
