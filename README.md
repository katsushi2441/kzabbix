# Kurage Zabbix

既存の `192.168.0.2` Zabbix Serverを監視・障害検知・ログ収集の正として利用し、障害イベントをGemma4で調査して、メールと限定Bluditブログへ同一レポートを配信するプロジェクトです。

## Architecture

```text
Zabbix Server 7.0 (192.168.0.2)
  ├─ monitoring / triggers / log[] / logrt[] / SNMP trapper
  └─ Action webhook -> kzabbix API (127.0.0.1:18300)
                         ├─ Zabbix API evidence collection
                         ├─ Gemma4 12B analysis (192.168.0.3)
                         ├─ SMTP -> katsushi2441@gmail.com
                         └─ Bludit -> /zabbix/ (X: xb_bittensor only)
```

Zabbix、Net-SNMP、rsyslogはvendorへ複製しません。既存ZabbixとOSパッケージを利用します。vendorで固定するOSSはBluditだけです。

## Incident evidence collectors

4台のローカルサーバーでは、`kzabbix-evidence.timer`が1分ごとに次の証拠を
`/var/tmp/kzabbix/evidence.json`へ保存します。

- journal/kernel/syslogの警告・エラー
- `iostat`、PSI、`/proc/diskstats`、上位I/Oプロセス
- CPU、メモリ、ファイルシステム、ネットワークカウンター
- Dockerコンテナ負荷、失敗中のsystemd unit、NVMe sysfs状態

Zabbix Agent 2のactive itemがスナップショットとAgent内部ログを7日間保持します。
障害Webhookを受けたワーカーは、イベント前後のスナップショット、Zabbixメトリクス、
実際の復旧イベント時刻をまとめてGemma4へ渡します。

```bash
scripts/deploy_evidence_collectors.sh
set -a; . ./.env; set +a
.venv/bin/python scripts/configure_zabbix.py
```

`xb-rtx3090-1`のNVMeについては、低使用率時の同期書込みを障害扱いしないよう、
待ち時間20ms超過に加えて5分平均使用率70%超過を要求するホスト専用トリガーを使用します。

```bash
set -a; . ./.env; set +a
.venv/bin/python scripts/configure_nvme_trigger.py
```

## Development

```bash
python3 -m venv .venv
.venv/bin/pip install -e '.[dev]'
.venv/bin/pytest
.venv/bin/uvicorn kzabbix.api:app --host 127.0.0.1 --port 18300
```

`.env.sample`を`.env`へコピーし、秘密値はローカルだけに設定します。

## Zabbix webhook

`zabbix/webhook.js`をZabbixのWebhook Media typeへ登録し、次のパラメータを渡します。

- `url`: `http://127.0.0.1:18300/webhook/zabbix`
- `token`: `KZABBIX_API_TOKEN`
- `event_id`: `{EVENT.ID}`
- `event_name`: `{EVENT.NAME}`
- `event_status`: `{EVENT.STATUS}`
- `event_severity`: `{EVENT.SEVERITY}`
- `host_id`: `{HOST.ID}`
- `host_name`: `{HOST.HOST}`
- `trigger_id`: `{TRIGGER.ID}`
- `trigger_expression`: `{TRIGGER.EXPRESSION}`
- `event_date`: `{EVENT.DATE}`
- `event_time`: `{EVENT.TIME}`

## Bludit

`vendor/bludit`は `katsushi2441/bludit` forkのBludit 3.22.0を固定しています。

```bash
scripts/build_bludit.sh
scripts/deploy_bludit.sh
```

Bluditの全ページは共有Xログインで保護され、`xb_bittensor`だけが閲覧できます。API投稿は別のgate token、Bludit API token、admin authentication tokenの3要素で保護します。
