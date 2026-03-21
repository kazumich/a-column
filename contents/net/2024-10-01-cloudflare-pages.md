---
title: "Cloudflare Pages で静的サイトを無料公開する"
date: "2024-10-01 10:00:00"
author: "kazumich"
category: net
tags: [cloudflare, hosting, jamstack]
eyecatch: "https://images.unsplash.com/photo-1478386900285-256cb4ea9fe1?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w5MDE2NjV8MHwxfHJhbmRvbXx8fHx8fHx8fDE3NzQwODM0OTR8&ixlib=rb-4.1.0&q=80&w=1080"
---
**Cloudflare Pages** を使うと、静的サイトを無料でグローバルCDNから配信できます。

## セットアップ手順

1. GitHub リポジトリに静的ファイルをプッシュ
2. Cloudflare ダッシュボードで「Pages」→「Create a project」
3. GitHub を連携してリポジトリを選択
4. ビルドコマンドと出力ディレクトリを設定

## カスタムドメイン

独自ドメインの設定も無料で、証明書も自動発行されます。
Cloudflare で DNS を管理していれば数クリックで完了します。

## 感想

無料プランでも帯域制限がなく、個人サイト運営には十分すぎるスペックです。
