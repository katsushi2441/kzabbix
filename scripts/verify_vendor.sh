#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
expected="$(python3 -c 'import json; print(json.load(open("vendor.lock.json"))["bludit"]["commit"])')"
actual="$(git -C vendor/bludit rev-parse HEAD)"
test "$actual" = "$expected"
test -f vendor/bludit/LICENSE
echo "vendor/bludit verified: $actual"

