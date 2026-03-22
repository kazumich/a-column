<?php

declare(strict_types=1);

namespace AColumn\Repository;

class GitHubSyncRepository
{
    private string $owner;
    private string $repo;
    private string $branch;
    private ?string $token;
    private string $contentsPath;

    public function __construct(private readonly string $basePath)
    {
        $this->owner        = $_ENV['GITHUB_OWNER']  ?? '';
        $this->repo         = $_ENV['GITHUB_REPO']   ?? '';
        $this->branch       = $_ENV['GITHUB_BRANCH'] ?? 'main';
        $this->token        = ($_ENV['GITHUB_TOKEN']  ?? '') ?: null;
        $this->contentsPath = $basePath . '/contents';
    }

    public function isConfigured(): bool
    {
        return $this->owner !== '' && $this->repo !== '';
    }

    /**
     * GitHub リポジトリの内容をローカルの contents/ に同期する。
     *
     * @return array{ added: int, updated: int, deleted: int, errors: string[] }
     */
    public function sync(): array
    {
        $result = ['added' => 0, 'updated' => 0, 'deleted' => 0, 'errors' => []];

        $remoteFiles = $this->fetchRemoteFileList();
        $localFiles  = $this->getLocalFileList();

        // 追加 / 更新
        foreach ($remoteFiles as $path => $remoteSha) {
            $localPath = $this->contentsPath . '/' . $path;
            $localSha  = $localFiles[$path] ?? null;

            if ($localSha === $remoteSha) {
                continue; // 変更なし
            }

            $content = $this->fetchFileContent($path);
            if ($content === null) {
                $result['errors'][] = $path;
                continue;
            }

            $dir = dirname($localPath);
            if (!is_dir($dir)) {
                mkdir($dir, 0755, true);
            }
            file_put_contents($localPath, $content);

            $localSha === null ? $result['added']++ : $result['updated']++;
        }

        // 削除（GitHub にないがローカルにある）
        foreach (array_keys($localFiles) as $path) {
            if (!isset($remoteFiles[$path])) {
                @unlink($this->contentsPath . '/' . $path);
                $result['deleted']++;
            }
        }

        return $result;
    }

    /**
     * ファイルを GitHub リポジトリに push する。
     *
     * @return array{ success: bool, error?: string }
     */
    public function pushFile(string $category, string $filename, string $content, string $commitMessage): array
    {
        if (!$this->isConfigured()) {
            return ['success' => false, 'error' => 'GitHub の設定がありません'];
        }
        if ($this->token === null) {
            return ['success' => false, 'error' => 'GITHUB_TOKEN が設定されていません。.env に GITHUB_TOKEN を追加してください'];
        }

        $path = $category . '/' . $filename;

        // 既存ファイルの SHA を取得（更新の場合に必要）
        $existing = $this->apiGet($path);
        $sha = $existing['sha'] ?? null;

        $body = [
            'message' => $commitMessage,
            'content' => base64_encode($content),
            'branch'  => $this->branch,
        ];
        if ($sha !== null) {
            $body['sha'] = $sha;
        }

        $requestBody = json_encode($body);

        $headers = [
            'User-Agent: a-column-cms',
            'Accept: application/vnd.github+json',
            'Authorization: Bearer ' . $this->token,
            'Content-Type: application/json',
            'Content-Length: ' . strlen($requestBody),
        ];

        $url = sprintf(
            'https://api.github.com/repos/%s/%s/contents/%s',
            $this->owner,
            $this->repo,
            $path
        );

        $context = stream_context_create(['http' => [
            'method'        => 'PUT',
            'header'        => implode("\r\n", $headers),
            'content'       => $requestBody,
            'timeout'       => 30,
            'ignore_errors' => true,
        ]]);

        $response = @file_get_contents($url, false, $context);
        if ($response === false) {
            return ['success' => false, 'error' => 'GitHub API への接続に失敗しました'];
        }

        $data = json_decode($response, true);
        if (isset($data['content'])) {
            return ['success' => true];
        }

        return ['success' => false, 'error' => $data['message'] ?? 'GitHub push に失敗しました'];
    }

    // ----------------------------------------------------------------
    // private
    // ----------------------------------------------------------------

    /**
     * GitHub リポジトリ上の Markdown ファイル一覧を返す。
     * キー: "category/slug.md"  値: GitHub の blob SHA
     *
     * @return array<string, string>
     */
    private function fetchRemoteFileList(): array
    {
        $files = [];

        $root = $this->apiGet('');
        if ($root === null) return $files;

        foreach ($root as $item) {
            if ($item['type'] !== 'dir' || str_starts_with($item['name'], '.')) {
                continue;
            }

            $entries = $this->apiGet($item['name']);
            if ($entries === null) continue;

            foreach ($entries as $entry) {
                if ($entry['type'] !== 'file' || !str_ends_with($entry['name'], '.md')) {
                    continue;
                }
                $files[$item['name'] . '/' . $entry['name']] = $entry['sha'];
            }
        }

        return $files;
    }

    /**
     * ローカルの contents/ 以下の Markdown ファイルを Git blob SHA 付きで返す。
     * キー: "category/slug.md"  値: blob SHA（GitHub と比較可能）
     *
     * @return array<string, string>
     */
    private function getLocalFileList(): array
    {
        $files = [];
        foreach (glob($this->contentsPath . '/*/*.md') ?: [] as $file) {
            $key        = str_replace($this->contentsPath . '/', '', $file);
            $files[$key] = $this->computeBlobSha($file);
        }
        return $files;
    }

    /** GitHub と同じアルゴリズムで blob SHA を計算する */
    private function computeBlobSha(string $filePath): string
    {
        $content = file_get_contents($filePath);
        return sha1('blob ' . strlen($content) . "\0" . $content);
    }

    /** GitHub API からファイルの内容（デコード済み）を取得する */
    private function fetchFileContent(string $path): ?string
    {
        $data = $this->apiGet($path);
        if ($data === null || !isset($data['content'])) {
            return null;
        }
        return base64_decode(str_replace(["\n", ' '], '', $data['content']));
    }

    /**
     * GitHub Contents API を叩く。
     *
     * @return array<mixed>|null
     */
    private function apiGet(string $path): ?array
    {
        $urlPath = $path === '' ? '' : '/' . ltrim($path, '/');
        $url     = sprintf(
            'https://api.github.com/repos/%s/%s/contents%s?ref=%s',
            $this->owner,
            $this->repo,
            $urlPath,
            $this->branch
        );

        $headers = [
            'User-Agent: a-column-cms',
            'Accept: application/vnd.github+json',
        ];
        if ($this->token !== null) {
            $headers[] = 'Authorization: Bearer ' . $this->token;
        }

        $context  = stream_context_create(['http' => [
            'method'  => 'GET',
            'header'  => implode("\r\n", $headers),
            'timeout' => 15,
            'ignore_errors' => true,
        ]]);
        $response = @file_get_contents($url, false, $context);

        if ($response === false) return null;

        $data = json_decode($response, true);
        return is_array($data) ? $data : null;
    }
}
