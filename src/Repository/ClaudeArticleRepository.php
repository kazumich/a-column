<?php

declare(strict_types=1);

namespace AColumn\Repository;

class ClaudeArticleRepository
{
    private ?string $apiKey;

    public function __construct()
    {
        $this->apiKey = ($_ENV['ANTHROPIC_API_KEY'] ?? '') ?: null;
    }

    public function isConfigured(): bool
    {
        return $this->apiKey !== null;
    }

    /**
     * Claude API を使って記事を生成する。
     *
     * @return array{ success: bool, content?: string, error?: string }
     */
    public function generate(
        string $theme,
        string $category,
        string $instructions,
        string $author,
        string $date
    ): array {
        if (!$this->isConfigured()) {
            return ['success' => false, 'error' => 'ANTHROPIC_API_KEY が設定されていません'];
        }

        $prompt = $this->buildPrompt($theme, $category, $instructions, $author, $date);

        $requestBody = json_encode([
            'model'      => 'claude-sonnet-4-6',
            'max_tokens' => 4000,
            'messages'   => [
                ['role' => 'user', 'content' => $prompt],
            ],
        ]);

        $ch = curl_init('https://api.anthropic.com/v1/messages');
        curl_setopt_array($ch, [
            CURLOPT_POST           => true,
            CURLOPT_POSTFIELDS     => $requestBody,
            CURLOPT_RETURNTRANSFER => true,
            CURLOPT_TIMEOUT        => 120,
            CURLOPT_HTTPHEADER     => [
                'Content-Type: application/json',
                'x-api-key: ' . $this->apiKey,
                'anthropic-version: 2023-06-01',
            ],
        ]);
        $response = curl_exec($ch);
        $curlError = curl_error($ch);

        if ($response === false) {
            return ['success' => false, 'error' => 'API への接続に失敗しました: ' . $curlError];
        }

        $data = json_decode($response, true);
        if (!is_array($data)) {
            return ['success' => false, 'error' => 'API レスポンスの解析に失敗しました'];
        }

        if (isset($data['error'])) {
            return ['success' => false, 'error' => $data['error']['message'] ?? 'API エラー'];
        }

        $content = $data['content'][0]['text'] ?? '';
        if ($content === '') {
            return ['success' => false, 'error' => '生成結果が空でした'];
        }

        // ```markdown ... ``` で囲まれている場合は取り除く
        if (preg_match('/^```(?:markdown|md)?\s*\n(.*)\n```\s*$/s', trim($content), $m)) {
            $content = $m[1];
        }

        return ['success' => true, 'content' => trim($content)];
    }

    private function buildPrompt(
        string $theme,
        string $category,
        string $instructions,
        string $author,
        string $date
    ): string {
        $extra = $instructions !== '' ? "\n追加指示: {$instructions}" : '';

        return <<<PROMPT
あなたは技術ブログのライターです。以下のテーマで日本語のブログ記事を生成してください。

テーマ: {$theme}
カテゴリ: {$category}{$extra}

以下の形式で出力してください（コードブロックで囲まずに、そのまま出力してください）：

---
title: "記事タイトル"
date: "{$date}"
author: "{$author}"
category: {$category}
tags: [tag1, tag2, tag3]
eyecatch: ""
description: "SEO用の概要文（80〜120文字）"
---

## 見出し

本文をMarkdownで記述...

注意事項：
- eyecatch は必ず空文字列 "" にしてください（URLは入れないでください）
- tags は記事内容に合った英語の単語を3〜6個
- description は検索エンジン向けに簡潔に（日本語）
- 本文は1500〜2500文字程度
- 見出し（##、###）を使って読みやすく構成
- 実際に役立つ情報を含めてください
PROMPT;
    }
}
