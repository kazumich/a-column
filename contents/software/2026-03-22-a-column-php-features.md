---
title: "a-column PHP の機能紹介"
date: "2026-03-22 12:00:00"
author: "kazumich"
category: software
tags: [php, cms, markdown, twig, tailwindcss, alpinejs]
eyecatch: "https://images.unsplash.com/photo-1641350625112-3b1d73c71418?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w5MDE2NjV8MHwxfHJhbmRvbXx8fHx8fHx8fDE3NzQxNDcxMDB8&ixlib=rb-4.1.0&q=80&w=1080"
description: "データベース不使用・ファイルベースで動く軽量 PHP CMS「a-column」の機能を紹介します。Markdown で記事を書き、タグ検索や GitHub 連携まで備えた次世代の CMS です。"
---

2000年代初頭に Perl で作った個人 CMS「a-column」を、20数年ぶりに PHP でリニューアルしました。データベースを使わず、Markdown ファイルだけでコンテンツを管理するシンプルな設計が特徴です。

## ファイルベースのコンテンツ管理

記事は Markdown ファイルで管理します。データベースのセットアップが不要で、ファイルをコピーするだけで環境を移行できます。

```
contents/
  hardware/
    2024-10-11-new-mac-mini.md
  software/
    2026-03-22-a-column-php-features.md
  net/
    2024-10-01-cloudflare-pages.md
```

各ファイルは YAML フロントマターと Markdown 本文で構成されています。

```yaml
---
title: "記事タイトル"
date: "2026-03-22 12:00:00"
author: "kazumich"
tags: [php, cms]
eyecatch: "https://..."
description: "SEO 用の概要文"
---

本文を **Markdown** で書く。
```

## タグ検索と JSON インデックス

タグ検索は DB を使わずに JSON インデックスで実現しています。タグごとにファイルを分けて管理し、AND 検索にも対応しています。

```
/tag/php+cms  →  php と cms 両方のタグを持つ記事を表示
```

インデックスはコンテンツファイルの更新を検知して自動再ビルドされます。将来 1 万件規模になっても対応できる設計です。

## Twig テンプレートエンジン

テンプレートは Twig を採用しています。a-blog cms のモジュール概念に近い形で、再利用可能なモジュールを `includes` で組み合わせる設計です。

```twig
{% include "modules/entry_summary.html.twig" %}
{% include "modules/tag_cloud.html.twig" %}
```

## Tailwind CSS v4 + Alpine.js

フロントエンドは Tailwind CSS v4 と Alpine.js の組み合わせです。

- **ダークモード**: OS 設定を自動検出、ヘッダーのトグルで切り替え
- **ハンバーガーメニュー**: SP・PC 共通、右からスライドインするドロワー
- **タグクラウド**: 出現数を min-max 正規化して 1〜20 段階のサイズで表示

## OGP / SNS メタタグ

記事ページでは OGP タグを自動生成します。アイキャッチ画像がある場合は `twitter:card` が `summary_large_image` に切り替わります。

## GitHub リポジトリとの同期

コンテンツを GitHub リポジトリで管理し、管理画面の「GitHub 同期」ボタンで取り込む機能を備えています。

```
GitHub リポジトリ = 正式データ（Single Source of Truth）
CMS の contents/  = システムキャッシュ
```

SHA を比較して差分のみ更新するため、ファイル数が増えても効率的に動作します。

## 静的サイトへの対応

記事 URL は `/hardware/2024-10-11-new-mac-mini.html` のように `.html` 拡張子付きで設計されています。将来的な静的出力にも対応しやすい構造です。

---

このように、a-column PHP は「シンプルさ」と「拡張性」を両立した軽量 CMS です。次のステップとして Claude API を使った AI 記事生成にも取り組んでいます。