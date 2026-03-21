<?php

declare(strict_types=1);

namespace AColumn\Core;

use AColumn\Repository\EntryRepository;
use AColumn\Repository\CategoryRepository;
use AColumn\Repository\TagIndexRepository;
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
    private int $excerptLength;

    public function __construct(private readonly string $basePath)
    {
        date_default_timezone_set('Asia/Tokyo');

        $this->config = new Config();
        $this->config->load($basePath . '/config/site.yaml');
        $this->config->load($basePath . '/config/categories.yaml');

        $tz = $this->config->get('site.timezone', 'Asia/Tokyo');
        date_default_timezone_set($tz);

        $this->request      = new Request();
        $this->router       = new Router();
        $this->entryRepo    = new EntryRepository($basePath . '/contents', $this->config);
        $this->categoryRepo = new CategoryRepository($this->config);
        $this->tagIndex     = new TagIndexRepository($basePath, $this->config);

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
}
