# ChongPlus Nano Banana API

- Model: `gemini-2.5-flash-image` (Google Nano Banana through ChongPlus).
- Base URL: `https://ai.chongplus.plus`.
- Generation: `POST /v1/images/generations` with JSON fields `model`, `prompt`, `size`, optional `n` (1-4), and `response_format: b64_json`.
- Editing: `POST /v1/images/edits` with multipart fields `image`, `model`, `prompt`, optional `size`, and `n` (1-4).
- Authentication: `Authorization: Bearer sk-...`.
- Sizes: `1024x1024`, `2048x2048`, `1536x1024`, `1024x1536`, `3840x2160`, or `2160x3840`.
- Results: `data` entries contain a `b64_json` payload or image `url`.
- Model discovery: `GET /v1/models`; the client caches successful results for 24 hours in the local user configuration directory. Generation proceeds with a warning if discovery is unavailable, but stops if discovery succeeds and the configured model is absent.
