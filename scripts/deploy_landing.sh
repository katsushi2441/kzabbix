#!/usr/bin/env bash
# kzabbix.exbridge.jp へLP(英index.html/日kzabbix.html)をデプロイする(kfinanalystと同型)。
set -euo pipefail
cd "$(dirname "$0")/.."
set -a; . /home/kojima/work/aixec/.env; set +a
remote="/web/kzabbix_exbridge_jp"
files=(
  "landing/index.html:index.html"
  "landing/kzabbix.html:kzabbix.html"
  "landing/assets/style.css:assets/style.css"
  "landing/assets/kzabbix-ogp.png:assets/kzabbix-ogp.png"
  "landing/assets/kurage_avatar_face.webp:assets/kurage_avatar_face.webp"
  "landing/robots.txt:robots.txt"
  "landing/sitemap.xml:sitemap.xml"
)
for item in "${files[@]}"; do
  curl --fail --silent --show-error --ftp-create-dirs -T "${item%%:*}" \
    "ftp://${FTP_USER}:${FTP_PASS}@${FTP_HOST}${remote}/${item#*:}"
  echo "deployed: ${item#*:}"
done
echo "https://kzabbix.exbridge.jp/"
