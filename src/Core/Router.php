<?php

declare(strict_types=1);

namespace AColumn\Core;

class Router
{
    private array $routes = [];

    public function add(string $method, string $pattern, callable $handler): void
    {
        // {param} をキャプチャグループに、それ以外のリテラル部分は正規表現エスケープ
        $regex = preg_replace_callback(
            '/\{(\w+)\}|([^{}]+)/',
            function (array $m): string {
                if (isset($m[1]) && $m[1] !== '') {
                    return '(?P<' . $m[1] . '>[^/]+)';
                }
                return preg_quote($m[2], '#');
            },
            $pattern
        );

        $this->routes[] = [
            'method'  => strtoupper($method),
            'pattern' => '#^' . $regex . '$#',
            'handler' => $handler,
        ];
    }

    public function dispatch(Request $request): array
    {
        foreach ($this->routes as $route) {
            if ($route['method'] !== $request->method) {
                continue;
            }
            if (preg_match($route['pattern'], $request->path, $matches)) {
                $params = array_filter($matches, 'is_string', ARRAY_FILTER_USE_KEY);
                return ['handler' => $route['handler'], 'params' => $params];
            }
        }
        return ['handler' => null, 'params' => []];
    }
}
