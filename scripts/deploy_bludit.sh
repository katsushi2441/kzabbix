#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
set -a
. /home/kojima/work/aixec/.env
set +a
test -f build/bludit/bl-content/databases/site.php
remote="/web/kurage_exbridge_jp/zabbix"
export remote
# The shared FTP server rejects concurrent MKD operations. Seed one real file
# per directory sequentially, then transfer the complete tree with two workers.
while IFS= read -r dir; do
  first="$(find "$dir" -maxdepth 1 -type f -print -quit)"
  if [[ -n "$first" ]]; then
    rel="${first#build/bludit/}"
    curl --fail --silent --show-error --ftp-create-dirs -T "$first" \
      "ftp://${FTP_USER}:${FTP_PASS}@${FTP_HOST}${remote}/${rel}"
  fi
done < <(find build/bludit -type d | sort)

find build/bludit -type f -print0 | xargs -0 -P 2 -I '{}' bash -c '
  file="$1"
  rel="${file#build/bludit/}"
  curl --fail --silent --show-error -T "$file" \
    "ftp://${FTP_USER}:${FTP_PASS}@${FTP_HOST}${remote}/${rel}"
' _ '{}'
echo "deployed: https://kurage.exbridge.jp/zabbix/"
