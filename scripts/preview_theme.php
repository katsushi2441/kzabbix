<?php
// kzabbixテーマのローカルプレビュー。Bludit APIをスタブしてindex.phpを描画する。
// 使い方: php scripts/preview_theme.php home > /tmp/preview_home.html
//         php scripts/preview_theme.php page > /tmp/preview_page.html
error_reporting(E_ALL & ~E_DEPRECATED & ~E_NOTICE & ~E_WARNING);

$mode = $argv[1] ?? 'home';
define('WHERE_AM_I', $mode === 'page' ? 'page' : 'home');
define('DOMAIN_THEME', './');
define('DOMAIN_BASE', './');

class Theme { public static function plugins($x) {} }
class Site { public function title() { return 'Kurage Zabbix'; } }
class StubPage {
    public function __construct(private string $t, private string $raw, private string $d) {}
    public function title() { return $this->t; }
    public function contentRaw($x = false) { return $this->raw; }
    public function content() { return nl2br(htmlspecialchars($this->raw)); }
    public function date() { return $this->d; }
    public function permalink() { return '#'; }
    public function category() { return 'incidents'; }
    public function contentBreak() { return $this->content(); }
}

$sample = <<<'MD'
## 概要
2026-08-01 03:12、**web-01** の nginx がヘルスチェックに応答しなくなり、Zabbixトリガー `HTTP service is down` が発火しました。3分後にプロセス再起動で自動復旧しています。

## 影響範囲
- kurage.exbridge.jp 配下の全Webサービス(約3分間の502)
- バックグラウンドジョブへの影響なし

## 時系列
- 03:12:04 Zabbixが `HTTP service is down` を検知 (severity: High)
- 03:12:30 kzabbixが証拠収集を開始
- 03:13:11 nginx error.log に `worker_connections are not enough` を確認
- 03:15:02 systemdがnginxを自動再起動、トリガー復旧

## 観測事実
| 項目 | 値 |
| 対象ホスト | web-01 (192.168.0.7) |
| トリガー | HTTP service is down |
| 継続時間 | 2分58秒 |

## ログ解析
```
2026/08/01 03:11:58 [alert] 1123#1123: worker_connections are not enough
2026/08/01 03:12:02 [error] 1123#1123: *4411 connect() failed (111: Connection refused)
```
接続数が `worker_connections` 上限(768)へ到達し、新規接続を受け付けられない状態でした。

## 原因候補と確度
- **worker_connections枯渇**(確度: 高) — alertログと接続数グラフが一致
- 上流からのバーストアクセス(確度: 中) — 03:10台にリクエスト数が平常の6倍

## 推奨対応
- nginx.conf の `worker_connections` を 768 → 2048 へ引き上げる
- keepalive_timeout を 65 → 30 に短縮し接続滞留を減らす
- 同型アラートの再発時はレート制限の導入を検討する

## 追加で必要な証拠
- 03:00-03:20 のアクセスログ上位クライアント集計
MD;

$site = new Site();
$content = [
    new StubPage('[web-01] HTTP service is down (kz-20260801-0312a)', $sample, '2026-08-01 03:15'),
    new StubPage('[db-01] Free disk space is less than 20% (kz-20260731-2244b)', "## 概要\n/var/lib のディスク使用率が81%に達しました。**復旧済み**、ログローテートで空きを確保しています。", '2026-07-31 22:44'),
    new StubPage('[gw-01] Zabbix agent is not available (kz-20260730-1801c)', "## 概要\nagent疎通が5分間失われました。ネットワーク瞬断が原因候補です。", '2026-07-30 18:01'),
];
if (WHERE_AM_I === 'page') { $content = [$content[0]]; }

require __DIR__ . '/../build/bludit/bl-themes/kzabbix/init.php';
require __DIR__ . '/../build/bludit/bl-themes/kzabbix/index.php';
