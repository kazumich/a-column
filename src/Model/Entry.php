<?php

declare(strict_types=1);

namespace AColumn\Model;

class Entry
{
    public function __construct(
        public readonly string $slug,
        public readonly string $category,
        public readonly string $title,
        public readonly \DateTimeImmutable $date,
        public readonly string $author,
        public readonly array $tags,
        public readonly string $htmlBody,
        public readonly string $eyecatch = '',
        public readonly string $description = '',
        public readonly bool $published = true,
    ) {}

    /**
     * description が設定されていればそれを返す。
     * なければ本文を $chars 文字で切り、途中で切れた場合は … を付ける。
     */
    public function getExcerpt(int $chars = 200): string
    {
        if ($this->description !== '') {
            return $this->description;
        }

        $text = strip_tags($this->htmlBody);
        $text = trim(preg_replace('/\s+/', ' ', $text)); // 改行・連続空白を1スペースに
        if (mb_strlen($text) <= $chars) {
            return $text;
        }
        return mb_substr($text, 0, $chars) . '…';
    }

    public function toArray(int $excerptLength = 200): array
    {
        return [
            'slug'        => $this->slug,
            'category'    => $this->category,
            'title'       => $this->title,
            'date'        => $this->date->format('Y/m/d'),
            'datetime'    => $this->date->format('c'),
            'author'      => $this->author,
            'tags'        => $this->tags,
            'body'        => $this->htmlBody,
            'excerpt'     => $this->getExcerpt($excerptLength),
            'eyecatch'    => $this->eyecatch,
            'description' => $this->description,
            'url'         => '/' . $this->category . '/' . $this->slug . '.html',
            'published'   => $this->published,
        ];
    }
}
