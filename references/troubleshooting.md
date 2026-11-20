# Troubleshooting

| Symptom | Meaning | Action |
| --- | --- | --- |
| `No ChongPlus API key is saved` | No local credential is configured. | Ask for the key and save it with `config --set-key` or safe stdin. |
| Authentication failure | The key is missing, invalid, or lacks access. | Replace the saved key or check its access and quota. |
| Authorization failure | The request is not allowed. | Check account access and quota. |
| Rate limit | ChongPlus temporarily limited requests. | Wait, then ask the user before making another request. |
| Temporary service failure | ChongPlus or the network route is unavailable. | Report the failure; retry only when the user explicitly requests it. |

`config --check` performs a no-cost local configuration check. It does not prove API access; real image generation may consume quota.
