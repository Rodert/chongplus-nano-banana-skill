# ChongPlus Nano Banana Skill

An Agent Skill for image generation and reference-image editing with Google's Nano Banana model through the ChongPlus Image API.

## What it does

- Generates images from text through the ChongPlus Image API
- Edits a supplied reference image with text instructions
- Stores the ChongPlus API Key in the current user's local configuration directory
- Uses Python's standard library only
- Writes per-request status files and never automatically retries a quota-consuming request
- Verifies the configured model against a locally cached model list (24-hour refresh interval)

## Requirements

- An Agent Skills-compatible client, such as Codex
- Python 3.9 or newer
- A ChongPlus API Key with image-generation access

## Install and use in Codex

Copy the following into Codex:

```text
Install and use the ChongPlus Nano Banana Skill from this repository.

On first use, proactively ask me for my ChongPlus API Key. Save it securely in the local user configuration, then read and reuse it automatically for later Nano Banana image requests. Do not ask me to configure an environment variable.
```

Create a key at https://api.chongplus.plus/keys. After installation, ask Codex to generate or edit an image.

## Local use

```bash
python3 scripts/nano_banana.py config --set-key
python3 scripts/nano_banana.py models
python3 scripts/nano_banana.py generate \
  --prompt "A cinematic mountain landscape at sunrise" \
  --size 1536x1024 --output-dir ./outputs
```

For non-interactive automation, pass the key only through standard input:

```bash
printf '%s' "$KEY" | python3 scripts/nano_banana.py config --set-key-stdin
```

Do not place API keys in command arguments, repository files, or committed configuration.

## Credential storage

| Platform | Path |
| --- | --- |
| macOS/Linux | `$XDG_CONFIG_HOME/chongplus-nano-banana/config.json`, or `~/.config/chongplus-nano-banana/config.json` |
| Windows | `%APPDATA%\\chongplus-nano-banana\\config.json` |

On Unix systems the client applies directory mode `0700` and file mode `0600`.

## Development

```bash
python3 -m unittest discover -s tests
```

The tests do not call the ChongPlus API and do not need a real key.
