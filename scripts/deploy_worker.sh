#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
test -f .runtime.env
remote_host="192.168.0.2"
remote_key="/home/kojima/.ssh/id_swarmclaw_openclaw"
remote_dir="/home/kojima/work/kzabbix"
ssh_opts=(-i "$remote_key" -p 2222 -o BatchMode=yes)
scp_opts=(-i "$remote_key" -P 2222 -o BatchMode=yes)

ssh "${ssh_opts[@]}" "kojima@${remote_host}" "mkdir -p /home/kojima/work"
if ssh "${ssh_opts[@]}" "kojima@${remote_host}" "test -d '${remote_dir}/.git'"; then
  ssh "${ssh_opts[@]}" "kojima@${remote_host}" \
    "cd '${remote_dir}' && git status --short --branch && git pull --rebase origin main && git status --short --branch"
else
  ssh "${ssh_opts[@]}" "kojima@${remote_host}" \
    "git clone https://github.com/katsushi2441/kzabbix.git '${remote_dir}'"
fi
scp "${scp_opts[@]}" .runtime.env "kojima@${remote_host}:${remote_dir}/.env"
ssh "${ssh_opts[@]}" "kojima@${remote_host}" "chmod 600 '${remote_dir}/.env'; \
  cd '${remote_dir}'; python3 -m venv .venv; .venv/bin/pip install -q -e .; \
  mkdir -p data /home/kojima/.config/systemd/user; \
  install -m 0644 systemd/kzabbix-api.service /home/kojima/.config/systemd/user/kzabbix-api.service; \
  systemctl --user daemon-reload; systemctl --user enable --now kzabbix-api; \
  systemctl --user is-enabled kzabbix-api; systemctl --user is-active kzabbix-api"
