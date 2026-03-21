<?php

declare(strict_types=1);

namespace AColumn\Repository;

use AColumn\Core\Config;
use AColumn\Model\Entry;

class TagIndexRepository
{
    private string $indexDir;
    private string $markerFile;

    public function __construct(
        private readonly string $basePath,
        private readonly Config $config,
    ) {
        $this->indexDir   = $basePath . '/var/cache/tags';
        $this->markerFile = $this->indexDir . '/.last_built';
    }

    /**
     * インデックスが古ければ再構築する。
     * $loadEntries は再構築が必要な時だけ呼ばれる。
     */
    public function ensureUpToDate(callable $loadEntries): void
    {
        if ($this->needsRebuild()) {
            $this->build($loadEntries());
        }
    }

    // ---- クエリメソッド -----------------------------------------------

    /** 指定タグをすべて持つ記事（AND検索）をページネーションして返す */
    public function findByTags(array $tags, int $page = 1, int $perPage = 10): array
    {
        $all = $this->filterByTags($tags);
        return array_slice($all, ($page - 1) * $perPage, $perPage);
    }

    public function countByTags(array $tags): int
    {
        return count($this->filterByTags($tags));
    }

    /**
     * 選択タグで絞った結果の中にある、選択外タグを件数順で返す
     * @return array<string, int>
     */
    public function relatedTags(array $selectedTags): array
    {
        $counts = [];
        foreach ($this->filterByTags($selectedTags) as $entry) {
            foreach ($entry['tags'] as $tag) {
                if (!in_array($tag, $selectedTags, true)) {
                    $counts[$tag] = ($counts[$tag] ?? 0) + 1;
                }
            }
        }
        arsort($counts);
        return $counts;
    }

    /**
     * 全タグの件数を返す（タグクラウド用）
     * @return array<string, int>
     */
    public function aggregateTags(): array
    {
        $counts = [];
        foreach (glob($this->indexDir . '/*.json') ?: [] as $file) {
            $tag          = basename($file, '.json');
            $entries      = json_decode(file_get_contents($file), true) ?? [];
            $counts[$tag] = count($entries);
        }
        arsort($counts);
        return $counts;
    }

    // ---- ビルド -------------------------------------------------------

    private function needsRebuild(): bool
    {
        if (!file_exists($this->markerFile)) {
            return true;
        }

        $builtAt    = (int) file_get_contents($this->markerFile);
        $mdFiles    = glob($this->basePath . '/contents/*/*.md') ?: [];

        foreach ($mdFiles as $file) {
            if (filemtime($file) > $builtAt) {
                return true;
            }
        }

        return false;
    }

    /** @param Entry[] $entries */
    private function build(array $entries): void
    {
        if (!is_dir($this->indexDir)) {
            mkdir($this->indexDir, 0755, true);
        }

        // 既存 JSON をクリア
        foreach (glob($this->indexDir . '/*.json') ?: [] as $f) {
            unlink($f);
        }

        // タグ別にエントリを集める
        $tagMap = [];
        foreach ($entries as $entry) {
            $row = $this->entryToRow($entry);
            foreach ($entry->tags as $tag) {
                $tagMap[$tag][] = $row;
            }
        }

        // 各タグの JSON を書き出す
        foreach ($tagMap as $tag => $rows) {
            file_put_contents(
                $this->indexDir . '/' . $tag . '.json',
                json_encode($rows, JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT)
            );
        }

        file_put_contents($this->markerFile, (string) time());
    }

    private function entryToRow(Entry $entry): array
    {
        $excerptLength = (int) $this->config->get('site.excerpt_length', 200);

        return [
            'slug'     => $entry->slug,
            'category' => $entry->category,
            'title'    => $entry->title,
            'date'     => $entry->date->format($this->config->get('site.date_format', 'Y/m/d')),
            'datetime' => $entry->date->format('c'),
            'author'   => $entry->author,
            'tags'     => $entry->tags,
            'eyecatch' => $entry->eyecatch,
            'url'      => '/' . $entry->category . '/' . $entry->slug . '.html',
            'excerpt'  => $entry->getExcerpt($excerptLength),
        ];
    }

    // ---- 内部クエリ ---------------------------------------------------

    /** @return array[] */
    private function filterByTags(array $tags): array
    {
        if (empty($tags)) {
            return [];
        }

        // 最初のタグのエントリを基点にする
        $result = $this->loadTagEntries($tags[0]);

        // 残りのタグで AND 絞り込み
        foreach (array_slice($tags, 1) as $tag) {
            $otherSlugs = array_column($this->loadTagEntries($tag), 'slug');
            $result     = array_values(
                array_filter($result, fn($e) => in_array($e['slug'], $otherSlugs, true))
            );
        }

        return $result;
    }

    /** @return array[] */
    private function loadTagEntries(string $tag): array
    {
        $file = $this->indexDir . '/' . $tag . '.json';
        if (!file_exists($file)) {
            return [];
        }
        return json_decode(file_get_contents($file), true) ?? [];
    }
}
