<?php

declare(strict_types=1);

namespace AColumn\Core;

use Symfony\Component\Yaml\Yaml;

class Config
{
    private array $data = [];

    public function load(string $file): void
    {
        if (!file_exists($file)) {
            throw new \RuntimeException("Config file not found: {$file}");
        }
        $parsed = Yaml::parseFile($file);
        $this->data = array_merge_recursive($this->data, $parsed ?? []);
    }

    public function get(string $key, mixed $default = null): mixed
    {
        $keys = explode('.', $key);
        $value = $this->data;
        foreach ($keys as $k) {
            if (!is_array($value) || !array_key_exists($k, $value)) {
                return $default;
            }
            $value = $value[$k];
        }
        return $value;
    }
}
