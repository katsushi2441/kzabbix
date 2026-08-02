#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

key="/home/kojima/.ssh/id_swarmclaw_openclaw"
remote_hosts=(192.168.0.2 192.168.0.11 192.168.0.14)

install_local() {
  install -d -m 0755 /home/kojima/.local/lib/kzabbix /home/kojima/.config/systemd/user
  install -m 0755 agent/kzabbix_evidence.py /home/kojima/.local/lib/kzabbix/kzabbix_evidence.py
  install -m 0644 systemd/kzabbix-evidence.service /home/kojima/.config/systemd/user/
  install -m 0644 systemd/kzabbix-evidence.timer /home/kojima/.config/systemd/user/
  systemctl --user daemon-reload
  systemctl --user enable --now kzabbix-evidence.timer
  systemctl --user start kzabbix-evidence.service
  systemctl --user is-active kzabbix-evidence.timer
  test -s /var/tmp/kzabbix/evidence.json
}

install_remote() {
  local host="$1"
  local ssh_opts=(-i "$key" -p 2222 -o BatchMode=yes -o ConnectTimeout=8)
  local scp_opts=(-i "$key" -P 2222 -o BatchMode=yes -o ConnectTimeout=8)
  ssh "${ssh_opts[@]}" "kojima@${host}" \
    "install -d -m 0755 /home/kojima/.local/lib/kzabbix /home/kojima/.config/systemd/user"
  scp "${scp_opts[@]}" agent/kzabbix_evidence.py "kojima@${host}:/home/kojima/.local/lib/kzabbix/"
  scp "${scp_opts[@]}" systemd/kzabbix-evidence.service systemd/kzabbix-evidence.timer \
    "kojima@${host}:/home/kojima/.config/systemd/user/"
  ssh "${ssh_opts[@]}" "kojima@${host}" \
    "chmod 0755 /home/kojima/.local/lib/kzabbix/kzabbix_evidence.py; \
     chmod 0644 /home/kojima/.config/systemd/user/kzabbix-evidence.service \
       /home/kojima/.config/systemd/user/kzabbix-evidence.timer; \
     systemctl --user daemon-reload; \
     systemctl --user enable --now kzabbix-evidence.timer; \
     systemctl --user start kzabbix-evidence.service; \
     systemctl --user is-active kzabbix-evidence.timer; \
     test -s /var/tmp/kzabbix/evidence.json"
}

printf '[local %s]\n' "$(hostname)"
install_local
for host in "${remote_hosts[@]}"; do
  printf '[remote %s]\n' "$host"
  install_remote "$host"
done
