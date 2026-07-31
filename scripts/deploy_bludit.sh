#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
set -a
. /home/kojima/work/aixec/.env
set +a
test -f build/bludit/bl-content/databases/site.php
remote="/web/kurage_exbridge_jp/zabbix"
find build/bludit -type f -print0 | while IFS= read -r -d '' file; do
  rel="${file#build/bludit/}"
  curl --fail --silent --show-error --ftp-create-dirs -T "$file" \
    "ftp://${FTP_USER}:${FTP_PASS}@${FTP_HOST}${remote}/${rel}"
done
echo "deployed: https://kurage.exbridge.jp/zabbix/"

