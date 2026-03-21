<?php

declare(strict_types=1);

namespace AColumn\Repository;

use AColumn\Core\Config;
use AColumn\Model\Category;

class CategoryRepository
{
    public function __construct(private readonly Config $config) {}

    /** @return Category[] */
    public function findAll(): array
    {
        $raw = $this->config->get('categories', []);
        $result = [];
        foreach ($raw as $slug => $data) {
            $result[] = new Category(
                slug:        $slug,
                label:       $data['label'] ?? $slug,
                description: $data['description'] ?? '',
            );
        }
        return $result;
    }

    public function findBySlug(string $slug): ?Category
    {
        foreach ($this->findAll() as $category) {
            if ($category->slug === $slug) {
                return $category;
            }
        }
        return null;
    }
}
