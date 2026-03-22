<?php

declare(strict_types=1);

define('BASE_PATH', dirname(__DIR__));

require BASE_PATH . '/vendor/autoload.php';

session_start();

$app = new AColumn\Core\Application(BASE_PATH);
$app->run();
