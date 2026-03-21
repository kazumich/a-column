# a-column PHP — 仕様書

> 2000〜2004年に Perl で運用していた個人 CMS「a-column v2.31」の PHP リニューアル版。
> データベース不使用・ファイルベースの軽量 CMS。

---

## 目次

1. [概要](#概要)
2. [技術スタック](#技術スタック)
3. [ディレクトリ構成](#ディレクトリ構成)
4. [セットアップ](#セットアップ)
5. [設定ファイル](#設定ファイル)
6. [コンテンツ管理](#コンテンツ管理)
7. [URL ルーティング](#urlルーティング)
8. [アーキテクチャ](#アーキテクチャ)
9. [テンプレートシステム](#テンプレートシステム)
10. [タグ検索・インデックス](#タグ検索インデックス)
11. [フロントエンド](#フロントエンド)
12. [OGP / SNS メタタグ](#ogp--sns-メタタグ)
13. [アイキャッチ画像](#アイキャッチ画像)
14. [CLI ツール](#cli-ツール)
15. [今後の拡張予定](#今後の拡張予定)

---

## 概要

| 項目 | 内容 |
|------|------|
| 言語 | PHP 8.1+ |
| フレームワーク | なし（素の PHP） |
| テンプレートエンジン | Twig 3 |
| コンテンツ形式 | Markdown + YAML フロントマター |
| データストア | ファイルシステム（DB 不使用） |
| CSS | Tailwind CSS v4 |
| JS | Alpine.js v3 |

---

## 技術スタック

### PHP（Composer）

| パッケージ | 用途 |
|-----------|------|
| `twig/twig ^3.0` | テンプレートエンジン |
| `symfony/yaml ^6\|^7` | YAML パーサー（設定・フロントマター） |
| `erusev/parsedown ^1.7` | Markdown → HTML 変換 |

### Node.js（npm）

| パッケージ | 用途 |
|-----------|------|
| `tailwindcss ^4` | CSS フレームワーク |
| `@tailwindcss/cli` | v4 用 CLI ビルドツール |
| `@tailwindcss/typography` | Markdown 本文の prose スタイル |

### フロントエンド（CDN）

| ライブラリ | 用途 |
|-----------|------|
| Alpine.js v3 | リアクティブ UI（ドロワー・ダークモード） |

### CSS ビルドコマンド

```bash
npm run build   # ビルド（minify あり）
npm run watch   # ウォッチモード
```

> **重要:** テンプレートに新しい Tailwind クラスを追加した場合は必ず `npm run build` を実行すること。
> Tailwind CSS v4 はテンプレートを静的スキャンするため、ビルドしないと新規クラスが CSS に含まれない。

ソース: `src/css/input.css` → 出力: `public/assets/css/style.css`

---

## ディレクトリ構成

```
a-column/
├── bin/
│   └── fetch-eyecatch.php       # Unsplash アイキャッチ取得 CLI
├── config/
│   ├── site.yaml                # サイト設定
│   └── categories.yaml          # カテゴリ定義
├── contents/                    # 記事 Markdown ファイル
│   ├── hardware/
│   ├── software/
│   └── net/
├── document/                    # ドキュメント（本ファイル等）
│   └── spec.md
├── public/                      # Web ルート（ここだけ公開）
│   ├── index.php                # フロントコントローラー
│   └── assets/css/style.css     # Tailwind ビルド済み CSS
├── src/
│   ├── Core/
│   │   ├── Application.php      # アプリケーション本体
│   │   ├── Config.php           # YAML 設定ローダー
│   │   ├── Request.php          # HTTP リクエスト抽象化
│   │   └── Router.php           # URL ルーター
│   ├── Model/
│   │   ├── Entry.php            # 記事バリューオブジェクト
│   │   └── Category.php         # カテゴリバリューオブジェクト
│   ├── Repository/
│   │   ├── EntryRepository.php      # Markdown ファイル読み取り
│   │   ├── CategoryRepository.php   # カテゴリ読み取り
│   │   └── TagIndexRepository.php   # タグインデックス管理
│   ├── Module/                  # モジュール（将来拡張用）
│   └── css/
│       └── input.css            # Tailwind CSS ソース
├── themes/
│   └── default/
│       ├── layout.html.twig     # 共通レイアウト
│       ├── home.html.twig       # トップページ
│       ├── category.html.twig   # カテゴリ一覧
│       ├── entry.html.twig      # 記事詳細
│       ├── tag.html.twig        # タグ検索
│       ├── 404.html.twig        # 404 ページ
│       └── modules/
│           ├── entry_summary.html.twig   # 記事カード
│           ├── entry_detail.html.twig    # 記事本文
│           ├── category_list.html.twig   # カテゴリナビ
│           ├── tag_cloud.html.twig       # タグクラウド
│           └── pagination.html.twig      # ページネーション
├── var/cache/
│   ├── twig/                    # Twig コンパイル済みテンプレート
│   └── tags/                    # タグインデックス JSON（自動生成）
│       ├── php.json
│       ├── mac.json
│       └── .last_built          # インデックス最終ビルド時刻
├── .env                         # 環境変数（git 管理外）
├── .env.example                 # 環境変数テンプレート
├── composer.json
└── package.json
```

---

## セットアップ

```bash
composer install
npm install
npm run build
php -S localhost:8080 -t public/
```

### 環境変数

`.env.example` をコピーして `.env` を作成する。

```
UNSPLASH_ACCESS_KEY=your_access_key_here
```

---

## 設定ファイル

### `config/site.yaml`

```yaml
site:
  name: "a-column"
  description: "20数年ぶりにアップデート"
  url: "http://localhost:8080"
  timezone: "Asia/Tokyo"
  entries_per_page: 10           # カテゴリ・タグ一覧の1ページあたり表示件数
  home_entries_per_category: 5   # トップページの1カテゴリあたり表示件数
  tag_cloud_min_count: 2         # タグクラウドに表示する最低記事数
  excerpt_length: 200            # 自動抜粋の文字数
  date_format: "Y/m/d"
  theme: "default"
```

### `config/categories.yaml`

```yaml
categories:
  hardware:
    label: "Hardware"
    description: "ハードウェアに関する話題"
  software:
    label: "Software"
    description: "ソフトウェアに関する話題"
  net:
    label: "Internet"
    description: "インターネットに関する話題"
```

カテゴリの追加はこのファイルに追記し、`contents/` 以下に同名ディレクトリを作成する。

---

## コンテンツ管理

### ファイル配置

```
contents/{category}/{YYYY-MM-DD-slug}.md
```

例: `contents/hardware/2024-10-11-new-mac-mini.md`

### フロントマター形式

```markdown
---
title: "記事タイトル"
date: "2024-10-11 10:00:00"
author: "kazumich"
category: hardware
tags: [apple, macbook, m4]
eyecatch: "https://images.unsplash.com/..."
description: "手動で設定する抜粋テキスト（省略可）"
---

記事本文を **Markdown** で書く。
```

| フィールド | 必須 | 説明 |
|-----------|------|------|
| `title` | ✓ | 記事タイトル |
| `date` | ✓ | 公開日時（`Y-m-d H:i:s` 形式） |
| `author` | ✓ | 著者名 |
| `category` | ✓ | カテゴリスラッグ（categories.yaml と一致） |
| `tags` | — | タグの配列 |
| `eyecatch` | — | アイキャッチ画像 URL |
| `description` | — | 手動抜粋（設定時は自動抜粋より優先） |

### 抜粋（excerpt）の動作

1. `description` が設定されていればそれを使用
2. 未設定の場合は本文 HTML からタグを除去・空白を正規化し、`excerpt_length` 文字で切り `…` を付与

---

## URL ルーティング

| URL | テンプレート | 説明 |
|-----|------------|------|
| `/` | `home.html.twig` | トップ（カテゴリ別新着） |
| `/{category}/` | `category.html.twig` | カテゴリ一覧（1ページ目） |
| `/{category}/page/{n}/` | `category.html.twig` | カテゴリ一覧（n ページ目） |
| `/{category}/{slug}.html` | `entry.html.twig` | 記事詳細 |
| `/tag/{tags}/` | `tag.html.twig` | タグ検索（1ページ目） |

### タグ複合検索

`+` 区切りで AND 検索。

```
/tag/apple+macbook/    → apple かつ macbook のタグを持つ記事
```

### URL の末尾 `.html`

記事詳細 URL は `.html` で終わる形式。静的サイトへのパブリッシュを見据えた設計。

---

## アーキテクチャ

### リクエスト処理フロー

```
public/index.php
  └─ Application::__construct()
       ├─ Config::load()                    # site.yaml / categories.yaml 読み込み
       ├─ TagIndexRepository::ensureUpToDate()  # タグインデックス自動更新
       └─ Twig::Environment 初期化

Application::run()
  └─ Router::dispatch()                     # URL マッチング
       └─ renderHome() / renderCategory() / renderEntry() / renderTag()
            ├─ EntryRepository             # Markdown ファイル読み取り
            ├─ TagIndexRepository          # タグ検索（JSON インデックス）
            ├─ CategoryRepository          # カテゴリ情報
            └─ Twig::render()              # テンプレート描画
```

### 主要クラス

#### `src/Core/Application.php`

- アプリケーション全体のブートストラップ
- ルーティング定義とハンドラー登録
- Twig 環境の初期化（キャッシュ: `var/cache/twig/`）
- `baseData()` で全テンプレート共通変数を生成（タグクラウド・カテゴリリスト・現在 URL）

**タグクラウド正規化（min-max normalization）:**

```php
$min   = min($tagCounts);
$max   = max($tagCounts);
$range = max($max - $min, 1);
$size  = (int) round(($count - $min) / $range * 19) + 1;
// → 最も少ないタグが size-1、最も多いタグが size-20
```

#### `src/Core/Router.php`

- `{param}` 形式のプレースホルダーを正規表現に変換
- リテラル部分は `preg_quote()` でエスケープ（`.html` の `.` など）

```php
$regex = preg_replace_callback(
    '/\{(\w+)\}|([^{}]+)/',
    function (array $m): string {
        if (isset($m[1]) && $m[1] !== '') {
            return '(?P<' . $m[1] . '>[^/]+)';
        }
        return preg_quote($m[2], '#');
    },
    $pattern
);
```

#### `src/Model/Entry.php`

- 記事のバリューオブジェクト（イミュータブル・readonly プロパティ）
- `getExcerpt()` / `toArray()` メソッドを持つ
- URL は `/{category}/{slug}.html`

| プロパティ | 型 | 必須 |
|-----------|-----|------|
| `slug` | string | ✓ |
| `category` | string | ✓ |
| `title` | string | ✓ |
| `date` | DateTimeImmutable | ✓ |
| `author` | string | ✓ |
| `tags` | array | — |
| `htmlBody` | string | ✓ |
| `eyecatch` | string | — |
| `description` | string | — |

#### `src/Repository/EntryRepository.php`

- `contents/{category}/*.md` をスキャン
- Parsedown で Markdown → HTML 変換
- Symfony YAML でフロントマター解析
- 日付降順ソート、ページネーション対応

#### `src/Repository/TagIndexRepository.php`

タグ別 JSON インデックスの生成・クエリを担当。詳細は「タグ検索・インデックス」参照。

---

## テンプレートシステム

### 継承構造

```
layout.html.twig          ← 全ページの基底
  ├─ home.html.twig
  ├─ category.html.twig
  ├─ entry.html.twig      ← OGP ブロックをオーバーライド
  ├─ tag.html.twig
  └─ 404.html.twig
```

### Twig ブロック一覧

| ブロック名 | デフォルト値 | 用途 |
|-----------|------------|------|
| `title` | `site.name` | `<title>` タグ |
| `og_title` | `site.name` | OGP タイトル |
| `og_description` | `site.description` | OGP 説明文 |
| `og_type` | `website` | OGP タイプ |
| `og_image` | （空） | OGP 画像 `<meta>` タグ |
| `twitter_card` | `summary` | Twitter Card タイプ |
| `content` | （空） | ページ本文 |

### テンプレート変数

#### 全ページ共通（`baseData()`）

| 変数 | 型 | 内容 |
|------|----|------|
| `site` | array | `site.yaml` の値（name, description, url） |
| `categories` | array | 全カテゴリ（`toArray()`） |
| `tag_cloud` | array | タグクラウド用データ（`name`, `count`, `size`, `url`） |
| `current_url` | string | 現在ページの絶対 URL（OGP 用） |

---

## タグ検索・インデックス

### 設計方針

DB を使わずに最大 1 万件規模に対応するため、タグごとに JSON ファイルをキャッシュする。

### JSON インデックスの仕組み

```
var/cache/tags/
  ├── apple.json          # "apple" タグを持つ全記事
  ├── macbook.json
  ├── ...
  └── .last_built         # 最終ビルド時刻（UNIX タイムスタンプ）のマーカー
```

#### 自動更新タイミング

初回アクセス時またはコンテンツ変更後の最初のアクセス時に自動再ビルド。

```
Application::__construct()
  └─ TagIndexRepository::ensureUpToDate(fn() => EntryRepository::findAllEntries())
```

`contents/*/*.md` の全ファイルの `filemtime` 最大値を `.last_built` のタイムスタンプと比較し、新しければ再ビルド。

#### JSON ファイルの構造（1タグあたり）

```json
[
  {
    "slug": "2024-10-11-new-mac-mini",
    "category": "hardware",
    "title": "新型 Mac mini レビュー",
    "date": "2024/10/11",
    "datetime": "2024-10-11T10:00:00+09:00",
    "author": "kazumich",
    "tags": ["apple", "macbook", "m4"],
    "eyecatch": "https://images.unsplash.com/...",
    "url": "/hardware/2024-10-11-new-mac-mini.html",
    "excerpt": "概要テキスト..."
  }
]
```

### AND 検索の実装

複数タグ指定時、各タグの JSON からスラッグ一覧を取得し `array_intersect()` で絞り込む。

```
/tag/php+mac → php.json の slug ∩ mac.json の slug で絞り込み
```

### 関連タグ

選択中のタグで絞り込んだ結果に含まれる全タグのうち、選択済みでないものを出現数降順で表示。追加絞り込みリンクを提供。

### タグクラウド表示しきい値

`tag_cloud_min_count`（現在: 2）未満の出現数のタグはタグクラウドに表示しない。

---

## フロントエンド

### Tailwind CSS v4

設定ファイルは `src/css/input.css`（v4 では CSS ファイルで設定）。

```css
@import "tailwindcss";
@plugin "@tailwindcss/typography";
@source "../../themes";

@custom-variant dark (&:where(.dark, .dark *));
```

### ダークモード

- `<html>` 要素に `.dark` クラスを付与する方式
- ページ表示前に `<head>` 内のインラインスクリプトで適用（FOUC 防止）

```html
<script>
  if (localStorage.getItem('theme') === 'dark' ||
      (!localStorage.getItem('theme') && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
    document.documentElement.classList.add('dark');
  }
</script>
```

- localStorage に `theme` を保存、未設定時は OS 設定に従う
- ヘッダーの太陽/月アイコンボタンでトグル

### Alpine.js レイアウト

`<body>` の `x-data` でアプリ全体の状態を管理。

```js
{
  sidebarOpen: false,   // ドロワーの開閉
  isDark: ...,          // ダークモード状態
  toggleDark() { ... }
}
```

### ハンバーガーメニュー・ドロワー

- SP・PC 共通でヘッダー右上にハンバーガーボタンを表示（PC でもサイドバーは非表示がデフォルト）
- クリックでオーバーレイとドロワーが表示
- ドロワー内にカテゴリナビ＋タグクラウド

**アニメーション:**

| 要素 | 表示 | 非表示 |
|------|------|--------|
| オーバーレイ（黒半透明） | フェードイン 500ms ease-out | フェードアウト 400ms ease-in |
| ドロワー（右からスライド） | スライドイン 500ms ease-out | スライドアウト 400ms ease-in |

### タグクラウドサイズクラス

`@layer components` で定義。出現数の相対的な大きさを min-max 正規化した 1〜20 の CSS クラスで表現。

```
size = round((count - min) / (max - min) * 19) + 1
```

| クラス | スタイル |
|--------|---------|
| `.tag-size-1`, `.tag-size-2` | `text-xs` |
| `.tag-size-3`, `.tag-size-4` | `text-xs font-medium` |
| `.tag-size-5`, `.tag-size-6` | `text-sm` |
| `.tag-size-7`, `.tag-size-8` | `text-sm font-medium` |
| `.tag-size-9`, `.tag-size-10` | `text-base` |
| `.tag-size-11`, `.tag-size-12` | `text-base font-medium` |
| `.tag-size-13`〜`.tag-size-15` | `text-lg font-semibold` |
| `.tag-size-16`〜`.tag-size-18` | `text-xl font-semibold` |
| `.tag-size-19`, `.tag-size-20` | `text-2xl font-bold` |

---

## OGP / SNS メタタグ

`layout.html.twig` に共通タグを配置し、記事詳細ページ（`entry.html.twig`）でブロックをオーバーライドする。

### 全ページ共通タグ

```html
<meta property="og:site_name" content="{{ site.name }}">
<meta property="og:title" content="...">
<meta property="og:description" content="...">
<meta property="og:url" content="{{ current_url }}">
<meta property="og:type" content="website">
<meta name="twitter:card" content="summary">
<meta name="robots" content="noindex, nofollow">
```

### 記事詳細ページでのオーバーライド

```twig
{% block og_title %}{{ entry.title }}{% endblock %}
{% block og_description %}{{ entry.excerpt }}{% endblock %}
{% block og_type %}article{% endblock %}
{% block twitter_card %}{{ entry.eyecatch ? 'summary_large_image' : 'summary' }}{% endblock %}
{% block og_image %}
  {% if entry.eyecatch %}
    <meta property="og:image" content="{{ entry.eyecatch }}">
  {% endif %}
{% endblock %}
```

### noindex 設定

現在はサンプル段階のため全ページに `noindex, nofollow` を設定。

本番公開時は `layout.html.twig` の以下を変更：

```html
<!-- 現在（開発・サンプル） -->
<meta name="robots" content="noindex, nofollow">

<!-- 本番時 -->
<meta name="robots" content="index, follow">
```

---

## アイキャッチ画像

### フロントマター設定

```yaml
eyecatch: "https://images.unsplash.com/photo-xxxxx?..."
```

### 詳細ページの表示仕様

- `aspect-video`（16:9）の比率でクロップ表示
- `object-cover` でリサイズ

```twig
<div class="w-full aspect-video rounded-lg mb-8 overflow-hidden">
  <img src="{{ entry.eyecatch }}" alt="{{ entry.title }}"
       class="w-full h-full object-cover">
</div>
```

- OGP `og:image` にも使用
- eyecatch がある場合は Twitter Card が `summary_large_image` になる

---

## CLI ツール

### `bin/fetch-eyecatch.php`

Unsplash API を使って全記事のアイキャッチ画像を一括取得し、フロントマターの `eyecatch` フィールドを更新する。

#### 使い方

```bash
php bin/fetch-eyecatch.php           # 未設定の記事のみ更新
php bin/fetch-eyecatch.php --force   # 設定済みも含めて全て上書き
```

#### 動作仕様

1. `.env` から `UNSPLASH_ACCESS_KEY` を読み込む
2. 各記事のタグからキーワードを決定（`$keywordMap` で対応表を定義）
3. `GET https://api.unsplash.com/photos/random?query={keyword}&orientation=landscape&client_id={key}` を呼び出す
4. レスポンスの `urls.regular` を `eyecatch` フィールドに書き込む
5. 既に `images.unsplash.com` の URL が設定済みの場合はスキップ（`--force` で上書き可）
6. レート制限対策として 1.5 秒インターバル（無料プラン: 50 req/h）

#### 必要な環境変数

| 変数 | 取得方法 |
|------|---------|
| `UNSPLASH_ACCESS_KEY` | [unsplash.com/oauth/applications](https://unsplash.com/oauth/applications) で発行 |

---

## 今後の拡張予定

- [ ] 管理画面（記事の作成・編集・削除）→ a-column-admin として別ブランチ or 別リポジトリで開発予定
- [ ] 静的サイトへのパブリッシュ機能
- [ ] 全文検索
- [ ] RSS フィード
- [ ] サイトマップ生成
- [ ] 本番公開時の robots 設定変更（noindex → index, follow）

---

*最終更新: 2026-03-21*
