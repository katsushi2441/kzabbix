<?php
$isReport = ($WHERE_AM_I === 'page');
$documentTitle = $isReport ? $page->title() . ' | ' . $site->title() : $site->title();
$avatarUrl = 'https://kurage.exbridge.jp/blog/bl-themes/kurage/img/kurage_avatar_face.webp';
?>
<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex,nofollow">
<meta name="description" content="KurageさんがZabbixの障害を検知・調査し、AI障害調査レポートを発行する管理者専用ブログです。">
<title><?php echo htmlspecialchars($documentTitle, ENT_QUOTES, 'UTF-8'); ?></title>
<?php Theme::plugins('siteHead'); ?>
<link rel="stylesheet" href="<?php echo DOMAIN_THEME; ?>style.css">
</head>
<body>
<header class="site-header">
  <div class="header-inner">
    <a class="brand" href="<?php echo DOMAIN_BASE; ?>" aria-label="Kurage Zabbix トップ">
      <span class="brand-mark">KZ</span>
      <span><strong>Kurage Zabbix</strong><small>障害調査・通知レポート</small></span>
    </a>
    <nav aria-label="メインナビゲーション">
      <a href="<?php echo DOMAIN_BASE; ?>">トップ</a>
      <a class="nav-primary" href="<?php echo DOMAIN_BASE; ?>#reports">レポート一覧</a>
    </nav>
  </div>
</header>

<?php if (!$isReport): ?>
<section class="service-map" aria-label="監視フロー">
  <div class="service-map-inner">
    <div class="service-heading"><span>MONITORING FLOW</span> 障害検知からレポート発行まで</div>
    <div class="service-cards">
      <div class="service-card"><b>ZB</b><span><strong>Zabbix</strong><small>24時間監視・障害検知</small></span><i>01</i></div>
      <div class="service-card"><b>LG</b><span><strong>Evidence</strong><small>メトリクス・ログ収集</small></span><i>02</i></div>
      <div class="service-card"><b>AI</b><span><strong>Gemma4</strong><small>原因分析・レポート生成</small></span><i>03</i></div>
      <div class="service-card"><b>NT</b><span><strong>Notify</strong><small>メール・ブログ通知</small></span><i>04</i></div>
    </div>
  </div>
</section>

<main>
  <section class="hero">
    <div class="hero-copy">
      <span class="eyebrow">● PRIVATE INCIDENT INTELLIGENCE</span>
      <h1>Kurageさんが障害を見つけ、<em>調べて、レポートします。</em></h1>
      <p>Zabbixがサーバーやネットワークの異常を検知すると、関連するメトリクスとログを収集。Gemma4が状況を整理し、障害調査レポートとしてメールとこのブログへ発行します。</p>
      <div class="hero-actions">
        <a class="button" href="#reports">障害調査レポートを見る</a>
        <span><b>24 / 7</b> 自動監視中</span>
      </div>
    </div>
    <aside class="kurage-card">
      <img src="<?php echo $avatarUrl; ?>" alt="Kurageさん" width="180" height="180">
      <div><strong>Kurageさんが監視中</strong><p>障害検知から証拠収集、AI解析、通知までを自動で進めます。</p></div>
      <span class="live-indicator">● MONITORING</span>
    </aside>
  </section>

  <section class="content-layout" id="reports">
    <div class="report-column">
      <div class="section-title">
        <div><span>INCIDENT REPORTS</span><h2>障害調査レポート一覧</h2></div>
        <p>新しい順に表示</p>
      </div>

      <?php if (empty($content)): ?>
      <section class="empty-state">
        <span>✓</span><div><h2>現在、公開済みレポートはありません</h2><p>Zabbixが障害を検知すると、調査完了後にここへ追加されます。</p></div>
      </section>
      <?php endif; ?>

      <?php foreach ($content as $report): ?>
      <?php
        $plain = trim(preg_replace('/\s+/u', ' ', strip_tags($report->content())));
        $excerpt = mb_strlen($plain) > 260 ? mb_substr($plain, 0, 260) . '…' : $plain;
        $category = $report->category() ?: '障害調査';
      ?>
      <article class="report-card">
        <div class="report-meta">
          <span class="status-badge">調査レポート</span>
          <time><?php echo htmlspecialchars($report->date(), ENT_QUOTES, 'UTF-8'); ?></time>
          <span><?php echo htmlspecialchars($report->readingTime(), ENT_QUOTES, 'UTF-8'); ?></span>
        </div>
        <h2><a href="<?php echo $report->permalink(); ?>"><?php echo htmlspecialchars($report->title(), ENT_QUOTES, 'UTF-8'); ?></a></h2>
        <p class="excerpt"><?php echo htmlspecialchars($excerpt, ENT_QUOTES, 'UTF-8'); ?></p>
        <div class="report-footer">
          <a class="read-more" href="<?php echo $report->permalink(); ?>">レポートを読む <span>→</span></a>
          <span class="category"># <?php echo htmlspecialchars($category, ENT_QUOTES, 'UTF-8'); ?></span>
        </div>
      </article>
      <?php endforeach; ?>

      <?php if (Paginator::numberOfPages() > 1): ?>
      <nav class="pagination" aria-label="レポート一覧のページ送り">
        <?php if (Paginator::showPrev()): ?><a href="<?php echo htmlspecialchars(Paginator::previousPageUrl(), ENT_QUOTES, 'UTF-8'); ?>">← 新しいレポート</a><?php endif; ?>
        <span><?php echo Paginator::currentPage(); ?> / <?php echo Paginator::numberOfPages(); ?></span>
        <?php if (Paginator::showNext()): ?><a href="<?php echo htmlspecialchars(Paginator::nextPageUrl(), ENT_QUOTES, 'UTF-8'); ?>">過去のレポート →</a><?php endif; ?>
      </nav>
      <?php endif; ?>
    </div>

    <aside class="sidebar">
      <section><span class="side-label">ABOUT</span><h3>このブログについて</h3><p>Kurage Zabbixが自動発行する、管理者専用の障害調査記録です。観測事実・推定原因・確信度・不足情報・推奨対応を残します。</p></section>
      <section><span class="side-label">WORKFLOW</span><h3>調査の流れ</h3><ol><li><b>検知</b><small>ZabbixがWarning以上を検出</small></li><li><b>収集</b><small>イベント前後のログと指標を取得</small></li><li><b>解析</b><small>Gemma4が原因候補と影響を整理</small></li><li><b>通知</b><small>メールとブログへレポート発行</small></li></ol></section>
      <section class="privacy-note"><span>🔒</span><div><strong>PRIVATE REPORT</strong><p>X認証された管理者だけが閲覧できます。</p></div></section>
    </aside>
  </section>
</main>
<?php else: ?>
<main class="report-page">
  <nav class="breadcrumb" aria-label="パンくずリスト"><a href="<?php echo DOMAIN_BASE; ?>">トップ</a><span>›</span><a href="<?php echo DOMAIN_BASE; ?>#reports">レポート一覧</a><span>›</span><span>障害調査レポート</span></nav>
  <div class="detail-layout">
    <article class="report-detail">
      <div class="report-meta"><span class="status-badge">障害調査レポート</span><time><?php echo htmlspecialchars($page->date(), ENT_QUOTES, 'UTF-8'); ?></time><span><?php echo htmlspecialchars($page->readingTime(), ENT_QUOTES, 'UTF-8'); ?></span></div>
      <h1><?php echo htmlspecialchars($page->title(), ENT_QUOTES, 'UTF-8'); ?></h1>
      <div class="detail-divider"><span></span><b>Kurage Zabbix AI Investigation</b></div>
      <div class="report-body"><?php echo $page->content(); ?></div>
      <div class="back-link"><a href="<?php echo DOMAIN_BASE; ?>#reports">← 障害調査レポート一覧へ戻る</a></div>
    </article>
    <aside class="detail-aside"><img src="<?php echo $avatarUrl; ?>" alt="Kurageさん" width="120" height="120"><strong>Kurageさんが調査しました</strong><p>Zabbixの観測データと収集ログをもとに、Gemma4がレポートを構成しています。</p><a href="<?php echo DOMAIN_BASE; ?>#reports">ほかのレポートを見る</a></aside>
  </div>
</main>
<?php endif; ?>

<footer><div><strong>Kurage Zabbix</strong><span>Zabbix × Gemma4 障害調査・通知システム</span></div><p>Private monitoring intelligence · noindex / nofollow</p></footer>
<?php Theme::plugins('siteBodyEnd'); ?>
</body>
</html>
