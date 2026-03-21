<?php

declare(strict_types=1);

namespace AColumn\Core;

class Request
{
    public readonly string $method;
    public readonly string $uri;
    public readonly string $path;

    public function __construct()
    {
        $this->method = $_SERVER['REQUEST_METHOD'] ?? 'GET';
        $this->uri    = $_SERVER['REQUEST_URI'] ?? '/';
        $this->path   = strtok($this->uri, '?') ?: '/';
    }

    public function get(string $key, mixed $default = null): mixed
    {
        return $_GET[$key] ?? $default;
    }

    public function post(string $key, mixed $default = null): mixed
    {
        return $_POST[$key] ?? $default;
    }
}
