#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
: "${BLUDIT_ADMIN_PASSWORD:?BLUDIT_ADMIN_PASSWORD is required}"
: "${BLUDIT_API_TOKEN:?BLUDIT_API_TOKEN is required}"
: "${BLUDIT_AUTH_TOKEN:?BLUDIT_AUTH_TOKEN is required}"
: "${BLUDIT_GATE_TOKEN:?BLUDIT_GATE_TOKEN is required}"
build_dir="$(pwd)/build/bludit"
mkdir -p "$(pwd)/build"
rsync -a --delete vendor/bludit/ "$build_dir/"
mv "$build_dir/index.php" "$build_dir/bludit.php"
mv "$build_dir/install.php" "$build_dir/bludit-install.php"
install -m 0644 public/index.php "$build_dir/index.php"
install -m 0644 public/install.php "$build_dir/install.php"
# The build host CLI lacks gd/dom, but database initialization does not use
# either extension. Relax only the disposable initializer, then restore the
# pristine installer before deployment so production requirements stay intact.
sed -i "s/array('mbstring', 'json', 'gd', 'dom', 'session')/array('mbstring', 'json', 'session')/" \
  "$build_dir/bludit-install.php"
php scripts/init_bludit.php "$build_dir" "$BLUDIT_ADMIN_PASSWORD"
test -f "$build_dir/bl-content/databases/site.php"
install -m 0644 vendor/bludit/install.php "$build_dir/bludit-install.php"
sed -i 's#^RewriteBase /$#RewriteBase /zabbix/#' "$build_dir/.htaccess"
php scripts/configure_bludit.php "$build_dir" "$BLUDIT_API_TOKEN" "$BLUDIT_AUTH_TOKEN" "$BLUDIT_GATE_TOKEN" "$BLUDIT_ADMIN_PASSWORD"
rsync -a --delete bludit/theme/kzabbix/ "$build_dir/bl-themes/kzabbix/"
echo "built: $build_dir"
