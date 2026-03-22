<?php

declare(strict_types=1);

namespace AColumn\Core;

use AColumn\Repository\EntryRepository;
use AColumn\Repository\CategoryRepository;
use AColumn\Repository\TagIndexRepository;
use AColumn\Repository\GitHubSyncRepository;
use Twig\Environment;
use Twig\Loader\FilesystemLoader;

class Application
{
    private Config $config;
    private Request $request;
    private Router $router;
    private Environment $twig;
    private EntryRepository $entryRepo;
    private CategoryRepository $categoryRepo;
    private TagIndexRepository $tagIndex;
    private AdminAuth $auth;
    private GitHubSyncRepository $githubSync;
    private int $excerptLength;

    public function __construct(private readonly string $basePath)
    {
        date_default_timezone_set('Asia/Tokyo');

        $this->config = new Config();
        $this->config->load($basePath . '/config/site.yaml');
        $this->config->load($basePath . '/config/categories.yaml');

        $tz = $this->config->get('site.timezone', 'Asia/Tokyo');
        date_default_timezone_set($tz);

        // .env 読み込み（GitHub 同期などに使用）
        $this->loadEnv($basePath . '/.env');

        $this->request      = new Request();
        $this->router       = new Router();
        $this->entryRepo    = new EntryRepository($basePath . '/contents', $this->config);
        $this->categoryRepo = new CategoryRepository($this->config);
        $this->tagIndex     = new TagIndexRepository($basePath, $this->config);
        $this->auth         = new AdminAuth($this->config);
        $this->githubSync   = new GitHubSyncRepository($basePath);

        $this->excerptLength = (int) $this->config->get('site.excerpt_length', 200);

        // インデックスが古ければ再構築（ファイル変更時のみ全記事ロード）
        $this->tagIndex->ensureUpToDate(fn() => $this->entryRepo->findAllEntries());

        $theme  = $this->config->get('site.theme', 'default');
        $loader = new FilesystemLoader($basePath . '/themes/' . $theme);
        $this->twig = new Environment($loader, [
            'cache'       => $basePath . '/var/cache/twig',
            'auto_reload' => true,
        ]);

        $this->registerRoutes();
    }

    private function registerRoutes(): void
    {
        $app = $this;

        // --- admin routes ---
        $this->router->add('GET',  '/admin',                                        fn($p) => $this->redirectTo('/admin/entries'));
        $this->router->add('GET',  '/admin/login',                                  fn($p) => $this->renderAdminLogin($p));
        $this->router->add('POST', '/admin/login',                                  fn($p) => $this->handleAdminLogin($p));
        $this->router->add('GET',  '/admin/logout',                                 fn($p) => $this->handleAdminLogout($p));
        $this->router->add('GET',  '/admin/entries',                                fn($p) => $this->renderAdminEntries($p));
        $this->router->add('GET',  '/admin/entries/new',                            fn($p) => $this->renderAdminEntryForm($p));
        $this->router->add('POST', '/admin/entries/new',                            fn($p) => $this->handleAdminEntryCreate($p));
        $this->router->add('GET',  '/admin/entries/{category}/{slug}/edit',         fn($p) => $this->renderAdminEntryEdit($p));
        $this->router->add('POST', '/admin/entries/{category}/{slug}/edit',         fn($p) => $this->handleAdminEntryUpdate($p));
        $this->router->add('POST', '/admin/entries/{category}/{slug}/delete',       fn($p) => $this->handleAdminEntryDelete($p));
        $this->router->add('POST', '/admin/entries/{category}/{slug}/duplicate',    fn($p) => $this->handleAdminEntryDuplicate($p));
        $this->router->add('POST', '/admin/entries/{category}/{slug}/toggle-publish', fn($p) => $this->handleAdminTogglePublish($p));
        $this->router->add('POST', '/admin/upload/image',                             fn($p) => $this->handleAdminImageUpload($p));
        $this->router->add('GET',  '/admin/media',                                   fn($p) => $this->renderAdminMedia($p));
        $this->router->add('POST', '/admin/media/delete',                            fn($p) => $this->handleAdminMediaDelete($p));
        $this->router->add('POST', '/admin/sync',                                    fn($p) => $this->handleAdminSync($p));

        $this->router->add('GET', '/', function (array $params) use ($app): void {
            $app->renderHome($params);
        });

        $this->router->add('GET', '/tag/{tags}', function (array $params) use ($app): void {
            $params['page'] = (int)($app->getRequest()->get('page', 1));
            $app->renderTag($params);
        });

        $this->router->add('GET', '/{slug}', function (array $params) use ($app): void {
            $params['page'] = (int)($app->getRequest()->get('page', 1));
            $app->renderCategory($params);
        });

        $this->router->add('GET', '/{slug}/page/{page}', function (array $params) use ($app): void {
            $app->renderCategory($params);
        });

        $this->router->add('GET', '/{category}/{slug}.html', function (array $params) use ($app): void {
            $app->renderEntry($params);
        });
    }

    public function run(): void
    {
        $result = $this->router->dispatch($this->request);

        if ($result['handler'] === null) {
            http_response_code(404);
            echo $this->twig->render('404.html.twig', $this->baseData());
            return;
        }

        ($result['handler'])($result['params']);
    }

    public function renderHome(array $params): void
    {
        $categories = $this->categoryRepo->findAll();
        $grouped    = [];

        $limit = (int)$this->config->get('site.home_entries_per_category', 5);

        foreach ($categories as $category) {
            $entries = $this->entryRepo->findAll($category->slug, 1, $limit);
            $total   = $this->entryRepo->countAll($category->slug);
            $grouped[] = [
                'category' => $category->toArray(),
                'entries'  => array_map(fn($e) => $e->toArray($this->excerptLength), $entries),
                'total'    => $total,
                'has_more' => $total > $limit,
            ];
        }

        echo $this->twig->render('home.html.twig', array_merge($this->baseData(), [
            'grouped' => $grouped,
        ]));
    }

    public function renderCategory(array $params): void
    {
        $slug     = $params['slug'];
        $page     = (int)($params['page'] ?? $this->request->get('page', 1));
        $category = $this->categoryRepo->findBySlug($slug);

        if ($category === null) {
            http_response_code(404);
            echo $this->twig->render('404.html.twig', $this->baseData());
            return;
        }

        $perPage = (int)$this->config->get('site.entries_per_page', 10);
        $entries = $this->entryRepo->findAll($slug, $page, $perPage);
        $total   = $this->entryRepo->countAll($slug);

        echo $this->twig->render('category.html.twig', array_merge($this->baseData(), [
            'category'   => $category->toArray(),
            'entries'    => array_map(fn($e) => $e->toArray($this->excerptLength), $entries),
            'pagination' => $this->buildPagination($page, $total, $perPage, '/' . $slug),
        ]));
    }

    public function renderTag(array $params): void
    {
        $tagsParam    = $params['tags'];
        $selectedTags = array_values(array_filter(array_map('trim', explode('+', $tagsParam))));
        $page         = (int)($params['page'] ?? 1);
        $perPage      = (int)$this->config->get('site.entries_per_page', 10);

        $entries = $this->tagIndex->findByTags($selectedTags, $page, $perPage);
        $total   = $this->tagIndex->countByTags($selectedTags);

        // 選択中タグ（外すURL付き）
        $selectedTagList = array_map(function (string $tag) use ($selectedTags): array {
            $rest = array_values(array_filter($selectedTags, fn($t) => $t !== $tag));
            return [
                'name'       => $tag,
                'remove_url' => empty($rest) ? '/' : '/tag/' . implode('+', $rest),
            ];
        }, $selectedTags);

        // 絞り込み候補タグ（追加URL付き）
        $relatedTagList = [];
        foreach ($this->tagIndex->relatedTags($selectedTags) as $tag => $count) {
            $next   = $selectedTags;
            $next[] = $tag;
            sort($next);
            $relatedTagList[] = [
                'name'  => $tag,
                'count' => $count,
                'url'   => '/tag/' . implode('+', $next),
            ];
        }

        echo $this->twig->render('tag.html.twig', array_merge($this->baseData(), [
            'selected_tags' => $selectedTagList,
            'related_tags'  => $relatedTagList,
            'entries'       => $entries,
            'pagination'    => $this->buildPagination($page, $total, $perPage, '/tag/' . $tagsParam),
        ]));
    }

    public function renderEntry(array $params): void
    {
        $entry = $this->entryRepo->findById($params['category'], $params['slug']);

        if ($entry === null) {
            http_response_code(404);
            echo $this->twig->render('404.html.twig', $this->baseData());
            return;
        }

        echo $this->twig->render('entry.html.twig', array_merge($this->baseData(), [
            'entry' => $entry->toArray($this->excerptLength),
        ]));
    }

    private function baseData(): array
    {
        $minCount  = (int)$this->config->get('site.tag_cloud_min_count', 2);
        $tagCounts = array_filter(
            $this->tagIndex->aggregateTags(),
            fn(int $count) => $count >= $minCount
        );
        $min   = $tagCounts ? min($tagCounts) : 1;
        $max   = $tagCounts ? max($tagCounts) : 1;
        $range = max($max - $min, 1);

        $tagCloud = [];
        foreach ($tagCounts as $tag => $count) {
            // カウントを 1〜20 に正規化してサイズクラス番号にする
            $size = (int) round(($count - $min) / $range * 19) + 1;
            $tagCloud[] = [
                'name'  => $tag,
                'count' => $count,
                'size'  => $size,
                'url'   => '/tag/' . $tag,
            ];
        }

        $siteUrl = $this->config->get('site.url', '');

        return [
            'site'        => [
                'name'        => $this->config->get('site.name', 'a-column'),
                'description' => $this->config->get('site.description', ''),
                'url'         => $siteUrl,
            ],
            'current_url' => $siteUrl . $this->request->path,
            'categories' => array_map(
                fn($c) => $c->toArray(),
                $this->categoryRepo->findAll()
            ),
            'tag_cloud'  => $tagCloud,
            'is_admin'   => $this->auth->isLoggedIn(),
            'csrf_token' => $this->auth->getCsrfToken(),
        ];
    }

    private function buildPagination(int $page, int $total, int $perPage, string $baseUrl): array
    {
        $totalPages = (int) ceil($total / $perPage);
        return [
            'current_page' => $page,
            'total_pages'  => $totalPages,
            'total'        => $total,
            'prev_url'     => $page > 1 ? $baseUrl . '/page/' . ($page - 1) : null,
            'next_url'     => $page < $totalPages ? $baseUrl . '/page/' . ($page + 1) : null,
        ];
    }

    public function getRequest(): Request
    {
        return $this->request;
    }

    // -------------------------------------------------------------------------
    // Admin handlers
    // -------------------------------------------------------------------------

    private function redirectTo(string $url): void
    {
        header('Location: ' . $url);
        exit;
    }

    private function renderAdminLogin(array $params): void
    {
        echo $this->twig->render('admin/login.html.twig', array_merge($this->baseData(), [
            'error' => $_SESSION['login_error'] ?? null,
        ]));
        unset($_SESSION['login_error']);
    }

    private function handleAdminLogin(array $params): void
    {
        $username = trim($_POST['username'] ?? '');
        $password = $_POST['password'] ?? '';
        if ($this->auth->login($username, $password)) {
            $this->redirectTo('/admin/entries');
        } else {
            $_SESSION['login_error'] = 'ユーザー名またはパスワードが違います';
            $this->redirectTo('/admin/login');
        }
    }

    private function handleAdminLogout(array $params): void
    {
        $this->auth->logout();
        $this->redirectTo('/admin/login');
    }

    private function renderAdminEntries(array $params): void
    {
        $this->auth->requireLogin();
        $entries = $this->entryRepo->findAllForAdmin();

        $flash = $_SESSION['flash'] ?? null;
        unset($_SESSION['flash']);

        echo $this->twig->render('admin/entries.html.twig', array_merge($this->baseData(), [
            'entries'           => array_map(fn($e) => $e->toArray($this->excerptLength), $entries),
            'flash'             => $flash,
            'github_configured' => $this->githubSync->isConfigured(),
            'csrf_token'        => $this->auth->getCsrfToken(),
        ]));
    }

    private function renderAdminEntryForm(array $params): void
    {
        $this->auth->requireLogin();
        $categories = $this->categoryRepo->findAll();
        echo $this->twig->render('admin/entry_form.html.twig', array_merge($this->baseData(), [
            'categories'  => array_map(fn($c) => $c->toArray(), $categories),
            'entry'       => null,
            'frontmatter' => [
                'title'       => '',
                'date'        => date('Y-m-d H:i:s'),
                'author'      => $this->config->get('admin.username', 'admin'),
                'tags'        => [],
                'eyecatch'    => '',
                'description' => '',
                'published'   => true,
            ],
            'body'   => '',
            'action' => '/admin/entries/new',
            'is_new' => true,
        ]));
    }

    private function handleAdminEntryCreate(array $params): void
    {
        $this->auth->requireLogin();
        if (!$this->auth->validateCsrf($_POST['csrf_token'] ?? '')) {
            http_response_code(403);
            echo 'Invalid CSRF token';
            return;
        }

        $category = trim($_POST['category'] ?? '');
        $slug     = $this->buildSlug($_POST['slug'] ?? '', $_POST['title'] ?? '', $_POST['date'] ?? '');
        $fm       = $this->buildFrontmatter($_POST);
        $body     = $_POST['body'] ?? '';

        $this->entryRepo->save($category, $slug, $fm, $body);
        $this->invalidateTagIndex();
        $this->redirectTo('/admin/entries');
    }

    private function renderAdminEntryEdit(array $params): void
    {
        $this->auth->requireLogin();
        $raw = $this->entryRepo->getRaw($params['category'], $params['slug']);
        if ($raw === null) {
            http_response_code(404);
            echo 'Not found';
            return;
        }
        $categories = $this->categoryRepo->findAll();
        $fm         = $raw['frontmatter'];
        echo $this->twig->render('admin/entry_form.html.twig', array_merge($this->baseData(), [
            'categories'       => array_map(fn($c) => $c->toArray(), $categories),
            'frontmatter'      => $fm,
            'body'             => $raw['body'],
            'action'           => '/admin/entries/' . $params['category'] . '/' . $params['slug'] . '/edit',
            'is_new'           => false,
            'current_category' => $params['category'],
            'current_slug'     => $params['slug'],
        ]));
    }

    private function handleAdminEntryUpdate(array $params): void
    {
        $this->auth->requireLogin();
        if (!$this->auth->validateCsrf($_POST['csrf_token'] ?? '')) {
            http_response_code(403);
            echo 'Invalid CSRF token';
            return;
        }

        $oldCategory = $params['category'];
        $oldSlug     = $params['slug'];
        $newCategory = trim($_POST['category'] ?? $oldCategory);
        $newSlug     = trim($_POST['slug'] ?? $oldSlug);
        $fm          = $this->buildFrontmatter($_POST);
        $body        = $_POST['body'] ?? '';

        // カテゴリ/スラッグが変わった場合は旧ファイルを削除
        if ($oldCategory !== $newCategory || $oldSlug !== $newSlug) {
            $this->entryRepo->delete($oldCategory, $oldSlug);
        }
        $this->entryRepo->save($newCategory, $newSlug, $fm, $body);
        $this->invalidateTagIndex();
        $this->redirectTo('/admin/entries');
    }

    private function handleAdminEntryDelete(array $params): void
    {
        $this->auth->requireLogin();
        if (!$this->auth->validateCsrf($_POST['csrf_token'] ?? '')) {
            http_response_code(403);
            echo 'Invalid CSRF token';
            return;
        }
        $this->entryRepo->delete($params['category'], $params['slug']);
        $this->invalidateTagIndex();
        $this->redirectTo('/admin/entries');
    }

    private function handleAdminEntryDuplicate(array $params): void
    {
        $this->auth->requireLogin();
        if (!$this->auth->validateCsrf($_POST['csrf_token'] ?? '')) {
            http_response_code(403);
            echo 'Invalid CSRF token';
            return;
        }
        $raw = $this->entryRepo->getRaw($params['category'], $params['slug']);
        if ($raw === null) {
            $this->redirectTo('/admin/entries');
            return;
        }

        $fm          = $raw['frontmatter'];
        $fm['title'] = ($fm['title'] ?? '') . ' (copy)';
        $newSlug     = date('Y-m-d') . '-copy-' . $params['slug'];
        $this->entryRepo->save($params['category'], $newSlug, $fm, $raw['body']);
        $this->invalidateTagIndex();
        $this->redirectTo('/admin/entries/' . $params['category'] . '/' . $newSlug . '/edit');
    }

    private function handleAdminTogglePublish(array $params): void
    {
        $this->auth->requireLogin();
        if (!$this->auth->validateCsrf($_POST['csrf_token'] ?? '')) {
            http_response_code(403);
            echo 'Invalid CSRF token';
            return;
        }
        $raw = $this->entryRepo->getRaw($params['category'], $params['slug']);
        if ($raw === null) {
            $this->redirectTo('/admin/entries');
            return;
        }

        $fm              = $raw['frontmatter'];
        $current         = isset($fm['published']) ? (bool)$fm['published'] : true;
        $fm['published'] = !$current;
        $this->entryRepo->save($params['category'], $params['slug'], $fm, $raw['body']);
        $this->invalidateTagIndex();

        $referer = $_SERVER['HTTP_REFERER'] ?? '/admin/entries';
        $this->redirectTo($referer);
    }

    private function renderAdminMedia(array $params): void
    {
        $this->auth->requireLogin();

        $mediaDir = $this->basePath . '/public/media';
        $months   = [];

        foreach (glob($mediaDir . '/*/') ?: [] as $monthDir) {
            $month = basename($monthDir);
            $files = [];
            foreach (glob($monthDir . '*.{jpg,jpeg,png,gif,webp,svg}', GLOB_BRACE) ?: [] as $path) {
                $filename = basename($path);
                $files[]  = [
                    'filename' => $filename,
                    'url'      => '/media/' . $month . '/' . $filename,
                    'path'     => 'media/' . $month . '/' . $filename,
                    'size'     => $this->formatBytes(filesize($path)),
                    'mtime'    => filemtime($path),
                ];
            }
            usort($files, fn($a, $b) => $b['mtime'] - $a['mtime']);
            if (!empty($files)) {
                $months[] = ['label' => $month, 'files' => $files];
            }
        }
        usort($months, fn($a, $b) => strcmp($b['label'], $a['label']));

        echo $this->twig->render('admin/media.html.twig', array_merge($this->baseData(), [
            'months'     => $months,
            'csrf_token' => $this->auth->getCsrfToken(),
        ]));
    }

    private function handleAdminMediaDelete(array $params): void
    {
        $this->auth->requireLogin();
        if (!$this->auth->validateCsrf($_POST['csrf_token'] ?? '')) {
            http_response_code(403);
            echo 'Invalid CSRF token';
            return;
        }

        $rel  = ltrim($_POST['path'] ?? '', '/');
        // media/YYYYMM/filename.ext 形式のみ許可
        if (!preg_match('#^media/\d{6}/[\w\-]+\.\w+$#', $rel)) {
            $this->redirectTo('/admin/media');
            return;
        }

        $path = $this->basePath . '/public/' . $rel;
        if (file_exists($path)) {
            unlink($path);
        }

        $this->redirectTo('/admin/media');
    }

    private function formatBytes(int $bytes): string
    {
        if ($bytes < 1024) return $bytes . ' B';
        if ($bytes < 1048576) return round($bytes / 1024, 1) . ' KB';
        return round($bytes / 1048576, 1) . ' MB';
    }

    private function handleAdminImageUpload(array $params): void
    {
        header('Content-Type: application/json');

        if (!$this->auth->isLoggedIn()) {
            http_response_code(403);
            echo json_encode(['error' => 'Unauthorized']);
            return;
        }

        $file = $_FILES['image'] ?? null;
        if ($file === null || $file['error'] !== UPLOAD_ERR_OK) {
            http_response_code(400);
            echo json_encode(['error' => 'アップロードに失敗しました']);
            return;
        }

        // 画像ファイルのみ許可
        $allowed = ['image/jpeg', 'image/png', 'image/gif', 'image/webp', 'image/svg+xml'];
        $mime    = mime_content_type($file['tmp_name']);
        if (!in_array($mime, $allowed, true)) {
            http_response_code(400);
            echo json_encode(['error' => '画像ファイルのみアップロードできます']);
            return;
        }

        $ext      = pathinfo($file['name'], PATHINFO_EXTENSION);
        $subDir   = date('Ym');        // 例: 202603
        $filename = date('His') . '-' . bin2hex(random_bytes(4)) . '.' . strtolower($ext);
        $dir      = $this->basePath . '/public/media/' . $subDir;

        if (!is_dir($dir)) {
            mkdir($dir, 0755, true);
        }

        if (!move_uploaded_file($file['tmp_name'], $dir . '/' . $filename)) {
            http_response_code(500);
            echo json_encode(['error' => '保存に失敗しました']);
            return;
        }

        echo json_encode(['data' => ['filePath' => '/media/' . $subDir . '/' . $filename]]);
    }

    private function buildSlug(string $slug, string $title, string $date): string
    {
        $slug = trim($slug);
        if ($slug !== '') {
            return $slug;
        }
        // タイトルからスラッグ生成
        $slug = mb_strtolower($title);
        $slug = preg_replace('/[^a-z0-9]+/', '-', $slug);
        $slug = trim($slug, '-');
        if ($slug === '' || $slug === '-') {
            $slug = 'entry';
        }
        $datePrefix = date('Y-m-d', strtotime($date) ?: time());
        return $datePrefix . '-' . $slug;
    }

    private function buildFrontmatter(array $post): array
    {
        $tags = array_values(array_filter(array_map('trim', explode(',', $post['tags'] ?? ''))));
        return [
            'title'       => trim($post['title'] ?? ''),
            'date'        => trim($post['date'] ?? date('Y-m-d H:i:s')),
            'author'      => trim($post['author'] ?? ''),
            'category'    => trim($post['category'] ?? ''),
            'tags'        => $tags,
            'eyecatch'    => trim($post['eyecatch'] ?? ''),
            'description' => trim($post['description'] ?? ''),
            'published'   => isset($post['published']) && $post['published'] === '1',
        ];
    }

    private function handleAdminSync(array $params): void
    {
        $this->auth->requireLogin();
        if (!$this->auth->validateCsrf($_POST['csrf_token'] ?? '')) {
            http_response_code(403);
            echo 'Invalid CSRF token';
            return;
        }

        if (!$this->githubSync->isConfigured()) {
            $_SESSION['flash'] = ['type' => 'error', 'message' => 'GitHub の設定がありません（.env を確認してください）'];
            $this->redirectTo('/admin/entries');
            return;
        }

        $result = $this->githubSync->sync();
        $this->invalidateTagIndex();

        $msg = sprintf(
            '同期完了: 追加 %d件 / 更新 %d件 / 削除 %d件',
            $result['added'],
            $result['updated'],
            $result['deleted']
        );
        if (!empty($result['errors'])) {
            $msg .= sprintf(' / エラー %d件', count($result['errors']));
        }

        $_SESSION['flash'] = ['type' => 'success', 'message' => $msg];
        $this->redirectTo('/admin/entries');
    }

    private function invalidateTagIndex(): void
    {
        $marker = $this->basePath . '/var/cache/tags/.last_built';
        if (file_exists($marker)) {
            unlink($marker);
        }
    }

    private function loadEnv(string $path): void
    {
        if (!file_exists($path)) return;
        foreach (file($path, FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES) as $line) {
            if (str_starts_with(trim($line), '#')) continue;
            if (!str_contains($line, '=')) continue;
            [$key, $value] = explode('=', $line, 2);
            $key   = trim($key);
            $value = trim($value);
            if ($key !== '' && !isset($_ENV[$key])) {
                $_ENV[$key] = $value;
            }
        }
    }
}
