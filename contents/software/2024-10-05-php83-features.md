---
title: "PHP 8.3 の新機能まとめ"
date: "2024-10-05 14:30:00"
author: "kazumich"
category: software
tags: [php, programming]
eyecatch: "https://picsum.photos/seed/2024-10-05-php83-features/1200/630"
---
PHP 8.3 がリリースされました。主な新機能を紹介します。

## 型付き定数

クラス定数に型を指定できるようになりました。

```php
class Config {
    const string VERSION = '1.0.0';
    const int MAX_RETRIES = 3;
}
```

## json_validate()

JSON 文字列の検証専用関数が追加されました。

```php
if (json_validate($input)) {
    $data = json_decode($input);
}
```

## readonly プロパティの動的変更

`readonly` クラスのクローン時に特定プロパティを変更できるようになりました（`clone with`）。

PHP 8.x シリーズは着実に型システムが強化されており、大規模開発での採用がより安心になってきました。
