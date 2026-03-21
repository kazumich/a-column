
# ---( 通常設定の修正はここから )----------------------

#■このCGIの名前
$cgi_name = "a-column.cgi";

#■Perlのソースの変更 
# 0: なし
# 1: あり (a-news.cgiを改造した場合は1にしてください)
$kaizo = 0;

#■パスワードの設定(注意：必ず変更してください。)
$passwd = "pass";

#■時差の修正 (海外のサーバでも日本の時間になります)
$ENV{'TZ'} = "JST-9";

#■パスワードの暗号化
# 0: しない
# 1: する(crypt.cgiを利用して暗号化して下さい)
$crypt_sw = 0;

#■a-Columnで作成したファイルかどうかをチェック
# 0 : チェックしない
# 1 : チェックする
$generator_check = 1;

# □ 上記でチェックする場合に更新できない場合に表示する文字
$notedit_msg = " <b>【更新不可】</b>";

$columnStartTag = "<!--columnStart-->";
$columnEndTag = "<!--columnEnd-->";

$updateStartTag = "<!--updateStart-->";
$updateEndTag = "<!--updateEnd-->";

$logoff_btn = "LOGOFF";

# ------------------------------------- ( ファイルの関連設定 ) ------

#■ データディレクトリまでのURL (写真へのリンクをする際に利用)
$url = "/oldSystem/a-column/column";

#■ 写真を保存するディレクトリ名
$photo_dir = "images";

#■index.htmlの出力
# 0: しない (CGIで全て表示する)
# 1: する　 (トップページのみHTML化する)

$publish_sw = 1;

#□ 出力するHTMLファイル(上記が1の場合に利用)
$index_file = "index.html";

# ジャンル毎の一覧を作る際の名前を設定（v1.60で追加）
$genre_index = "index.html";

# ジャンル毎の最新HTMLの別名を設定（v1.60で追加）
$new_html = "new.html";

#■読み込むテンプレートファイル（注：画像は絶対パスで記述してください）
$template_file = "index.html";		# 一覧のテンプレート
$template_file2 = "templateColmun.htm";		# 本文のテンプレート
$template_file3 = "templateColindex.htm";		# ジャンル一覧用のテンプレート

#■CGIサーバが別の場合に設定してください。
$cgi_server = "."; # a-column.cgi のあるディレクトリまでを指定してください。
$www_server = "."; # データファイルのあるURLの手前までを指定してください。

#■データファイルのパス 
$site_path = "column"; 
#$site_path = "."; # 同一ディレクトリの場合には . だけ書いてください。



#更新日付の管理ファイル (v1.60より設定ファイルに移動）
$upinfo_file = "upinfo.dat";

#インデックスファイル（v.160より設定ファイルに移動）
$dataFile = "list.cgi"; # デフォルトのファイル名を変更しました。（v1.60）

# ------------------------------------- ( ジャンルの関連設定 ) ------

#ジャンルのディレクトリ設定（ジャンル分けをしない場合1つだけ設定してください）
@GENRE = ('secret','soft','hard','net');
#@GENRE = ('column');

#ジャンルの日本語設定
%GENRE_TABLE = (
'secret','非公開',
'soft','ソフトウェアについて',
'hard','ハードウェアについて',
'net','インターネットについて'
);

#非公開ジャンルの設定（デフォルトのままの名前では非公開の意味がありません）
$secret = "secret";

#そのジャンルに1件もデータが無い場合のタイトルの表示（v1.42で追加）
# 0: タイトル表示
# 1: タイトル非表示
$title_zero = 1;

# ------------------------------------- ( 一覧表示の関連設定 ) ------

#表示件数を制限
# 0: 制限しない
# 1～ : その件数まで表示
$list_max = 3;

#件数を制限した時に表示される文字列
$genre_all = "more ...";

# 改ページ機能
# 0: オフ （一覧のHTMLにリンク/ more... 表示）
# 1: オン （CGIを利用した表示で改ページされます）
$kaiPage = 1;

#ソート順の設定
# 0: タイムスタンプ順に表示（降順）
# 1: タイムスタンプ順に表示（昇順）
# 2: タイトル順に表示（昇順）（v1.51で追加）
# 3: ファイル名順に表示（昇順）（v1.51で追加）
$sort_jun = 0;

#一覧のジャンルタイトル部分のタグ（v1.50で追加）
$list_title_tag = "h3";

#$genreBox_tag = '';
#$genreTitle_tag = '<h3 class="genreTitle">';
#$genreTitle_tag_end = '</h3>';
#$top_tag = '<table border=1>';
#$listTag = '<tr><td><a href="{url}">{title}</a></td><td>{date}</td></tr>'."\n";
#$foot_tag = '</table>';
#$genreBox_tag_end = '';

#<UL>でレイアウトする場合

$genreBox_tag = '<div class="genreBox">';
$genreTitle_tag = '<h3 class="genreTitle">';
$genreTitle_tag_end = '</h3>';
$top_tag = '<ul>';
$listTag = '<li class="columnTitle"><a href="{url}">{title}</a>　<span class="columnDate">[<a href="{url}">{date}</a>]</span></li>'."\n";
$foot_tag = '</ul>';
$genreBox_tag_end = '</div>';

$moreTag = '<li class="columnTitle"><a href="{url}">{title}</a></li>'."\n";

# 改ページ機能用のリンク（v2.3で追加）
$nextPrevBox = '<p class="columnNavi">{prev} {next}</p>';
$prevLink = '[<a href="{prevLink}">前へ</a>]';
$nextLink = '[<a href="{nextLink}">次へ</a>]';


#■一覧で日付を表示
# 0: しない
# 1: する
# $list_day = 1; 
# 使わなくなりました。 
#
#  $listTag 上の {date} を削除してください。

#■パスワードの入力エリア
# 0:下
# 1:上
# 2:非表示
$pass_ichi = 0;

# ------------------------------------- ( その他の設定 ) ------

#タイトル行のタグ
$title_tag = "h3";

#タイトル行の挿入位置
# 0 : <!--from-->の後	（v1.0.x互換）デフォルト
# 1 : <!--title_include-->
$title_ichi = 1;

#■ 追加／更新／削除ボタンの位置
# 0 : 下
# 1 : 上
$aud_btn = 1;
 
#■入力フォームの位置を設定
# 0:下
# 1:上
$form_ichi = 1;
 
#■項目追加をどちらの方向にするかを設定
# 0:下
# 1:上
# 2:どちらも可
$add_ichi = 2;

#■追加時のボタン名称
$add_btn0 = "　下追加　";
$add_btn1 = "　上追加　";

#■ ボタン名の表示
$list_btn = "一覧";
$add_btn = "追加";
$update_btn = "更新";
$delete_btn = "削除";
$new_btn = "コラム新規追加";
$publish_btn = "index.htmlの生成";

#$list_btn = "List";
#$add_btn = "Add";
#$update_btn = "Update";
#$delete_btn = "Delete";
#$new_btn = "New Column";
#$publish_btn = "index Publish";


#■入力フォームのサイズ
#(<textarea></textarea>のサイズになります。)
$rows = 6;		# (長文を書く場合には大きめの数値にしておくといいかも)
$cols = 60;		# <textarea cols=??>
$cols2 = 50;	# <input size=??>(MacのIEだと10少ないくらいがちょうどいい)


#■改行モード 
# 0: off (改行を無視します)
# 1: on　(改行すると<BR>タグに置き換えるようになります)
$cr_sw = 1; 


#更新フォーム表示時の自動日付更新
# 0: off (v1.51までのデフォルト）
# 1: on (v1.60からのデフォルト)
$updatecheck= 1;

#■日時の表示設定 
# 0: YYYY/MM/DD HH:MM
# 1: YYYY/MM/DD
# 2: MM/DD
# 3: MM/DD HH:MM
# $datetime_sw = 1; 
# 
# 下の方にある $dateFormat をご利用下さい。

# 画像の横幅の最大サイズ設定（v1,50で追加）
$max_img_width = 300;

# center時の画像の横幅の最大サイズ設定（v.161で追加）
$max_img_width_center = 500;

# 管理者モードへのログインボタン表示（v1.50で追加）
# 未記入でボタン非表示 (v1.43までの状態)
# 記入するとボタン表示
$login_btn = "admin";

#更新時刻の表示 
# hidden: 非表示（デフォルト）（v1.62で追加）
# text : 表示
$updateTimeType = "hidden";

# サーバに imagemagick がインストールされている場合の
# convertファイルのパスを設定 
$imagemagick = "/usr/local/bin/convert";

#■年月日のフォーマットを設定
#
#YYYY 年。4桁数字
#YY 年。2桁数字
#
#MM 月。数字。先頭にゼロをつける。
#MON 月。3文字形式。
#Mn 月。数字。先頭にゼロをつけない。
#MONTH 月。フルスペルの文字。
#
#DD 日。二桁の数字（先頭にゼロがつく場合も）
#Dn 日。先頭にゼロをつけない。
#
#W3 曜日。3文字のテキスト形式。
#WF 曜日。フルスペル形式。
#YOBI 曜日。日本語で1文字

#JJ 時。2桁
#FF	分。2桁
#BB 秒。2桁

#$dateFormat = "YYYY.MM.DD (W3)";
#$dateFormat = "YYYY/Mn/Dn (W3)";
#$dateFormat = " MONTH Dn , YYYY [ WF ]";
$dateFormat = "YYYY年MM月DD日 (YOBI) JJ:FF";

#$dateFormat = "YYYY/MM/DD (YOBI) JJ:FF";

# ------------------------------------------ v2.x でも未サポート ------
#著者のデフォルト設定 
@WRITER = ('なまえ1','なまえ2','なまえ3');
#@WRITER = ""; # 利用しない場合
#一覧に著者情報表示
$list_author = 0;
# 入力フォームに表示
$input_author = 0;

# ---( 通常設定の修正はここまで )----------------------

1;
