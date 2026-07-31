# kzabbix Agent Rules

- Follow `/home/kojima/work/AGENTS.md`, `WORKFLOW.md`, and `QUALITY_RULES.md`.
- The existing Zabbix Server on `192.168.0.2` is the source of truth. Never install or replace Zabbix Server or existing agents from this project.
- Use only `gemma4:12b-it-qat` and always send `think: false` unless the user explicitly changes the model.
- Never commit Zabbix, SMTP, Bludit, webhook, X OAuth, or FTP secrets.
- Incident reports must distinguish observed evidence, inference, confidence, and missing evidence.
- The Bludit site is private and must require the shared X login with the exact allowlisted user `xb_bittensor`.
- Public deployment lives at `https://kurage.exbridge.jp/zabbix/`.

