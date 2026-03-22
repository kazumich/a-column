<?php

declare(strict_types=1);

namespace AColumn\Core;

class AdminAuth
{
    public function __construct(private readonly Config $config) {}

    public function isLoggedIn(): bool
    {
        return isset($_SESSION['admin_logged_in']) && $_SESSION['admin_logged_in'] === true;
    }

    public function login(string $username, string $password): bool
    {
        $validUsername = $this->config->get('admin.username', 'admin');
        $validPassword = $this->config->get('admin.password', '');
        if ($username === $validUsername && $password === $validPassword) {
            session_regenerate_id(true);
            $_SESSION['admin_logged_in'] = true;
            $_SESSION['csrf_token'] = bin2hex(random_bytes(32));
            return true;
        }
        return false;
    }

    public function logout(): void
    {
        $_SESSION = [];
        session_destroy();
    }

    public function requireLogin(): void
    {
        if (!$this->isLoggedIn()) {
            header('Location: /admin/login');
            exit;
        }
    }

    public function getCsrfToken(): string
    {
        if (!isset($_SESSION['csrf_token'])) {
            $_SESSION['csrf_token'] = bin2hex(random_bytes(32));
        }
        return $_SESSION['csrf_token'];
    }

    public function validateCsrf(string $token): bool
    {
        return isset($_SESSION['csrf_token']) && hash_equals($_SESSION['csrf_token'], $token);
    }
}
