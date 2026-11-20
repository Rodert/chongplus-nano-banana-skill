---
name: chongplus-nano-banana
description: Generate or edit images with Google's Nano Banana model through the ChongPlus Image API. Use for ChongPlus Nano Banana text-to-image, reference-image editing, or image revisions. On first use, ask for the user's ChongPlus API Key and save it with the bundled local client; never require an environment variable.
---

# ChongPlus Nano Banana

Run the bundled client from this Skill's directory. Resolve `SKILL_DIR` as the directory containing this `SKILL.md`; do not use an absolute path from another machine.

This Skill calls the ChongPlus Image API with `gemini-2.5-flash-image`, its Google Nano Banana model. Each `generate` or `edit` invocation may consume image-generation quota. Do not submit a duplicate while an earlier request is still running, and never retry a failed request unless the user explicitly requests another attempt.

Before a generation or edit, validate the configured model against the ChongPlus `/v1/models` list. Cache the list locally for 24 hours; a refresh has a 2-second timeout. If the list is reachable and does not include the configured model, stop and report available models without silently switching. If the list cannot be fetched, warn and continue the image request with the configured model. Use `models` to force-refresh and print the current list.

## Credential workflow

1. Let the client load the saved key during an image request. Do not run `config --show-status` before every request.
2. On first use, or when the client reports that no key is saved, ask: `Please provide your ChongPlus API Key (sk-...). I will save it locally for future Nano Banana image requests. If you do not have one, sign in at https://api.chongplus.plus/keys and create a key with image-generation access.`
3. Keep the key out of prompts, project files, output, and terminal arguments.
4. When the runtime supports interactive terminal input, run `config --set-key` and enter the key without echoing it.
5. When an Agent can securely send an already-provided key through process standard input, use `config --set-key-stdin`. Do not put it in a command-line argument or environment variable.

The client saves credentials to `~/.config/chongplus-nano-banana/config.json` on macOS/Linux (or `$XDG_CONFIG_HOME/chongplus-nano-banana/config.json`) and `%APPDATA%\\chongplus-nano-banana\\config.json` on Windows. It applies owner-only permissions where the platform supports them.

## Generate

Use a documented size: `1024x1024`, `2048x2048`, `1536x1024`, `1024x1536`, `3840x2160`, or `2160x3840`.

```bash
python3 "$SKILL_DIR/scripts/nano_banana.py" generate \
  --prompt 'A cinematic product photograph of a compact espresso machine, soft studio light, light gray background' \
  --size 1536x1024 --output-dir ./outputs
```

The client writes result files to the output directory and prints their absolute paths.

## Edit

```bash
python3 "$SKILL_DIR/scripts/nano_banana.py" edit \
  --image /absolute/path/to/source.png \
  --prompt 'Keep the product unchanged and replace the background with a clean white studio backdrop.' \
  --size 1024x1024 --output-dir ./outputs
```

## Live request status

Each invocation writes one atomically updated JSON status file. By default it is named `nano-banana-<request-id>.status.json` in the output directory; use `--status-file /absolute/path/status.json` to choose its location. It records only the request ID, action, timestamps, state, safe error summary, and completed output paths; it never records the API key, prompt, input image, or raw provider response.

Use the status file rather than delayed terminal output to decide request state. Valid states include `started`, `checking_model`, `reading_reference`, `submitting_request`, `response_received`, `writing_results`, `succeeded`, and `failed`.

## Error handling

Report only the bundled client's summarized error to the user. Do not expose the API key, raw response body, request URL, or provider diagnostics. Do not automatically retry authentication, authorization, invalid-request, rate-limit, network, or service failures. See [references/troubleshooting.md](references/troubleshooting.md) for public error categories.
