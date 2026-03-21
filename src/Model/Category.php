<?php

declare(strict_types=1);

namespace AColumn\Model;

class Category
{
    public function __construct(
        public readonly string $slug,
        public readonly string $label,
        public readonly string $description,
    ) {}

    public function toArray(): array
    {
        return [
            'slug'        => $this->slug,
            'label'       => $this->label,
            'description' => $this->description,
            'url'         => '/' . $this->slug,
        ];
    }
}
