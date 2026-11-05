# Design and assets

Use visual direction to explain this particular offer. Start with existing brand
constraints and the content, then choose hierarchy, typography, spacing, imagery,
and interaction. Taste is contextual; there is no universal prohibited font,
color, hero pattern, animation, or section count.

## Make a specific design decision

Write a short direction: intended feeling, dominant visual device, information
density, type roles, color roles, and what should attract attention first. For
example, a practical local service can use warm material colors and clear service
boundaries; a complex B2B product can use restrained typography and an explanatory
interface. Do not translate every brief into the same gradient and card grid.

Define a small token set for color, type, space, radius, and width. Keep it native
to the existing stack. Add a token interchange format only if a real consumer
needs it. Use content length to choose breakpoints, with flexible grids and
readable line lengths. Repeated components should behave consistently.

## Choose assets by purpose

| Purpose | Useful asset | Avoid |
| --- | --- | --- |
| Explain a product | Approved screenshot, original annotated diagram, interactive sample | Invented customer data presented as live usage |
| Show a service | Permissioned work photos, process illustration, real team image | Stock imagery represented as the actual team or project |
| Establish proof | Source-linked result or approved quote | Decorative logos that imply affiliation |
| Set atmosphere | Original illustration, restrained texture, typography | Large media with no explanatory or emotional role |

Inspect supplied assets first. Record creator/source, license/permission, local
path, purpose, modifications, and alt treatment. For generated images, retain the
prompt/tool/date and inspect for misleading text or artifacts. Generated images
do not establish product evidence or rights to a depicted brand.

When image tools are unavailable, choose intentional typography, CSS, or original
SVG instead of broken placeholders. Use decorative alt text only for genuinely
decorative content; informative images need contextual alternatives. Do not
recreate a customer's logo inaccurately as text art.

## Build and inspect

- Reserve image dimensions; use responsive sources and appropriate formats.
- Prioritize the likely largest above-the-fold image; defer below-fold media.
- Avoid auto-playing heavy video. Provide a useful poster and controls when used.
- Keep focus indicators visible and contrast sufficient in every state.
- Respect reduced motion; motion should clarify, not delay the primary action.
- Verify mobile composition, zoom, long labels, keyboard order, and error states.
- Inspect rendered pages at desktop and mobile widths before declaring visual QA.

Use the bundled original SVG patterns only when they fit the direction. They are
starting assets, not a mandatory aesthetic or a substitute for product proof.
