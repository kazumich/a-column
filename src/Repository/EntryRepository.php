<?php

declare(strict_types=1);

namespace AColumn\Repository;

use AColumn\Core\Config;
use AColumn\Model\Entry;
use Parsedown;
use Symfony\Component\Yaml\Yaml;

class EntryRepository
{
    private Parsedown $parsedown;

    public function __construct(
        private readonly string $basePath,
        private readonly Config $config,
    ) {
        $this->parsedown = new Parsedown();
        $this->parsedown->setSafeMode(false);
    }

    /** @return Entry[] */
    public function findAll(?string $category, int $page = 1, int $perPage = 10): array
    {
        $entries = $this->loadAll($category);
        $offset  = ($page - 1) * $perPage;
        return array_slice($entries, $offset, $perPage);
    }

    public function countAll(?string $category): int
    {
        return count($this->loadAll($category));
    }

    /**
     * 全記事のタグを集計して件数順に返す
     * @return array<string, int>  ['php' => 5, 'apple' => 3, ...]
     */
    public function aggregateTags(): array
    {
        $counts = [];
        foreach ($this->loadAll(null) as $entry) {
            foreach ($entry->tags as $tag) {
                $counts[$tag] = ($counts[$tag] ?? 0) + 1;
            }
        }
        arsort($counts);
        return $counts;
    }

    /** 全記事を返す（インデックスビルド用） */
    public function findAllEntries(): array
    {
        return $this->loadAll(null);
    }

    /** 指定タグをすべて持つ記事を返す（AND検索） */
    public function findByTags(array $tags, int $page = 1, int $perPage = 10): array
    {
        $filtered = $this->filterByTags($tags);
        return array_slice($filtered, ($page - 1) * $perPage, $perPage);
    }

    public function countByTags(array $tags): int
    {
        return count($this->filterByTags($tags));
    }

    /**
     * 選択タグで絞り込んだ記事群の中で、選択外タグを件数順に返す
     * @return array<string, int>
     */
    public function relatedTags(array $selectedTags): array
    {
        $counts = [];
        foreach ($this->filterByTags($selectedTags) as $entry) {
            foreach ($entry->tags as $tag) {
                if (!in_array($tag, $selectedTags, true)) {
                    $counts[$tag] = ($counts[$tag] ?? 0) + 1;
                }
            }
        }
        arsort($counts);
        return $counts;
    }

    /** @return Entry[] */
    private function filterByTags(array $tags): array
    {
        return array_values(array_filter(
            $this->loadAll(null),
            fn(Entry $e) => count(array_intersect($tags, $e->tags)) === count($tags)
        ));
    }

    public function findById(string $category, string $slug): ?Entry
    {
        $pattern = $this->basePath . '/' . $category . '/' . $slug . '.md';
        if (!file_exists($pattern)) {
            return null;
        }
        return $this->parseFile($pattern, $category);
    }

    /** @return Entry[] sorted by date desc */
    private function loadAll(?string $category): array
    {
        $entries = [];

        if ($category !== null) {
            $dir = $this->basePath . '/' . $category;
            if (is_dir($dir)) {
                foreach (glob($dir . '/*.md') as $file) {
                    $entry = $this->parseFile($file, $category);
                    if ($entry !== null) {
                        $entries[] = $entry;
                    }
                }
            }
        } else {
            foreach (glob($this->basePath . '/*/') as $dir) {
                $cat = basename($dir);
                foreach (glob($dir . '*.md') as $file) {
                    $entry = $this->parseFile($file, $cat);
                    if ($entry !== null) {
                        $entries[] = $entry;
                    }
                }
            }
        }

        usort($entries, fn(Entry $a, Entry $b) => $b->date <=> $a->date);

        return $entries;
    }

    private function parseFile(string $path, string $category): ?Entry
    {
        $raw = file_get_contents($path);
        if ($raw === false) {
            return null;
        }

        [$frontMatter, $body] = $this->splitFrontMatter($raw);

        $title       = $frontMatter['title'] ?? basename($path, '.md');
        $author      = $frontMatter['author'] ?? '';
        $eyecatch    = $frontMatter['eyecatch'] ?? '';
        $description = $frontMatter['description'] ?? '';
        $tags        = $frontMatter['tags'] ?? [];
        if (is_string($tags)) {
            $tags = array_map('trim', explode(',', $tags));
        }

        $dateStr = $frontMatter['date'] ?? null;
        try {
            $date = $dateStr
                ? new \DateTimeImmutable($dateStr)
                : \DateTimeImmutable::createFromFormat('U', (string)filemtime($path));
        } catch (\Exception) {
            $date = new \DateTimeImmutable();
        }

        $html = $this->parsedown->text($body);
        $slug = basename($path, '.md');

        return new Entry(
            slug:        $slug,
            category:    $category,
            title:       $title,
            date:        $date,
            author:      $author,
            tags:        (array)$tags,
            htmlBody:    $html,
            eyecatch:    $eyecatch,
            description: $description,
        );
    }

    private function splitFrontMatter(string $content): array
    {
        if (!str_starts_with($content, '---')) {
            return [[], $content];
        }

        $end = strpos($content, '---', 3);
        if ($end === false) {
            return [[], $content];
        }

        $yaml = substr($content, 3, $end - 3);
        $body = ltrim(substr($content, $end + 3));

        try {
            $frontMatter = Yaml::parse($yaml) ?? [];
        } catch (\Exception) {
            $frontMatter = [];
        }

        return [$frontMatter, $body];
    }
}
