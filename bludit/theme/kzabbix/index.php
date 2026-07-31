<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex,nofollow">
<title><?php echo $site->title(); ?></title>
<?php Theme::plugins('siteHead'); ?>
<link rel="stylesheet" href="<?php echo DOMAIN_THEME; ?>style.css">
</head>
<body>
<header><div class="brand"><span>KZ</span><div><strong>Kurage Zabbix</strong><small>PRIVATE INCIDENT INTELLIGENCE</small></div></div><a href="<?php echo DOMAIN_BASE; ?>">障害レポート</a></header>
<main>
<?php if (empty($content)): ?><section class="empty"><h1>障害レポートはありません</h1><p>Zabbixで障害を検知すると、Gemma4の調査結果がここに保存されます。</p></section><?php endif; ?>
<?php foreach ($content as $page): ?>
<article>
  <div class="meta"><?php echo $page->date(); ?> · <?php echo htmlspecialchars($page->category(), ENT_QUOTES, 'UTF-8'); ?></div>
  <h1><a href="<?php echo $page->permalink(); ?>"><?php echo $page->title(); ?></a></h1>
  <div class="report"><?php echo $page->contentBreak(); ?></div>
</article>
<?php endforeach; ?>
</main>
<?php Theme::plugins('siteBodyEnd'); ?>
</body></html>

