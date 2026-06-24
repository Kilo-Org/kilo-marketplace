# NiFi layout rules

## Names

- Use Russian names when the flow is for Russian-speaking operators.
- Prefix major stages with `10`, `20`, `30`, `90`.
- Prefix nested stages by extending the parent number: `30.10`, `30.20`, `30.20.10`.
- Never use `.00`.
- Keep the useful business name after the number.

## Comments

- Add comments to every object type that supports them: process groups, processors, input ports, output ports.
- Write comments in plain human Russian: why the object exists, what it receives/sends, where errors go.
- Avoid generic comments like “processes data”. The comment must help a future maintainer.
- Connections do not support comments. Keep connection names empty so the canvas does not become noisy.

## Layout

- Prefer one main vertical spine.
- Input port or start processor is at the top.
- Output port or finish processor is at the bottom.
- Final output ports are sinks, not intermediate blocks. If an output port has
  incoming connections and no outgoing connections, place it after the last main
  processor/process group, even when its old y-position was above the last group.
  Do not leave a final output port between `Teams` and `Обслуживание`: it creates
  a fake loop instead of a readable finish.
- Side-effect/error/log processors go to the right column.
- Keep the right column close enough to the main spine for short readable
  branches, but leave a real routing corridor between the main processors and
  the side processors. Do not push errors far away just to avoid crossings.
- Use consistent vertical spacing by component type:
  - process group to process group: close enough that the connection label sits neatly between them;
  - processor to process group: a little more breathing room;
  - processor to processor: enough for the queue label without overlap.
  - input port to processor and processor to output port must be visually
    symmetrical when both ports have the same size; do not leave a long bottom
    tail if the top input link is compact.
- Do not leave large dead space unless it separates side branches from the main route.
- Side columns must be dynamic. A single log/error branch should stay close to
  the main line; dense fan-in can reserve a wider corridor for labels and lanes.

## Connections

- Use orthogonal routes: vertical and horizontal segments only.
- Main success path should usually have no bends when components are centered on the same x-axis.
- Error routes should leave to the right, travel on a side bus, then enter the log processor from the side.
- A single same-row branch should usually be a direct straight line. Do not add
  doglegs just to place the queue label if NiFi can place the label cleanly on
  the straight segment.
- Prefer the nearest useful side of the target. Do not force every connection
  into one common point: processors, groups and ports can be entered from top,
  bottom, left or right.
- Source side is also a routing decision. If a branch crosses another block
  only because it leaves from the left/top, try the right/bottom exit before
  adding more bends.
- Avoid giant “telephone wire” loops. A local side route is better than going
  far right/up/down and then coming back.
- A route must not visually touch a component edge except at its own arrowhead.
  If the label/segment lies flush against a processor, group, port, or queue
  label, treat it as an overlap and move the route to another side/lane.
- Several routes into one output port must use separate lanes.
- Several routes into one processor, process group, or port must also use
  separate edge slots on the target side. Do not collapse fan-in into one
  center arrowhead: it looks like one thick wire and hides which branch goes where.
- Choose the target side globally: left, right, top, or bottom depending on the
  source position and blockers. Never hard-code “all error routes enter from the
  left” or “all branches enter from the top”.
- Fan-in/fan-out routes need two independent separations:
  1. separate bus lanes in the open corridor;
  2. separate entry/exit slots on the component edge.
  Solving only one of them still leaves overlapping lines near the target or source.
- Fan-in must be comb-shaped, not bundled. If several labels sit on one vertical
  bus or several paths overlap before entering a log/error processor, route some
  branches through the opposite side or move the error processor closer to the
  source cluster.
- Do not let a handler's outgoing route reuse the same short edge segment as
  incoming failure routes. A right-column handler returning to a lower main-lane
  processor should usually leave from the bottom first, then enter the lower
  target from the side.
- For output ports, prefer a bottom lane when a direct vertical connection is
  blocked by another component. This makes the route read as “branch finished”.
- When a side processor routes to an output port below the main lane, prefer:
  leave the side processor from the bottom/right, go below the nearby blocks,
  then enter the output port from the right/bottom. Do not drag the line back
  through the center corridor if a clean side exit exists.
- If the route would cross a queued label or another component, enter from the side instead of from the top.
- Set `labelIndex` so the connection label appears on a segment with enough free space.
- After routing, repack `labelIndex` values globally inside the process group.
  Local route scoring can miss two labels that are individually valid but overlap
  each other on the canvas.
- Empty every connection name.

## Verification

A flow is not finished until these checks are clean:

- no named connections;
- no missing comments on commentable objects;
- no `.00` numbering;
- no route segment intersects a component rectangle, except its own source/target;
- no connection label intersects a component or another label;
- no long collinear path overlap between different connections;
- screenshot is readable without guessing where a line goes.

## Apache NiFi UI geometry findings

Use these values from the current Apache NiFi frontend, not guessed screenshot sizes:

- Processor: `350 x 130`.
- Process group / remote process group: `384 x 176`.
- Input/output port: `240 x 48`; remote port: `240 x 80`.
- Funnel: `48 x 48`.
- Connection label width: `240`.
- Connection label row height: `19`; backpressure strip adds `3`.
- A connection label always has `Queued`; it also adds `From`/`To` rows for cross-process-group port connections and a `Name` row for selected relationships such as `success`, `failure`, `split`.
- `labelIndex` is centered on `bends[labelIndex]` when bends exist. Without bends the label is centered between calculated source/destination perimeter points.
- Do not use the old `apache/nifi-fds` repository for canvas geometry. It is a reusable Angular/Material design-system package; the live canvas sizes and connection behavior are in `apache/nifi` frontend files: `canvas.constants.ts` and `connection-renderer.ts`.

## Routing corrections learned from real visual review

- First prefer a straight vertical route for the main lane when source and destination share a centerline and there is no real blocker between them.
- Put error/log handlers far enough to the side so the 240px connection label fits between the main processor and side processor.
- For side routes, compute the lane from available corridor width; do not send every connection to the same point.
- Dense fan-in must be ranked before routing. Sort sources by their visible order,
  then assign target-edge slots in the same order. This avoids crossings and
  turns a fan-in into a readable comb instead of a bundle.
- Use actual component rectangles for label overlap checks, but inflated rectangles for path/segment clearance.
- Playwright screenshots remain mandatory after apply; REST geometry alone is not enough because the browser expands connection labels based on relationship rows.
- Use wide screenshots and, when the flow is larger than one viewport, capture
  multiple viewports or scroll/pan through the canvas. A route can look fine in
  a cropped screenshot and still create an ugly long loop outside the view.
- Treat diagonal route segments as defects. In NiFi they usually mean the first
  bend was put on the wrong side of the source/target, so the arrow visually
  goes under the block or the block hides the arrowhead.
- Dense fan-in columns must have enough corridor width for at least one visible grid cell between parallel lanes. If lanes are closer than ~16px over a long segment, treat it as fan-in overlap even if the segments are not exactly collinear.
- A side handler returning to a lower output port should use the shortest clean bottom/right route: drop from the handler, go horizontally at the output level, then enter the output from the side. Do not draw a large rectangle below the whole group unless a real blocker forces it.
- Connection labels are real obstacles. No route segment may pass through another connection's `Name`/`Queued` label box. If this happens, move the label to another bend or route the line around the label.
- For dense fan-in into a right-column processor, lower sources should be tested against both left and right target edges. If the left-edge route crosses the central bus/labels, prefer a right-edge entry, but only after checking the full candidate route against component rectangles.
- A side handler that returns to a lower main-lane processor must not cross the queue labels between main processors. If a direct side return intersects labels, move the horizontal return into a clear gap next to the target and enter from the nearest safe side.
- For side handler → output port routes, do not add a tiny final dogleg just to separate lanes. If the output centerline is clear, route at that y-level and enter the output from the side.
- For dense fan-in into a right-column handler with another handler underneath,
  do not send lower sources around the far right by default: the far-side bus can
  run straight through the lower processor. Split upper sources to the top edge
  and keep same/lower sources in the clear left/middle corridor unless the full
  far-side candidate is proven clear.
- For a right-column handler returning to a lower main-lane processor, do not
  drop from the handler centerline. Exit from the handler's left edge, use an
  open middle corridor, then enter the lower main-lane target from the right so
  the first vertical segment cannot pass through a lower side handler.
- Treat label-on-component and label-on-label collisions as hard failures when
  choosing `labelIndex`; route-line penalties must never outweigh a queued-label
  overlap.
- If two same-column side processors have a clear vertical gap between them,
  prefer the direct no-bend route instead of a scored dogleg that may run along
  or over the lower processor.
- Lines must keep visible clearance, not merely avoid intersection: at the NiFi
  browser zoom used for PUIG evidence, route segments need at least 12px visual
  gap from other connection labels and component edges, and parallel route
  segments need at least 32px visual gap over meaningful lengths.
- When labels are packed but a neighboring line still skims the label border,
  nudge the whole collinear route run, not a single segment. Moving only one
  segment in a same-orientation run creates diagonal artifacts.
- Any visual X/T crossing between different connection lines in open canvas is a defect. Use wider bus lanes or route around the crossing; only the connection's own short source/destination endpoint touch is allowed.
- Non-adjacent segments of the same connection are also separate visual wires: self-overlapping U-turns, close parallel self-runs, or self-crossing loops must be widened or rerouted just like conflicts between different connections.
