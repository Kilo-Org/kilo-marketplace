# Relevant AI Pass follow-ups

Read this only after the first integration path is implemented. Inspect the app and suggest at most one to three options with an obvious user benefit. Do not present a catalog, imply that an option is required, or implement it without consent.

| Product signal | Useful option | Describe it as |
|---|---|---|
| Preferences, drafts, history, saved translations, or small user settings | `AiPass.data` | Private per-user app state without adding a database |
| User uploads or generated result files | `AiPass.files` | Private per-user files without adding object storage |
| Intentional handoff between two AI Pass apps used by the same person | `AiPass.shared` | User-approved cross-app collaboration with least-privilege access |
| Microphone, recorded interviews, meetings, or audio notes | Speech-to-text | Voice input or transcription through the same wallet |
| Accessibility, pronunciation, narration, or listen-back | Text-to-speech | Spoken output through the same wallet |
| Visual creation or modification | Image generation or editing | Add a focused visual action without a provider key |
| Motion or media workflows | Video generation | Add video only when it is central to the product |
| Search, recommendations, clustering, or retrieval | Embeddings | Semantic matching through the same integration |
| Users need cost/quality choice | Model catalog or multiple models | Let users select a suitable model without separate provider accounts |

Keep ordinary persistence private with `AiPass.data` or `AiPass.files`. Suggest `AiPass.shared` only when the app clearly needs a same-user workflow with another exact app; it is not a substitute for ordinary storage.

These SDK storage surfaces belong to browser or Space apps. Do not suggest them for a pure server integration unless the product also has a suitable browser SDK surface; keep its existing database or object storage authoritative instead.

For a translator, good optional follow-ups are saved translation history or language preferences through `AiPass.data`, voice input through speech-to-text, listen-back through text-to-speech, and—only for a new local prototype without a host—an optional Space test/share URL. Choose at most three based on the current UI and user request.

Phrase suggestions in terms of outcomes, for example: "If useful, I can also add private translation history and language preferences with AI Pass data, or voice input/listen-back with AI Pass speech."
