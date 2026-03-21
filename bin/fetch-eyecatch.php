#!/usr/bin/env php
<?php
/**
 * Unsplash API を使って各記事のアイキャッチ画像 URL を取得し frontmatter に保存する
 * 使い方: php bin/fetch-eyecatch.php [--force]
 *   --force : eyecatch が設定済みの記事も上書きする
 */

$force = in_array('--force', $argv ?? []);

// .env からキーを読み込む
$envFile = __DIR__ . '/../.env';
if (!file_exists($envFile)) {
    fwrite(STDERR, ".env ファイルが見つかりません。.env.example を参考に作成してください。\n");
    exit(1);
}
foreach (file($envFile, FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES) as $line) {
    if (str_starts_with(trim($line), '#')) continue;
    [$key, $val] = array_map('trim', explode('=', $line, 2));
    $_ENV[$key] = $val;
}

$accessKey = $_ENV['UNSPLASH_ACCESS_KEY'] ?? '';
if (!$accessKey || $accessKey === 'your_access_key_here') {
    fwrite(STDERR, "UNSPLASH_ACCESS_KEY が設定されていません。\n");
    exit(1);
}

// タグ → 検索キーワードのマッピング
$keywordMap = [
    'macbook'      => 'macbook laptop',
    'iphone'       => 'iphone smartphone',
    'ipad'         => 'ipad tablet',
    'vision'       => 'augmented reality',
    'xr'           => 'virtual reality headset',
    'apple'        => 'apple technology',
    'headphone'    => 'headphones audio',
    'audio'        => 'headphones music',
    'sony'         => 'sony headphones',
    'monitor'      => 'monitor desk setup',
    'oled'         => 'display screen',
    'lg'           => 'ultrawide monitor',
    'gaming'       => 'gaming setup',
    'steam'        => 'gaming controller',
    'nas'          => 'network storage server',
    'synology'     => 'nas server',
    'storage'      => 'hard drive storage',
    'keyboard'     => 'mechanical keyboard',
    'keychron'     => 'keyboard typing',
    'camera'       => 'camera photography',
    'photography'  => 'camera photo',
    'ricoh'        => 'street photography',
    'fullframe'    => 'mirrorless camera',
    'dji'          => 'drone aerial',
    'video'        => 'camera video',
    'elgato'       => 'streaming setup',
    'watch'        => 'smartwatch',
    'outdoor'      => 'outdoor adventure',
    'mouse'        => 'mouse desk',
    'logicool'     => 'mouse keyboard',
    'ssd'          => 'ssd storage',
    'samsung'      => 'technology device',
    'charger'      => 'charger cable usb',
    'anker'        => 'charger power',
    'raspberrypi'  => 'raspberry pi electronics',
    'linux'        => 'linux terminal',
    'fujifilm'     => 'film camera',
    'm3'           => 'macbook apple chip',
    'm4'           => 'apple silicon',
    'vscode'       => 'code editor',
    'editor'       => 'code programming',
    'cursor'       => 'ai code editor',
    'docker'       => 'container devops',
    'container'    => 'docker server',
    'tailwind'     => 'css web design',
    'css'          => 'web design',
    'frontend'     => 'web development',
    'bun'          => 'javascript runtime',
    'nodejs'       => 'nodejs javascript',
    'astro'        => 'web framework',
    'neovim'       => 'terminal code',
    'vim'          => 'terminal editor',
    'copilot'      => 'ai github code',
    'github'       => 'github code',
    'figma'        => 'design ui figma',
    'browser'      => 'browser web',
    'arc'          => 'browser minimal',
    'terminal'     => 'terminal command line',
    'warp'         => 'terminal cli',
    'database'     => 'database server',
    'obsidian'     => 'notes writing',
    'raycast'      => 'mac productivity',
    'productivity' => 'productivity workspace',
    'linear'       => 'project management',
    'vercel'       => 'deploy cloud',
    'zed'          => 'code editor',
    'rust'         => 'programming',
    'deno'         => 'javascript',
    'javascript'   => 'javascript code',
    'typescript'   => 'typescript programming',
    'php'          => 'php code',
    'ai'           => 'artificial intelligence',
    'cloudflare'   => 'network cloud',
    'hosting'      => 'server hosting',
    'serverless'   => 'serverless cloud',
    'actions'      => 'github automation',
    'vpn'          => 'vpn security network',
    'tailscale'    => 'vpn network',
    'aws'          => 'aws cloud server',
    'lambda'       => 'serverless function',
    'nextjs'       => 'nextjs react',
    'react'        => 'react code',
    'htmx'         => 'html web',
    'cdn'          => 'network cdn',
    'netlify'      => 'deploy cloud',
    'render'       => 'cloud server',
    'caddy'        => 'server https',
    'server'       => 'server datacenter',
    'minio'        => 'storage cloud',
    's3'           => 'cloud storage',
    'wireguard'    => 'vpn security',
    'security'     => 'security lock',
    'nginx'        => 'server nginx',
    'proxy'        => 'network proxy',
];

$base    = __DIR__ . '/../contents';
$total   = 0;
$skipped = 0;
$errors  = 0;

foreach (glob($base . '/*/*.md') as $file) {
    $raw = file_get_contents($file);

    if (!preg_match('/^---\s*\n(.*?)\n---\s*\n/s', $raw, $m)) continue;

    $frontmatter = $m[1];
    $body        = substr($raw, strlen($m[0]));

    // --force なし かつ既存の Unsplash URL なら skip
    if (!$force && preg_match('/^eyecatch:.*images\.unsplash\.com/m', $frontmatter)) {
        $skipped++;
        continue;
    }

    // タグからキーワード決定
    $keyword = null;
    if (preg_match('/^tags:\s*\[([^\]]+)\]/m', $frontmatter, $tm)) {
        foreach (array_map('trim', explode(',', $tm[1])) as $tag) {
            $tag = trim($tag, '"\'');
            if (isset($keywordMap[$tag])) {
                $keyword = $keywordMap[$tag];
                break;
            }
        }
    }
    $keyword ??= 'technology';

    // Unsplash API を呼ぶ
    $url = 'https://api.unsplash.com/photos/random'
         . '?query=' . urlencode($keyword)
         . '&orientation=landscape'
         . '&client_id=' . $accessKey;

    $ctx  = stream_context_create(['http' => ['header' => 'Accept: application/json']]);
    $json = @file_get_contents($url, false, $ctx);

    if ($json === false) {
        fwrite(STDERR, "ERROR: " . basename($file) . " ($keyword)\n");
        $errors++;
        continue;
    }

    $data      = json_decode($json, true);
    $imgUrl    = $data['urls']['regular'] ?? null;

    if (!$imgUrl) {
        fwrite(STDERR, "NO IMAGE: " . basename($file) . " ($keyword)\n");
        $errors++;
        continue;
    }

    // Picsum URL があれば置換、なければ追加
    if (preg_match('/^eyecatch:/m', $frontmatter)) {
        $frontmatter = preg_replace('/^eyecatch:.*$/m', 'eyecatch: "' . $imgUrl . '"', $frontmatter);
    } else {
        $frontmatter = preg_replace('/^(tags:.+)$/m', '$1' . "\neyecatch: \"$imgUrl\"", $frontmatter);
    }

    file_put_contents($file, "---\n" . $frontmatter . "\n---\n" . $body);
    echo basename($file) . "\n  keyword : $keyword\n  url     : $imgUrl\n";
    $total++;

    // レート制限対策（50req/h = 1.2秒間隔）
    usleep(1500000);
}

echo "\n完了: {$total}件更新, {$skipped}件スキップ, {$errors}件エラー\n";
