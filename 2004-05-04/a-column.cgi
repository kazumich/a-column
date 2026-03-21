#!/usr/local/bin/perl

#======================================================
# a-Column v2.31 (2004/05/04)
#------------------------------------------------------
# HomePage : http://www.appleple.com/
# E-Mail   : Kazumich@appleple.com
#======================================================

$version = "2.31";
$site_url= "http://www.appleple.com/";
$email = 'kazumich@appleple.com';

require './cgi-lib.pl';
require './GetPicSize.pl';
require './setupColumn.cgi';

$meta_generator = "<meta name=\"generator\" content=\"a-Column\">";
$method = "POST";
$err_sw = 0;

if ($updateTimeType eq "hidden") {
	$dateTimeText = "日付";
} else {
	$dateTimeText = "日時";
}

#レイアウト用のテーブルサイズ
$x_table = "90%";

$now_time = time;
$genre_kensu = @GENRE;
$writer_kensu =@WRITER;
$check_length = $cols * $rows;

($sec,$min,$hour,$mday,$mon,$year,$wday,$yday,$isdst) = localtime(time);
$now_year = sprintf("%04d",$year + 1900);
$now_month = sprintf("%02d",$mon + 1);
$now_day = sprintf("%02d",$mday);
$now_hour = sprintf("%02d",$hour);
$now_min = sprintf("%02d",$min);
$now_sec = sprintf("%02d",$sec);

#---------------------------------------------------------------

#バッファ展開処理

&ReadParse();

# アップロードファイルの種類をチェック
&upfile_check;

# COOKIEの取得

$i=0;
if ($ENV{'HTTP_COOKIE'}) {
  @cookie = split(/;/, $ENV{'HTTP_COOKIE'});
  foreach (@cookie) {
	$_  =~ s/ //g;
	$_  =~ s/\n//g;
    ($key, $val) = split(/=/);
    $COOKIE{$key} = $val;
	if ($key eq "a-Site") {
		$passCookieFlag = 1;
		$passCookieData = $val;
	}
  }
} 

# パスワードチェック
$admin_ok = &pass_check($in{'pass'});

#----- テンプレート表示前振分処理 -----

if ($admin_ok eq 1) {
	if ($in{'action'} eq "regist") { &regist; }
	elsif ($in{'action'} eq "update2") { &update; }
	elsif ($in{'action'} eq "add2") { &add; }
	elsif ($in{'action'} eq $delete_btn) { &delete; $in{'file'} = "";}
	elsif ($in{'action'} eq $list_btn) { $in{'file'} = ""; $in{'genre'} = "";}
	elsif ($in{'action'} eq "publish" ) {
		foreach (@GENRE) {
			&fileCheck($_);
		}
	} elsif ($in{'action'} eq "rebuild" ) {
		&rebuildCheck;
	} elsif ($in{'action'} eq "rebuildGo" ) {
		&rebuildCheck;
	}}
#----- テンプレートファイル読み込み -----

if ($in{'action'} eq "new") {
	$read_temp = $template_file2;
} elsif ($in{'action'} eq $update_btn || $in{'action'} eq $add_btn || $in{'file'} ne "") {
	$checkFile = "$site_path/$in{'genre'}/$template_file2";
	if (-e $checkFile) {
		$read_temp = $checkFile;
	} else {
		$read_temp = $template_file2;
	}
} else {
	$read_temp = $template_file;
}

open(TEMPFILE, $read_temp) || &error("ファイル読込エラー<br>[$read_temp]","テンプレートファイルが開けません。");
@TEMPLATE = <TEMPFILE>;
close(TEMPFILE);

if ($in{'action'} eq "publish") { $admin_ok = 0; }

#---- 画面表示 ------

$err_sw = 1;
$pushFlag=1;

if (!($setCookie)){
	print "Content-type: text/html\n\n";
}

foreach $line (@TEMPLATE) {

	if ($genreTitlePrint eq 1) {
		$line =~ s/<!--genreTitle-->/$GENRE_TABLE{$in{genre}}/ig;
	}

	if ($line =~ /$columnStartTag/i) {
		$pushFlag=0;
		push(@OUTHTML,$`);
		push(@OUTHTML,"$columnStartTag\n");
		
		if ($in{'action'} eq $update_btn) { 
			&update_form;
		} elsif ($in{'action'} eq "new") { 
			&regist_form;
		} elsif ($in{'file'} eq "") {
			$main_sw = 1;
			&list_shori; 
		}
		
	} elsif ($line =~ /$columnEndTag/i){

		push(@OUTHTML,"\n$columnEndTag");
		push(@OUTHTML,$');
		$pushFlag=1;
		next;
		
	} elsif  ($line =~ /$updateStartTag/i)  {

		push(@OUTHTML,$`);
		push(@OUTHTML,"$updateStartTag \n");
		$printDate = &updatetime_print;
		push(@OUTHTML,"$printDate\n");
		$pushFlag=0;
		
	} elsif  ($line =~ /$updateEndTag/i)  {

		push(@OUTHTML,$updateEndTag);
		push(@OUTHTML,$');
		$pushFlag=1;
		next;
		
	} elsif ($pushFlag eq 1){
		if ($line =~ /<!--from-->/i) {
			$ato_print = $'; 
			push(@OUTHTML,$`);
			if ($in{'action'} eq $update_btn) { 
				&update_form; 
			} elsif ($in{'action'} eq "new") { 
				&regist_form; 
			} else { 
				&detail_shori; 
			}
			push(@OUTHTML,$ato_print);
			
		} elsif ($line =~ /<!--link_include-->/i) {
			&pass_link; 
		} else {
			push(@OUTHTML,$line);
		}
	}
}

# index publish処理
if ($in{'action'} eq "publish") {
	open (OUT,">$index_file");
	foreach $line (@OUTHTML) {
		print OUT $line;
	}
	close(OUT);
}

# 画面表示処理
foreach $data (@OUTHTML) {
	$data =~ s/<!--title_include-->/$titleName/g;
	print "$data";
}

exit;

#----- ジャンル毎の一覧データ読み込み -----

sub file_read2 {

		$inputList = "$site_path/$genre_data/$dataFile";
		open(DATA, $inputList); 
		@files2 = <DATA>;
		close(DATA);
		$kensu = @files2;
		
		if ($sort_jun eq 1) {
			#タイムスタンプの古い順にソート
			@files2 = reverse sort { $b cmp $a} @files2;
		} elsif ($sort_jun eq 2) {
			#タイトル順にソート
			@files2 = sort { (split(/;;/,$a))[2] cmp (split(/;;/,$b))[2] } @files2;
		} elsif ($sort_jun eq 3) {
			#ファイル名順にソート
			@files2 = sort { (split(/;;/,$a))[1] cmp (split(/;;/,$b))[1] } @files2;
		} else {
			#タイムスタンプの新しい順にソート
			@files2 = sort { $b cmp $a} @files2;
		}
}

#----- 一覧表示処理 -----

sub list_shori {

	if ($pass_ichi eq 1) {
		if ($admin_ok eq 1) {
			$msg = "<div class=\"passBox\">\n<form action=\"$cgi_server$cgi_name\" method=\"$method\">
				<input type=\"hidden\" name=\"pass\" value=\"$pass xxx\"><input type=\"submit\" value=\"$logoff_btn\" class=\"fButton\"></form>\n</div>";
			push(@OUTHTML,$msg);
		} else {
			$msg = "<div class=\"passBox\">\n<form action=\"$cgi_server/$cgi_name\" method=\"$method\">
				<input type=\"password\" name=\"pass\" size=\"8\">";
			push(@OUTHTML,$msg);
			if($login_btn) {
				$msg = "<input type=submit value=\"$login_btn\" class=\"fButton\">";
				push(@OUTHTML,$msg);
			}
			$msg = "</form></div>";
			push(@OUTHTML,$msg);
		}
	}

	if ($admin_ok eq 1) {
		$msg = "<table align=\"center\"><tr><td><form action=\"$cgi_name\" method=\"$method\">
			<input type=\"hidden\" name=\"action\" value=\"new\">
			<input type=\"submit\" value=\"　 $new_btn 　\" class=\"fButton\">
			</form></td>";
		push(@OUTHTML,$msg);

		if ($publish_sw ne 0) {
			$msg = "<td><form action=\"$cgi_name\" method=\"$method\">
				<input type=\"hidden\" name=\"action\" value=\"publish\">
				<input type=\"submit\" value=\"　 $publish_btn 　\" class=\"fButton\">
				</form></td>";
			push(@OUTHTML,$msg);
		}
		
		$msg = "</tr></table><hr>";
		push(@OUTHTML,$msg);
	} else {
		if ($in{'pass'} ne "" && $in{'action'} ne "publish") {
			if ($in{'pass'} ne "LOGOFF") {
				$msg = "<h3 align=center>パスワード入力エラー</h3>";
				push(@OUTHTML,$msg);
			} 
		}
	}

	if ($in{'action'} eq "rebuildGo") {

			$msg = "<div><p>$convertFile件の変換を終了しました。</p>";
			push(@OUTHTML,$msg);

			if ($noConvertFile) {

			$msg = "<div><p>以下の$noConvertFile件はa-Columnで生成されていないHTMLの為に変換することができませんでした。手動で対応してください。</p>";
			push(@OUTHTML,$msg);

				push(@OUTHTML,$top_tag);
				foreach $line (@noConvert) {
					$msg = $list_tag1 . $line . $notedit_msg ;
					push(@OUTHTML,$msg);
				}
				push(@OUTHTML,$foot_tag);
			}
			push(@OUTHTML,"</div>");
			
	} else {

		if ($convertFile) {
			$btnMsg = "再作成HTMLデータ数: $convertFile件 変換！\n";
			$msg = "<div><p>必ず、FTP等でデータディレクトリ毎ダウンロードし、バックアップしてからご利用ください。</p><form action=\"$cgi_name\" method=\"$method\">
					<input type=\"hidden\" name=\"action\" value=\"rebuildGo\">
					<input type=\"submit\" value=\"　 $btnMsg 　\" class=\"fButton\" onClick=\"return confirm('実行してもよろしいですか?')\">
					</form>";
			push(@OUTHTML,$msg);
			if ($noConvertFile) {
				$msg = "<p>a-Columnで生成されていないHTMLが$noConvertFile件あります。</p>";
				push(@OUTHTML,$msg);
				push(@OUTHTML,$top_tag);
				foreach $line (@noConvert) {
					$msg = $list_tag1 . $line . $notedit_msg ;
					push(@OUTHTML,$msg);
				}
				push(@OUTHTML,$foot_tag);
			}
			push(@OUTHTML,"</div>");
		}

	}

	# ----- 日毎のループ処理 ココから -----

	if ($GENRE_TABLE{$in{'genre'}} eq "") {
		@PRINT_GENRE = @GENRE;
	} else {
		@PRINT_GENRE = $in{'genre'};
	}
	
	foreach $genre_data (@PRINT_GENRE) {
	
		if ($admin_ok eq 0 && $genre_data eq $secret) {
			next;
		}

		&file_read2;

		if ($title_zero eq 1) {
			$file_count = @files2;
		} else {
			$file_count = 1;
		}
		if($file_count ne 0) {

			$msg = $genreBox_tag . $genreTitle_tag;
			push(@OUTHTML,$msg);
			
			if ($GENRE_TABLE{$genre_data} ne "") {
				$title_image = "$site_path/$photo_dir/$genre_data.gif";
				if (-e $title_image) {
					my ($format,$width, $height) = &GetImageSize($title_image);
					$msg = "<img src=\"$url/$photo_dir/$genre_data.gif\" width=\"$width\" height=\"$height\" alt=\"$GENRE_TABLE{$genre_data}\">";
				} else {
					$msg = "$GENRE_TABLE{$genre_data}";
				}
				push(@OUTHTML,$msg);
			}
			
			$msg = $genreTitle_tag_end . $top_tag;
			push(@OUTHTML,$msg);

		}
		
		$max_count = 0;
		$more_sw = 0;
		
		if ($list_max ne 0 && $in{'max'} ne "all") {
			$in{'max'} = $list_max;
		}
		
		if ($kaiPage) {
		
			if ($in{'nextG'} ne $genre_data) {
				$nextP = 0;
			} else {
				$nextP = $in{'nextP'};
			}
			
			$i = 0;
			$nextBtn = 0;
			$j = $nextP + $list_max;
			$k = $nextP - $list_max;
		}
		
		foreach (@files2) {

			if ($kaiPage) {

				$i++;
				if ($i - 1< $nextP) {
					next;
				} elsif ($i > $j) {
					$nextBtn = 1;
					last;
				}
			
			} else {
			
				if ($in{'max'} eq "all") {
					# no check
				} else {
					if ($in{'max'} > 0) {
						if ($in{'max'} <= $max_count) { $more_sw = 1; last; } else { $max_count++; }
					}
				}
				
			}
			
			chomp $_;
			($meta_time,$data_file,$title_data,$update_ng) = split(/\;;/,$_);
		
			$data_path = $data_file;
			$data_path =~ s/\.\./*/g;
			
			if ($generator_check eq 1) {		
				if ($admin_ok eq 1) {
					if ($update_ng eq 1) {
						$notedit  = "";
						$cgi_link = "$cgi_server/$cgi_name?genre=$genre_data&amp;file=";
					} else {
						$notedit = $notedit_msg;
						$cgi_link = "";
					}
				}
			} else {
				if ($admin_ok eq 1) {
					$cgi_link = "$cgi_server/$cgi_name?genre=$genre_data&amp;file="; 
				}
			}
			
			$cgi_link2 = $cgi_link;
			if ($cgi_link eq "") {
				if ($www_server ne ".") {
					$cgi_link2 = $www_server . "/" . $genre_data . "/";
				} else {
					$cgi_link2 = "$site_path/$genre_data/";
				}
			}
						
			$update_date = &date_time_print($meta_time);
			$printData = $listTag;
			
			$printData =~ s/{title}/$title_data/g;
			$printData =~ s/{url}/$cgi_link2$data_path/g;
			$printData =~ s/{date}/$update_date/g;
			
			push(@OUTHTML,$printData);
		}
		# ----- HTMLファイルリスト分をループ ----- ( ここまで ) -----

		if ($kaiPage) {

			if($file_count ne 0) {
				push(@OUTHTML,$foot_tag);
			}
			
			$prevLinkData = $prevLink;
			$nextLinkData = $nextLink;
			$nextPrevBoxData = $nextPrevBox;
			
			if ($nextP) { 
				$prevLinkURL = "$cgi_server/$cgi_name?nextP=$k&nextG=$genre_data";
				$prevLinkData = $prevLink;
				$prevLinkData =~ s/{prevLink}/$prevLinkURL/g;
			} else {
				$prevLinkData = "";
			}
			
			if ($nextBtn) { 
				$nextLinkURL = "$cgi_server/$cgi_name?nextP=$j&nextG=$genre_data";
				$nextLinkData = $nextLink;
				$nextLinkData =~ s/{nextLink}/$nextLinkURL/g;
			} else {
				$nextLinkData = "";
			}
			
			$nextPrevBoxData =~ s/{prev}/$prevLinkData/g;
			$nextPrevBoxData =~ s/{next}/$nextLinkData/g;
			push(@OUTHTML, $nextPrevBoxData);
			
			push(@OUTHTML, $genreBox_tag_end);
			
		} else {
	
			if($file_count ne 0) {
				push(@OUTHTML,$foot_tag);
				
				if ($more_sw eq 1) {
					if ($admin_ok eq 1) {
		
						$urlData = "$cgi_server/$cgi_name?genre=$genre_data&amp;max=all"; 
						$msg = $top_tag . $moreTag .$foot_tag;
						$msg =~ s/{title}/$genre_all/g;
						$msg =~ s/{url}/$urlData/g;
						
					} else {
	
						if ($www_server ne ".") {
							$cgi_link2 = $www_server . "/" . $genre_data;
						} else {
							$cgi_link2 = "$site_path/$genre_data";
						}
						$urlData = "$cgi_link2/$genre_index";
						$msg = $top_tag . $moreTag .$foot_tag;
						$msg =~ s/{title}/$genre_all/g;
						$msg =~ s/{url}/$urlData/g;
						
					}
					push(@OUTHTML,$msg);
				}
				push(@OUTHTML, $genreBox_tag_end);
			}
		}

	}

	if ($main_sw eq 1) {
		&pass_link;
	}
	
}

sub pass_link {

	# フッタ部表示
	
	if ($pass_ichi eq 0) {
		if ($admin_ok eq 1) {
			$msg = "<div class=\"passBox\">\n<form action=\"$cgi_server/$cgi_name\" method=\"$method\">
				<input type=\"hidden\" name=\"pass\" value=\"LOGOFF\"><input type=\"submit\" value=\"$logoff_btn\" class=\"fButton\"></form>\n</div>";
		} else {
			push(@OUTHTML,"<div class=\"passBox\">");
			$msg = "<form action=\"$cgi_server/$cgi_name\" method=\"$method\">
			<input type=\"hidden\" name=\"max\" value=\"$in{'max'}\">
			<input type=\"password\" name=\"pass\" size=\"8\">";
			push(@OUTHTML,$msg);
			if($login_btn) {
				$msg = "<input type=\"submit\" value=\"$login_btn\" class=\"fButton\">";
				push(@OUTHTML,$msg);
			}
			$msg ="</form></div>";
		}
		push(@OUTHTML,$msg);
	}
	
	if ($kaizo eq 1) {
		$kaizo = "+";
	} else {
		$kaizo = "";
	}
	# 著作権表示（以下の2行は削除不可です）
	$msg = "<p class=\"cgiName\"><a href=\"$site_url\" target=\"_blank\">a-Column $version$kaizo</a></p>";
	push(@OUTHTML,$msg);

}

#----- 詳細モード -----

sub detail_shori {

	$update_file = "$site_path/$in{'genre'}/$in{'file'}";
	if (!open(IN,"$update_file")) { &error("データ読取エラー <br>[$update_file]","設定ファイルの設定が間違っている可能性があります。"); }
	@column = <IN>;
	close(IN);

	$now_genre = $in{'genre'} ;

		if ($admin_ok eq 1) {
			if ($form_ichi eq 1) {
				if ($in{'action'} eq $add_btn) { &add_form; }
			}
		}

		if ($admin_ok eq 1 && $aud_btn eq 1) {
			$msg = "<hr><form action=$cgi_name method=$method>
			<input type=hidden name=pass value=\"$in{'pass'}\">
			<!-- <input type=hidden name=time value=\"$in{'time'}\"> -->
			<table width=\"100%\"><tr><td>
			<input type=hidden name=genre value=\"$in{'genre'}\">　
			<input type=submit name=action value=\"$list_btn\" class=\"fButton\">　
			<input type=submit name=action value=\"$add_btn\" class=\"fButton\">　
			<input type=submit name=action value=\"$update_btn\" class=\"fButton\">　 $GENRE_TABLE{$now_genre} 
			</td><td align=right>
			<input type=submit name=action value=\"$delete_btn\" onClick=\"return confirm('削除してもよろしいですか?')\" class=\"fButton\">
			<input type=hidden name=file value=\"$in{'file'}\">
			</td></tr></table></form><hr>\n";
			push(@OUTHTML,$msg);
		}
		
		$print_sw = 0;

		foreach $line (@column) {
			
			if ($print_sw eq 0) {
				if ($line =~ /<title>(.*)<\/title>/i) {
					$title = $1;
					$titleName = $1
				}
			}
			if ($admin_ok eq 1) {
				if ($line =~ /<!--from-->/i) {
#					if ($title_ichi eq 1) { push(@OUTHTML,"<$title_tag>$title</$title_tag>"); }
					$print_sw = 1; next;
				} elsif ($line =~ /<!--to-->/i) {
					$print_sw = 2;
				}
				if ($print_sw eq 1) {
					if ($title_ichi eq 1) { 
#						if ($line =~ /class=title/i) { next; }
					}
					push(@OUTHTML,$line);
				}
			}

			# Update日時を取得
			if ($line =~ /<meta name=\"update-time\" content=\"(.*)\">/i ) {
				$meta_time = $1; 
				$update_date = &date_time_print($meta_time);
			} 
			
		}

		if ($admin_ok eq 1 && $aud_btn ne 1) {
			$msg = "<hr><form action=$cgi_name method=$method>
			<input type=hidden name=pass value=\"$in{'pass'}\">
			<table width=\"100%\"><tr><td>
			<input type=submit name=action value=\"$list_btn\" class=\"fButton\">　
			<input type=submit name=action value=\"$add_btn\" class=\"fButton\">　
			<input type=submit name=action value=\"$update_btn\" class=\"fButton\">　 $GENRE_TABLE{$now_genre} 
			</td><td align=right>
			<input type=submit name=action value=\"$delete_btn\" onClick=\"return confirm('削除してもよろしいですか?')\" class=\"fButton\">
			<input type=hidden name=file value=\"$in{'file'}\">
			</td></tr></table></form><hr>\n";
			push(@OUTHTML,$msg);
		}

		if ($admin_ok eq 1) {
			if ($in{'action'} eq $add_btn) { 
				if ($form_ichi eq 1) {
					last;
				} else {
					&add_form; last; 
				}
			}
		}

#	}
	
	#push(@OUTHTML,"<p>$author</p>");

}

sub regist_form {

	&tag_editor;
 
	$msg = "<form name=\"form1\" action=$cgi_name method=$method ENCTYPE=\"multipart/form-data\">
	<table border=\"0\" cellspacing=\"0\" cellpadding=\"5\" align=\"center\" class=\"formTable\">";
	push(@OUTHTML,$msg);

	if ($genre_kensu ne 1) {
		$msg = "<tr><td align=right valign=top nowrap>ジャンル</td><td><select name=\"genre\" class=\"fSelect\">";
		push(@OUTHTML,$msg);
	
		foreach $line (@GENRE) {
			push(@OUTHTML,"<option value=$line>$GENRE_TABLE{$line}</option>");
		}
	
		$msg = "</select></td></tr>";
		push(@OUTHTML,$msg);
	} else {
		$msg = "<input type=hidden name=genre value=$GENRE[0]>";
		push(@OUTHTML,$msg);
	}

	$msg = "<tr><td align=right valign=top nowrap>タイトル</td>
			<td><input type=\"text\" name=\"title\" size=\"$cols2\" class=\"fInput\"></td>
		</tr>";
	push(@OUTHTML,$msg);

	if ($input_author eq 1) {
		$msg = "<tr><td align=right valign=top nowrap>著者</td>
					<td><select name=\"writer1\" class=\"fSelect\"><option value=\"\" selected>　</option>";
		push(@OUTHTML,$msg);
		
		foreach $line (@WRITER) {
			push(@OUTHTML,"<option>$line</option>");
		}
		
		$msg = "</select> <input type=\"text\" name=\"writer2\" size=\"20\" class=\"fInput\"></td></tr>";
		push(@OUTHTML,$msg);
	}

	$msg = "<tr><td align=right valign=top nowrap>内容</td>
			<td><textarea name=\"column\" cols=\"$cols\" rows=\"$rows\" class=\"fInput\"></textarea></td>
		</tr>
		<tr><td align=right valign=top nowrap>ファイル名</td>
			<td><input type=\"text\" name=\"filename\" size=\"20\" value=\"$now_time\" class=\"fInput\">.html</td>
		</tr>
		<tr><td align=right valign=top nowrap>改行</td>
		<td><input type=checkbox name=\"kaigyo\" value=\"off\">無効（HTMLをペーストする際にはチェック！）</td>
		</tr>
		<tr><td align=right valign=top nowrap>写真</td>
			<td> <input type=\"file\" name=\"attachment\" size=\"20\" class=\"fFile\"> 
			<select name=\"align\" class=\"fSelect\"><option value=left>写真を左寄せ<option value=top>写真を上に<option value=bottom>写真を下に<option value=right>写真を右寄せ</select></td>
			</tr>
	</table>
	<input type=hidden name=action value=\"regist\">
	<input type=hidden name=pass value=\"$in{'pass'}\">
	<p>
	<input type=submit value=\" 登　録 \" class=\"fButton\">　<input type=reset value=\" リセット \" class=\"fButton\">
	</form>
	<hr size=4 width=\"80%\">
	要望・バグ情報・感想等　<a href=\"mailto:$email\">メール</a>をお待ちしております。
	<hr size=4 width=\"80%\">
	</td></tr></table>";

	push(@OUTHTML,$msg);

}

sub update_form {
	
	$update_file = "$site_path/$in{'genre'}/$in{'file'}";

	if (!open(IN,"$update_file")) { &error("データ読取エラー<br>[$update_file]","設定ファイルの設定が間違っている可能性があります。"); }
	@column = <IN>;
	close(IN);

	$now_genre = $in{'genre'} ;
	$print_sw = 0;

	foreach $line (@column) {
			
		if ($line =~ /<!--from-->/i) {
			$print_sw = 1;
		} elsif ($line =~ /<!--to-->/i) {
			$print_sw = 2;
		}

		if ($print_sw eq 0) {

			#更新日時を取得
			if ($line =~ /<meta name=\"update-time\" content=\"(.*)\">/i ) { $meta_time = $1; }
			#タイトルを取得
			if ($line =~ /<title>(.*)<\/title>/i ) { $title = $1; $titleName = $1; }
			#とりあえず著者情報取得
			if ($line =~ /<meta name=\"author\" content=\"(.*)\">/i ) { $author = $1; }

		} elsif ($print_sw eq 1) {

			$line =~ s/<p>//ig;
			$line =~ s/<p class=column>//ig;
			$line =~ s/<\/p>//ig;
			$line =~ s/\n//g;
			
			if ($line eq "") { 
				next; 
			} elsif ($line =~ /class=title/i) { 
				next;
			}
			else { push(@DATA,$line); }
		}
	}

	if (length($meta_time) eq 14) {
		$year = substr($meta_time,0,4) - 1900;
		$mon = substr($meta_time,4,2) - 1;
		$mday = substr($meta_time,6,2);
		$hour = substr($meta_time,8,2);
		$min = substr($meta_time,10,2);
		$sec = substr($meta_time,12,2);
	} else {
		($sec,$min,$hour,$mday,$mon,$year,$wday,$yday,$isdst) = localtime($meta_time);
	}

	$formDate = sprintf("%04d.%02d.%02d",$year + 1900,$mon + 1,$mday);
	$formTime = sprintf("%02d:%02d:%02d",$hour,$min,$sec);

	$msg = "<table width=\"$x_table\" border=0 align=center><tr><td>
	<form action=\"$cgi_name\" method=\"$method\" ENCTYPE=\"multipart/form-data\">
	<table border=\"0\" cellspacing=\"0\" cellpadding=\"3\" align=\"center\" class=\"formTable\">";
		push(@OUTHTML,$msg);

	if ($genre_kensu ne 1) {
		$msg = "<tr><td align=right valign=top nowrap>ジャンル</td><td><select name=\"genre\" class=\"fSelect\">";
		push(@OUTHTML,$msg);
	
		foreach $line (@GENRE) {
			if ($line eq $now_genre) {
				$selected = " selected";
			} else {
				$selected = "";
			}
			push(@OUTHTML,"<option value=\"$line\"$selected>$GENRE_TABLE{$line}</option>");
		}
	
		$msg = "</select></td></tr>";
		push(@OUTHTML,$msg);
	} else {
		$msg = "<input type=hidden name=genre value=$GENRE[0]>";
		push(@OUTHTML,$msg);
	}

	$msg = "<tr><td align=right valign=top nowrap>タイトル</td>
	<td><input type=\"text\" name=\"title\" size=\"$cols2\" value=\"$title\" class=\"fInput\"></td></tr>";
	push(@OUTHTML,$msg);
	
	if ($input_author eq 1) {
		$msg = "<tr><td align=right valign=top nowrap>著者</td>
		<td><select name=\"writer1\" class=\"fSelect\"><option value=\"$author\" selected>$author</option>";
		push(@OUTHTML,$msg);
		foreach $line (@WRITER) {
			push(@OUTHTML,"<option>$line</option>");
		}
		$msg = "<option value=\"\">　</option></select> <input type=\"text\" name=\"writer2\" size=\"20\" class=\"fInput\"></td></tr>";
		push(@OUTHTML,$msg);
	}
	if ($updatecheck eq 1) {
		$updatechecked = " checked";
	} else {
		$updatechecked = "";
	}
		
	$msg = "<tr><td align=right valign=top nowrap>$dateTimeText</td>
	<td><input type=\"text\" name=\"formDate\" size=\"14\" value=\"$formDate\" class=\"fInput\"> <input type=\"$updateTimeType\" name=\"formTime\" value=\"$formTime\" size=\"14\" class=\"fInput\"><input type=\"checkbox\" name=\"updateDate\" value=\"update\">$dateTimeText更新</td></tr>";
	push(@OUTHTML,$msg);

	foreach $num (1 .. $#DATA) {

		if ($DATA[$num] =~ /^<img src="(.*)" width="(.*)" height="(.*)" class="img" align="(.*)" alt="(.*)" name="a-column">(.*)<br clear=all>/i) {
			$column_photo = $1;
			$column_align = $4;
			$column = $6;
		} elsif ($DATA[$num] =~ /^<div class="imgPosition"><img src="(.*)" width="(.*)" height="(.*)" class="img" alt="(.*)" name="a-column"><\/div><p class="column">(.*)/i) {
			$column_photo = $1;
			$column_align = "top";
			$column = $5;
		} elsif ($DATA[$num] =~ /^<div class="imgPosition"><img src="(.*)" width="(.*)" height="(.*)" class="img" alt="(.*)" name="a-column"><\/div>(.*)/i) {
			$column_photo = $1;
			$column_align = "top";
			$column = $5;
		} elsif ($DATA[$num] =~ /<p class="column">(.*)<div class="imgPosition"><img src="(.*)" width="(.*)" height="(.*)" class="img" alt="(.*)" name="a-column"><\/div>/i) {
			$column = $1;
			$column_photo = $2;
			$column_align = "bottom";
		} elsif ($DATA[$num] =~ /(.*)<div class="imgPosition"><img src="(.*)" width="(.*)" height="(.*)" class="img" alt="(.*)" name="a-column"><\/div>/i) {
			$column = $1;
			$column_photo = $2;
			$column_align = "bottom";
		} elsif ($DATA[$num] =~ /<p class="column">(.*)/i) {
			$column = $1;
			$column_photo = "";
			$column_align = "";
		} else {
			$column = $DATA[$num];
			$column_photo = "";
			$column_align = "";
		}
			if ($cr_sw eq 1) { 
				$column =~ s/<br>/\n/ig;
			}

		# フォームサイズを自動調整
		$column_lenght = length ($column);
		if ($column_lenght < $check_length) {
			$auto_rows = $rows;
		} else {
			$auto_rows = int ($column_lenght / $cols); 
		}

		$msg = "<tr>
			<td colspan=2><hr></td></tr>
		<tr>
			<td align=right valign=top nowrap>内容</td>
			<td><textarea name=\"column$num\" cols=\"$cols\" rows=\"$auto_rows\" class=\"fInput\">$column</textarea></td>
		</tr>";
		push(@OUTHTML,$msg);

		if ($column_photo ne "") {
			$msg = "<tr><td align=right valign=top nowrap>写真</td>
			<td><select name=\"align$num\" class=\"fSelect\">";
			push(@OUTHTML,$msg);
			
			if ($column_align eq "left") {
				$msg = "<option value=\"left\" selected>写真を左寄せ<option value=\"top\">写真を上に<option value=\"bottom\">写真を下に<option value=\"right\">写真を右寄せ<option value=\"delete\">写真を削除";
				if (-e $imagemagick) {
					$msg .= "<option value=rotate90>時計回りで回転<option value=rotate-90>反時計回りで回転";
				}
			} elsif ($column_align eq "right") {
				$msg = "<option value=\"left\">写真を左寄せ<option value=\"top\">写真を上に<option value=\"bottom\">写真を下に<option value=\"right\" selected>写真を右寄せ<option value=\"delete\">写真を削除";
				if (-e $imagemagick) {
					$msg .= "<option value=rotate90>時計回りで回転<option value=rotate-90>反時計回りで回転";
				}
			} elsif ($column_align eq "top") {
				$msg = "<option value=\"left\">写真を左寄せ<option value=\"top\" selected>写真を上に<option value=\"bottom\">写真を下に<option value=\"right\">写真を右寄せ<option value=\"delete\">写真を削除";
				if (-e $imagemagick) {
					$msg .= "<option value=rotate90>時計回りで回転<option value=rotate-90>反時計回りで回転";
				}
			} else {
				$msg = "<option value=\"left\">写真を左寄せ<option value=\"top\">写真を上に<option value=\"bottom\" selected>写真を下に<option value=\"right\">写真を右寄せ<option value=\"delete\">写真を削除";
				if (-e $imagemagick) {
					$msg .= "<option value=rotate90>時計回りで回転<option value=rotate-90>反時計回りで回転";
				}
			}
			push(@OUTHTML,$msg);
	
			if ($column_photo=~ /(.*)\/(.*)$/) {
				$photo_no = $2;
			}
			
			$msg = "</select>\n <input type=hidden name=now_align$num value=$column_align> <input type=checkbox name=kaigyo$num value=off>改行無効<br><img src=\"$column_photo\"><input type=hidden name=photo$num value=\"$photo_no\"></td></tr>";
			push(@OUTHTML,$msg);
		} else {
			$msg = "<tr><td align=right valign=top nowrap>写真</td>
			<td><input type=\"file\" name=\"attachment$num\" size=\"15\" class=\"fFile\"> <select name=\"align$num\" class=\"fSelect\"><option value=left selected>写真を左寄せ<option value=top>写真を上に<option value=bottom>写真を下に<option value=right>写真を右寄せ</select> <input type=checkbox name=kaigyo$num value=off>改行無効</td></tr>";
			push(@OUTHTML,$msg);
		}
		
	}

	$msg = "</table>
	<input type=hidden name=file value=\"$in{'file'}\">
	<input type=hidden name=time value=\"$meta_time\">
	<input type=hidden name=now_genre value=\"$now_genre\">
	<input type=hidden name=count value=\"$#DATA\">
	<input type=hidden name=action value=\"update2\">
	<input type=hidden name=pass value=\"$in{'pass'}\">
	<p align=center class=msg>内容欄を空欄にすると削除できます。</p>
	<p align=center><input type=submit value=\" 更　新 \" class=\"fButton\">　<input type=reset value=\" リセット \" class=\"fButton\"></p>
	</form></td></tr></table>";
	
	push(@OUTHTML,$msg);

}

sub add_form {

	&tag_editor;
	
	$msg = "<form action=$cgi_name method=$method  name=\"form1\"  ENCTYPE=\"multipart/form-data\">
	<table border=\"0\" cellspacing=\"0\" cellpadding=\"5\" align=\"center\" class=\"formTable\">
		<tr>
			<td align=right valign=top nowrap>内容</td>
			<td><textarea name=\"column\" cols=\"$cols\" rows=\"$rows\" class=\"fInput\">$DATA[$num]</textarea></td>
		</tr>
		<tr><td align=right valign=top nowrap>写真</td>
            <td> <input type=\"file\" name=\"attachment\" size=\"20\" class=\"fFile\"> <select name=\"align\" class=\"fSelect\"><option value=left>写真を左寄せ<option value=top>写真を上に<option value=bottom>写真を下に<option value=right>写真を右寄せ</select></td>
          </tr>
		  	<tr><td align=right valign=top nowrap>$dateTimeText</td>
			<td>$update_date <input type=checkbox name=\"update\" value=\"suru\" checked>更新する　<input type=checkbox name=\"kaigyo\" value=\"off\">改行無効</td></tr>
	</table>
	<input type=hidden name=file value=\"$in{'file'}\">
	<input type=hidden name=action value=\"add2\">
	<input type=hidden name=pass value=\"$in{'pass'}\">
	<input type=hidden name=genre value=\"$now_genre\">
	<p>";
	push(@OUTHTML,$msg);
	
	if ($add_ichi  eq 1) {
		$msg ="<input type=submit name=ichi value=\"$add_btn1\" class=\"fButton\">　<input type=reset value=\"リセット \" class=\"fButton\">";
	} elsif ($add_ichi  eq 2) {
		$msg ="<input type=submit name=ichi value=\"$add_btn0\" class=\"fButton\">　<input type=submit name=ichi value=\"$add_btn1\" class=\"fButton\">";
	} else {
		$msg ="<input type=submit name=ichi value=\"$add_btn0\" class=\"fButton\">　<input type=reset value=\"リセット \" class=\"fButton\">";
	}
	push(@OUTHTML,$msg);
		
	$msg = "</form></td></tr></table>";
	push(@OUTHTML,$msg);

}

sub tag_editor {

	$msg = "<SCRIPT LANGUAGE=\"JavaScript\">
	<!-- //
	function addurl() {
			document.form1.column.value = document.form1.column.value + '<a href=' + '\"' + 'URL' + '\"' + ' target=' + '\"' + '_blank' + '\">Link</a>';
	}
	function addbold() {
			document.form1.column.value = document.form1.column.value + '<b>太字</b>';
	}
	// -->
	</SCRIPT>
	<table width=\"$x_table\" border=0 align=center><tr><td align=center>
	<hr size=4 width=\"80%\">
	簡易タグエディタ：<a href=\"JavaScript:addurl();\">URL挿入</a>・<a href=\"JavaScript:addbold();\">Bold挿入</a>
	<hr size=4 width=\"80%\">";
	
	push(@OUTHTML,$msg);

}

sub regist {
	
	if ($in{'title'} eq "") {
		&error("入力チェックエラー","タイトルの入力がありません。"); 
	}
	
	if ($in{'column'} eq "") {
		&error("入力チェックエラー","本文の入力がありません。"); 
	}
	
	$column_dir = "$site_path/$in{'genre'}";

	$in{'filename'} =~ s/\.//g; 
	$in{'filename'} =~ s/\///g; 
	$column_filename = $in{'filename'}.".html";
	$column_file = "$column_dir/" . $column_filename;

	if (-e $column_file) {
		&error("入力チェックエラー","既に同じファイル名「$in{'filename'}.html」が存在します。"); 
	}
	
	if ($column_filename eq $new_html || $column_filename eq $genre_index) {
		&error("入力チェックエラー","$in{'filename'}.html というファイル名は利用できません。"); 
	}

#ニュース本文編集
	$column = $in{'column'};
	$column_title = $in{'title'};
	$column_align = $in{'align'};
	
	if ($input_author eq 1) {
		$writer = "$in{'writer1'}$in{'writer2'}";
		$author = "<meta name=\"author\" content=\"$writer\">";
	}

	($sec,$min,$hour,$mday,$mon,$year,$wday,$yday,$isdst) = localtime($now_time);
	$metaTag = sprintf("%04d%02d%02d%02d%02d%02d",$year + 1900,$mon + 1,$mday,$hour,$min,$sec);
	$meta_updatetime = "<meta name=\"update-time\" content=\"$metaTag\">";
	
	if ($in{'attachment'} ne "") {
		$column_photo = "attachment";
	} else {
		$column_photo = "";
	}
	$photo_no = $now_time;
	
	if ($in{'kaigyo'} eq "off") {
		$column =~ s/\n//g; 
		$column =~ s/\r//g; 
	}
	
	$photo_path = "$site_path/$photo_dir";	
	$photo_file = "$photo_path/$now_time.$GAZO{attachment}";

	if ($in{'attachment'} ne "") {
		unless(-e $photo_path){ mkdir($photo_path, 0777); $change = chmod(0777, "$photo_path"); }
		if (!open(OUT,">$photo_file")) { &error('ファイルをアップロードできません．'); }
		binmode OUT;
		print OUT $in{'attachment'};
		close(OUT);
		$change = chmod(0666, "$photo_file");
	}

	# 画像サイズチェック
	my ($format,$width, $height) = &GetImageSize("$photo_path/$now_time.$GAZO{'attachment'}");
	
	if ($column_align eq "top" || $column_align eq "bottom") {
		$max_img_x = $max_img_width_center;
	} else {
		$max_img_x = $max_img_width;
	}
	
	if ($max_img_x < $width) {
		$height = int($height * ($max_img_x / $width));
		$width = $max_img_x;
	} 
	$kakeru = "x";
	$new_filename = "$now_time\_$width$kakeru$height.$GAZO{'attachment'}";
	$new_path_filename = "$photo_path/$new_filename";
	$rename = rename $photo_file , $new_path_filename;

	#imagemagickにより実画像をリサイズ
	if (-e $imagemagick) {
		$convertSize = $width.$kakeru.$height;
		system ("$imagemagick -resize $convertSize $new_path_filename $new_path_filename");
	}
	
	$photo{attachment} = $new_filename;
	$x{attachment} = $width;
	$y{attachment} = $height;
	
	&p_edit;

	$print_time = &date_time_print($now_time);


	$temp_check = "$site_path/$in{'genre'}/$template_file2";
	if  (!(-e $temp_check)) {
		$temp_check =  $template_file2;
	}

#----- テンプレートファイル読み込み -----
	open(TEMPFILE2, $temp_check) || &error("ファイル読込エラー<br>[$temp_check]", "テンプレートファイルが開けません。<br>上記の場所にファイルがあるか確認してください。");
	@TEMPLATE2 = <TEMPFILE2>;
	close(TEMPFILE2);

	unless(-e $column_dir){ mkdir($column_dir, 0777); $change = chmod(0777, "$column_dir"); }

	open (OUT,">$column_file");

	foreach $line (@TEMPLATE2) {
	
		if ($genreTitlePrint eq 1) {
			$line =~ s/<!--genreTitle-->/$GENRE_TABLE{$in{'genre'}}/ig;
		}
			
			
		$line =~ s/<!--title_include-->/$column_title/ig;
		$line =~ s/<!--update_time-->/$print_time/ig;
		$line =~ s/<\/head>/$meta_updatetime\n<\/head>/ig;
		
		if ($input_author eq 1) { 
			$line =~ s/<!--writer_include-->/$writer/ig; 
		}
		
		if ($generator_check eq 1) {
			$line =~ s/<\/head>/$meta_generator\n<\/head>/ig;
		}
				
		if ($line =~ /<!--from-->/i) {
			$ato_print = $';
			print OUT $`;
			print OUT "<!--from-->\n";
			if ($title_ichi ne 1) { 
				print OUT "<$title_tag class=title>$column_title</$title_tag>\n";
			}
			print OUT $p_data;
			$ato_print =~ s/\n//g; 
			$ato_print =~ s/\r//g; 
			print OUT $ato_print;
		} else {
			print OUT $line;
		}
	}

	close(OUT);
	
	$ret = chmod(0666, "$column_file");

	&new_html_out;
	&fileCheck($in{'genre'});
		
	#更新日時の更新
	&upinfo_update;

	$in{'file'} = "$in{'filename'}.html";

}

sub update {

#写真のアップロード

	$i = 0;
	$up_photo = $now_time;
	
	while ($i < $in{'count'} + 1) {
	
		$photo_path = "$site_path/$photo_dir";	
		$photo_file = "$photo_path/$up_photo.$GAZO{\"attachment$i\"}";
	
		if ($in{"attachment$i"} ne "") {
			unless(-e $photo_path){ mkdir($photo_path, 0777); $change = chmod(0777, "$photo_path");}
			if (!open(OUT,">$photo_file")) { &error('ファイルをアップロードできません．'); }
			binmode OUT;
			print OUT $in{"attachment$i"};
			close(OUT);
			$change = chmod(0666, "$photo_file");
			
			# 画像サイズチェック
			$checkimg = "$photo_path/$now_time." . $GAZO{"attachment$i"};
			my ($format,$width, $height) = &GetImageSize($checkimg);

			if ($in{"align$i"} eq "top" || $in{"align$i"} eq "bottom") {
				$max_img_x = $max_img_width_center;
			} else {
				$max_img_x = $max_img_width;
			}
			
			if ($max_img_x < $width) {
				$height = int($height * ($max_img_x / $width));
				$width = $max_img_x;
			} 
			$kakeru = "x";
			$new_filename = "$now_time\_$width$kakeru$height." . $GAZO{"attachment$i"};
			$new_path_filename = "$photo_path/$new_filename";
			$rename = rename $photo_file , $new_path_filename;

			#imagemagickにより実画像をリサイズ
			if (-e $imagemagick) {
				$convertSize = $width.$kakeru.$height;
				system ("$imagemagick -resize $convertSize $new_path_filename $new_path_filename");
			}

			$photo{"attachment$i"} = $new_filename;
			$x{"attachment$i"} = $width;
			$y{"attachment$i"} = $height;
			
			$up_photo = $up_photo + 1;
		}
		$i = $i + 1;
	}

#----- テンプレートファイル読み込み -----

	$temp_check = "$site_path/$in{'genre'}/$template_file2";
	if  (!(-e $temp_check)) {
		$temp_check =  $template_file2;
	}
	
	open(TEMPFILE2, $temp_check) || &error("ファイル読込エラー<br>[$temp_check]", "テンプレートファイルが開けません。<br>上記の場所にファイルがあるか確認してください。");
	@TEMPLATE2 = <TEMPFILE2>;
	close(TEMPFILE2);

	$column_html = $in{'file'};
	$column_dir = "$site_path/$in{'genre'}";
	$column_file = "$column_dir/$column_html";

	if ($in{'genre'} ne "") { 
		if ($in{'now_genre'} ne $in{'genre'}) {
			
			if ($in{'genre'}) {
				if (-e $column_file) {
					&error("入力チェックエラー","既に同じファイル名「$column_html」が存在します。"); 
				}
			}
		
			$in{'update'} = "suru";
			unless(-e $column_dir){ mkdir($column_dir, 0777); $change = chmod(0777, "$column_dir"); }
			$column_file2 = "$site_path/$in{'now_genre'}/$in{'file'}";
			$del = unlink $column_file2;
		}
	} 
	
	if ($in{'updateDate'}) {
		$year = $now_year; $month = $now_month; $day = $now_day;
		$hour = $now_hour; $min =$now_min; $sec = $now_sec;
	} else {
		$formDate = &date_check($in{"formDate"});
		($year,$month,$day) = split(/\./,$formDate);
		($hour,$min,$sec) = split(/:/,$in{"formTime"});
	}
	$meta_updatetime = "<meta name=\"update-time\" content=\"$year$month$day$hour$min$sec\">";
	$print_time = &date_time_print("$year$month$day$hour$min$sec");

	open (OUT,">$column_file");
	
	if ($input_author eq 1) {
		$writer = "$in{'writer1'}$in{'writer2'}";
		$author = "<meta name=\"author\" content=\"$writer\">";
	}	
	
	foreach $line (@TEMPLATE2) {


	if ($genreTitlePrint eq 1) {
		$line =~ s/<!--genreTitle-->/$GENRE_TABLE{$in{'genre'}}/ig;
	}

	$line =~ s/<!--title_include-->/$in{'title'}/ig;
	$line =~ s/<!--update_time-->/$print_time/ig;
	
	if ($input_author eq 1) {
		$line =~ s/<!--writer_include-->/$writer/ig;
		$line =~ s/<\/head>/$author\n<\/head>/ig;
	}
	
	if ($generator_check eq 1) {
		$line =~ s/<\/head>/$meta_generator\n<\/head>/ig;
	}
	

	$line =~ s/<\/head>/$meta_updatetime\n<\/head>/ig;
	
	if ($line =~ /<!--from-->/i) {
		$ato_print = $'; 
		print OUT $`;
		print OUT "<!--from-->\n";
		if ($title_ichi ne 1) { 
			print OUT "<$title_tag class=title>$in{'title'}</$title_tag>\n";
		}
		$i = 0;
		$up_photo = $now_time - 1;
		
		while ($i < $in{'count'} + 1) {
		
			$column = $in{"column$i"};
			$column =~ s/\r//g;
			if ($in{"kaigyo$i"} eq "off") {
				$column =~ s/\n//g; 
			}
			$column_title = $in{"title$i"};
			
			$column_photo = "";
			
			if ($in{"attachment$i"} ne "") {
				$column_photo = "attachment$i";
				$up_photo = $up_photo + 1;
				$photo_no = $up_photo;
			}
			
			if ($in{"photo$i"} ne "") {
				$column_photo = "attachment$i";
				$photo{$column_photo} = $in{"photo$i"};
				($dummy,$sizexy) = split(/_/,$in{"photo$i"});
				
				if ($sizexy) {
					
					($x{$column_photo},$sizeY) = split(/x/,$sizexy);
					($y{$column_photo},$dummy) = split(/\./,$sizeY);
					
				} else {

					$checkimg = "$photo_path/".$in{"photo$i"};
					($fileName,$imgType) = split(/\./,$in{"photo$i"});
					
					my ($format,$width, $height) = &GetImageSize($checkimg);


					if ($in{"align$i"} eq "top" || $in{"align$i"} eq "bottom") {
						$max_img_x = $max_img_width_center;
					} else {
						$max_img_x = $max_img_width;
					}
					
					if ($max_img_x < $width) {
						$height = int($height * ($max_img_x / $width));
						$width = $max_img_x;
					} 
					$kakeru = "x";
					$new_filename = "$fileName\_$width$kakeru$height." . $imgType;
					$new_path_filename = "$photo_path/$new_filename";
					$rename = rename $checkimg , $new_path_filename;
				
					$photo{"attachment$i"} = $new_filename;
					$x{"attachment$i"} = $width;
					$y{"attachment$i"} = $height;

				}
			} 
			
			if ($in{"now_align$i"}) {
				if ($in{"align$i"} ne $in{"now_align$i"}) {
			
					$checkimg = "$photo_path/".$in{"photo$i"};
					($fileName,$imgType) = split(/\./,$in{"photo$i"});
					($fileName,$size) = split(/_/,$fileName);
					
					my ($format,$width, $height) = &GetImageSize($checkimg);

					if ($in{"align$i"} eq "top" || $in{"align$i"} eq "bottom") {
						$max_img_x = $max_img_width_center;
					} else {
						$max_img_x = $max_img_width;
					}
					
					if ($max_img_x < $width) {
						$height = int($height * ($max_img_x / $width));
						$width = $max_img_x;
					} 
					$kakeru = "x";
					$new_filename = "$fileName\_$width$kakeru$height." . $imgType;
					$new_path_filename = "$photo_path/$new_filename";
					$rename = rename $checkimg , $new_path_filename;
				
					$photo{"attachment$i"} = $new_filename;
					$x{"attachment$i"} = $width;
					$y{"attachment$i"} = $height;

				} 
				
			}
		
			if ($in{"align$i"} eq "delete") {
				$column_photo = "";			
				$photo_file = "$site_path/$photo_dir/".$in{"photo$i"};
				if (-e $photo_file ) {
					$del = unlink $photo_file;
				}

			} elsif ($in{"align$i"} eq "rotate90") {
			
				$photo_file = "$site_path/$photo_dir/".$in{"photo$i"};
				($fileName,$imgType) = split(/\./,$in{"photo$i"});
				($fileName,$size) = split(/_/,$fileName);
					
				my ($format,$width, $height) = &GetImageSize($photo_file);
				$new_filename = "$fileName\_".$height ."x". $width . "." . $imgType;
				$new_photo_file = $photo_path ."/" . $new_filename;
				if (-e $imagemagick) {
					system ("$imagemagick -rotate 90 $photo_file $photo_file");
				}
				$rename = rename $photo_file , $new_photo_file;

				$column_align = $in{"now_align$i"};
				$photo{"attachment$i"} = $new_filename;
				$y{"attachment$i"} = $width;
				$x{"attachment$i"} = $height;
				
			} elsif ($in{"align$i"} eq "rotate-90") {
			
				$photo_file = "$site_path/$photo_dir/".$in{"photo$i"};
				($fileName,$imgType) = split(/\./,$in{"photo$i"});
				($fileName,$size) = split(/_/,$fileName);
				
				my ($format,$width, $height) = &GetImageSize($photo_file);
				$new_filename = "$fileName\_".$height ."x". $width . "." . $imgType;
				$new_photo_file = $photo_path ."/" . $new_filename;
				if (-e $imagemagick) {
					system ("$imagemagick -rotate -90 $photo_file $photo_file");
				}
				$rename = rename $photo_file , $new_photo_file;

				$column_align = $in{"now_align$i"};
				$photo{"attachment$i"} = $new_filename;
				$y{"attachment$i"} = $width;
				$x{"attachment$i"} = $height;

			} else {
				$column_align = $in{"align$i"};
			}
		
			if ($column ne "" || $column_title ne "") {
				&p_edit;
				
				print OUT $p_data;
			} else {
				#画像削除
				$photo_no = $in{"photo$i"};
				$photo_file = "$site_path/$photo_dir/$photo_no";
				if (-e $photo_file ) {
					$del = unlink $photo_file;
				}
			}	
			$i = $i + 1;
		}
			$ato_print =~ s/\n//g; 
			$ato_print =~ s/\r//g; 
			print OUT $ato_print;
		} else {
			print OUT $line;
		}
	}

	close(OUT);

	&new_html_out;
	&fileCheck($in{'now_genre'});
	&fileCheck($in{'genre'});
	
	#更新日時の更新
	&upinfo_update;

}

sub add {

	if ($in{'column'} eq "" && $in{'title'} eq "") {
		&error("入力チェックエラー","タイトルと本文の両方の入力がありません。"); 
	}

	$photo_path = "$site_path/$photo_dir";	
	$photo_file = "$photo_path/$now_time.$GAZO{'attachment'}";

	if ($in{'attachment'} ne "") {
		unless(-e $photo_path){ mkdir($photo_path, 0777); $change = chmod(0777, "$photo_path");}
		if (!open(OUT,">$photo_file")) { &error('ファイルをアップロードできません．'); }
		binmode OUT;
		print OUT $in{'attachment'};
		close(OUT);
		$change = chmod(0666, "$photo_file");
	}

	# 画像サイズチェック
	my ($format,$width, $height) = &GetImageSize("$photo_path/$now_time.$GAZO{'attachment'}");

	if ($in{'align'} eq "top" || $in{'align'} eq "bottom") {
		$max_img_x = $max_img_width_center;
	} else {
		$max_img_x = $max_img_width;
	}
	
	if ($max_img_x < $width) {
		$height = int($height * ($max_img_x / $width));
		$width = $max_img_x;
	} 
	$kakeru = "x";
	$new_filename = "$now_time\_$width$kakeru$height.$GAZO{'attachment'}";
	$new_path_filename = "$photo_path/$new_filename";
	$rename = rename $photo_file , $new_path_filename;

	#imagemagickにより実画像をリサイズ
	if (-e $imagemagick) {
		$convertSize = $width.$kakeru.$height;
		system ("$imagemagick -resize $convertSize $new_path_filename $new_path_filename");
	}
	
	$photo{attachment} = $new_filename;
	$x{attachment} = $width;
	$y{attachment} = $height;

	if ($in{'ichi'} eq $add_btn1) {
		$add_ichi = 1;
	} else {
		$add_ichi = 0;
	}

	$column_file = "$site_path/$in{'genre'}/$in{'file'}";
	
	$column = $in{'column'};
	$column_align = $in{'align'};
	
	if ($in{'attachment'} ne "") {
		$column_photo = "attachment";
	} else {
		$column_photo = "";
	}
	if ($in{'kaigyo'} eq "off") {
		$column =~ s/\n//g; 
		$column =~ s/\r//g; 
	}
	
	$photo_no = $now_time;
	
	&p_edit;

	if (!open(IN,"$column_file")) { &error("データ読取エラー<br>[$column_file]","設定ファイルの設定が間違っている可能性があります。"); }
	@column = <IN>;
	close(IN);

	open (OUT,">$column_file");

	foreach $line (@column) {

		if ($line =~ /<meta name=\"update-time\"/i) {
			if ($in{'update'} eq "suru") {
				($sec,$min,$hour,$mday,$mon,$year,$wday,$yday,$isdst) = localtime($now_time);
				$metaTag = sprintf("%04d%02d%02d%02d%02d%02d",$year + 1900,$mon + 1,$mday,$hour,$min,$sec);
				$meta_updatetime = "<meta name=\"update-time\" content=\"$metaTag\">\n";
				print OUT $meta_updatetime;
				next;
			}
		}
	
		if ($add_ichi eq 1) {
			if ($title_ichi ne 1) { 
				if ($line =~ /class=title/i) {
					print OUT $line;
					print OUT $p_data;
				} else {
					print OUT $line;
				}
			} else {
				if ($line =~ /<!--from-->/i) {
					print OUT $line;
					print OUT $p_data;
				} else {
					print OUT $line;
				}
			}
		} elsif ($add_ichi eq 0) {
			if ($line =~ /<!--to-->/i) {
				print OUT $p_data;
			}
			print OUT $line;
		}
	}
	close(OUT);
	
	&new_html_out;
	&fileCheck($in{'genre'});
	
	#更新日時の更新
	&upinfo_update;

	
}

sub p_edit {
	
	if ($cr_sw eq 1) { 
		$column =~ s/\n/<br>/ig;
	} else {
		$column =~ s/\n//g;
	}
	
	$photo_tag1 = "<p class=\"column\">";
	$photo_tag2 = "</p>";
		
	if ($column_photo ne "") {
		if ($column_align eq "left" || $column_align eq "right") {
			$photo_tag1 = "<p class=column><img src=\"$url/$photo_dir/$photo{$column_photo}\" width=\"$x{$column_photo}\" height=\"$y{$column_photo}\" class=\"img\" align=\"$column_align\" alt=\"photo\" name=\"a-column\">";
			$photo_tag2 = "<br clear=all></p>";
		} elsif ($column_align eq "top") {
			$photo_tag1 = "<div class=\"imgPosition\"><img src=\"$url/$photo_dir/$photo{$column_photo}\" width=\"$x{$column_photo}\" height=\"$y{$column_photo}\" class=\"img\" alt=\"photo\" name=\"a-column\"></div><p class=\"column\">";
			$photo_tag2 = "</p>";
		} elsif ($column_align eq "bottom") {
			$photo_tag1 = "<p class=\"column\">";
			$photo_tag2 = "</p><div class=\"imgPosition\"><img src=\"$url/$photo_dir/$photo{$column_photo}\" width=\"$x{$column_photo}\" height=\"$y{$column_photo}\" class=\"img\" alt=\"photo\" name=\"a-column\"></div>";
		}
	}
	
	$p_data = "$photo_tag1$column$photo_tag2\n";
	
}


sub delete {
	
	$column_file = "$site_path/$in{'genre'}/$in{'file'}";

	if (!open(IN,"$column_file")) { &error("データ読取エラー<br>[$column_file]","設定ファイルの設定が間違っている可能性があります。"); }
	@column = <IN>;
	close(IN);
	
	foreach $line (@column) {
	
		$line =~ s/<p>//ig;
		$line =~ s/<p class=column>//ig;
		$line =~ s/<\/p>//ig;
		$line =~ s/\n//g;
	
		if ($line=~ /^<img src=\"(.*)\" width=\"(.*)\" height=\"(.*)\" class=\"(.*)\" align=\"(.*)\" name=\"a-column\">(.*)<br clear=all>/) {
			$column_photo = $1;
		} elsif ($line =~ /<center><img src=\"(.*)\" width=\"(.*)\" height=\"(.*)\" class=\"(.*)\" align=\"(.*)\" name=\"a-column\"><\/center>/) {
			$column_photo = $1;
		} elsif ($line =~ /^<img src=\"(.*)\" align=\"(.*)\" name=\"a-column\">(.*)<br clear=all>/i) {
			$column_photo = $1;
		}
	
		if ($column_photo=~ /(.*)\/(.*)$/) {
			$photo_no = $2;
		}

		$photo_file = "$site_path/$photo_dir/$photo_no";
		if (-e $photo_file ) {
			$del = unlink $photo_file;
		}
	
	}
	
	$del = unlink $column_file;
	
	&fileCheck($in{'genre'});
	
	#更新日時の更新
	&upinfo_update;
	
	$in{'genre'} ="";
}

sub error {

if (!($setCookie)){
	print "Content-type: text/html\n\n";
}
			print "<html><head><title>error</title></head><body>\n";
			print "<table width=\"$x_table\" border=0 align=center><tr><td align=center>\n";
			print "<h3>$_[0]</h3>\n";
			print "<h3>$_[1]</h3>\n";
			print "<p>ブラウザの戻るボタンで前の画面に戻って下さい。<p>";
			print "</td></tr></table>\n";
			print "</body></html>\n";
exit;
}

sub pass_check ($) {

	$pass_check = shift;
	$setCookie = 0;
	
	if ($pass_check) {
		# 入力があった場合の処理
	
		if ($crypt_sw eq 1) {
			$crypted = crypt ( $pass_check , $pass_check );	
		} else {
			$crypted = $pass_check;
		}
		if ($passwd eq $crypted) { 
#			$crypted = crypt ( $crypted , $crypted );
			#set cookie	
			print "Content-type: text/html\n";
			print "Set-Cookie: a-Site=$crypted;\n\n";
			$setCookie = 1;
			return 1; 
		} else { 
			print "Content-type: text/html\n";
			print "Set-Cookie: a-Site=$crypted;expires=Thu, 01-Jan-1970 00:00:00 GMT;\n\n";
			$setCookie = 1;
			return 0;
		}
	} else {
		# 入力のなかった場合の処理

		if ($passCookieFlag eq 1) {

			if ($passwd eq $passCookieData) {
				return 1;
			} else {
				return 0;
			}
		
		} else {
			return 0;
		}
	}
}

sub updatetime_print {

	if ($in{'file'} eq "") {
		$dir_file = "$site_path/$upinfo_file";
		if (-e $dir_file) { 
			open(IN,"$dir_file");
			@UPFILE = <IN>;
			close(IN);
			$update_time = $UPFILE[0];
			($updateDate,$updateTime) = split(/ /,$update_time);
			my ($year,$month,$day) = split(/\//,$updateDate);
			my ($hour,$min,$sec) = split(/:/,$updateTime);
			$yobi = getwday($year,$month,$day);
			$update_time = &date_format($year,$month,$day,$yobi,$hour,$min,$sec,$dateFormat);
		} else {
			$update_time = "????/??/?? ??:??:??";
		}
		chomp $update_time;
		return $update_time;
	} else {
		$line =~ s/<!--update_time-->/$update_date/ig;
	}
}

sub upinfo_update {

	if ($update_day ne 0) {
		($sec,$min,$hour,$mday,$mon,$year,$wday,$yday,$isdst) = localtime($now_time);
		$up_year = $year + 1900;
		$up_month = ($mon + 1);
		$up_day = $mday;
		$update_time = sprintf("%04d/%02d/%02d %02d:%02d:%02d",$up_year,$up_month,$up_day,$hour,$min,$sec);
	
		$dir_file = "$site_path/$upinfo_file";
		
		open (OUT,">$dir_file");
		print OUT $update_time;
		close(OUT);
		$chmod = chmod(0666, "$dir_file");

	}
}

sub upfile_check {

		foreach (@in) {
		
			$_=~ s/\n//g;
			$_=~ s/\r//g;
			
			if ($_ =~ /^Content-Disposition: form-data\; name=\"(.*)\"; filename=\"(.*)\"Content-Type: image\/(.*)/i) { 
				$formname = $1;
				$GAZO{$formname} = $3;

				if ($GAZO{$formname} =~ /jpeg/i ) { $GAZO{$formname} = "jpg"; }
				elsif ($GAZO{$formname} =~ /gif/i ) { $GAZO{$formname} = "gif"; }
				elsif ($GAZO{$formname} =~ /png/i ) { $GAZO{$formname} = "png"; }
				else { $in{$1} = ""; }
			
			# NetFront対応
			} elsif ($_ =~ /^Content-Disposition: form-data\; name=\"(.*)\"; filename=\"(.*)\"Content-Type: application\/octet-stream/i) { 
				$formname = $1;
				$filename = $2;
				($dummy,$kakuchosi) = split(/\./,$filename);
				$kakuchosi =~ tr/[A-Z]/[a-z]/;
				$GAZO{$formname} = $kakuchosi;
			} 
		}	
}

sub date_time_print ($) {

	my $timestamp = shift;

	if (length($timestamp) eq 14) {
		$year = substr($timestamp,0,4);
		$mon = substr($timestamp,4,2);
		$mday = substr($timestamp,6,2);
		$hour = substr($timestamp,8,2);
		$min = substr($timestamp,10,2);
		$sec = substr($timestamp,12,2);
		$wday = getwday($year,$mon ,$mday);
	} else {
		($sec,$min,$hour,$mday,$mon,$year,$wday,$yday,$isdst) = localtime($timestamp);
		$mon = $mon +1;
		$year = $year + 1900;
	}
	$datetime_p = &date_format($year,$mon,$mday,$wday,$hour,$min,$sec,$dateFormat);
	
	return $datetime_p;
}

sub getwday ($$$) {

	my ($year,$month,$day) = @_;

	$month = $month + 0;
	if ($month eq 1 || $month eq 2) {
		$year--;
		$month +=12;
	}
	$wday = int($year + int($year/4) - int($year/100) + int($year/400) + int((13*$month+8)/5) + $day) % 7;
	return $wday;
}


sub fileCheck ($) {

	$dirName = shift;

	undef @files;
	undef @files2;
	
	$checkDir = "$site_path/$dirName";
	$dataFilePath = "$site_path/$dirName/$dataFile";
	opendir (DIR,"$checkDir"); 
	foreach $data (readdir(DIR)){
		if ($data =~ /.*\.html/){
			push(@files,"$data");
		}
	}

	if (@files) {
		foreach $checkFile (@files) {
		
		if ($checkFile eq $genre_index ||  $checkFile eq $new_html || $checkFile eq $template_file2 || $checkFile eq $template_file3) {
			next;
		}
		
		$checkDirFile = $checkDir . "/" . $checkFile;
		if (!open(IN,"$checkDirFile")) { &error("データ読取エラー<br>[$checkDirFile]","設定ファイルの設定が間違っている可能性があります。"); }
		@column = <IN>;
		close(IN);
		
		$metaTime = "0000000000";
		$authorName = "";
		$update_ng = 0; 
	
		foreach $line (@column) {

			# TITLEタグをチェックする
			if ($line =~ /<title>(.*)<\/title>/i ) {
				if ($1 eq "") { 
					$titleData = "タイトル無し"; 
				} else { 
					$titleData = $1; 
				}
			}
			
			# METAタグのタイムスタンプをチェック
			if ($line =~ /<meta name=\"update-time\" content=\"(.*)\">/i ) {
				if (length($1) eq 14) {
					$metaTime = $1;
				} else {
					($sec,$min,$hour,$mday,$mon,$year,$wday,$yday,$isdst) = localtime($1);
					$metaTime = sprintf("%04d%02d%02d%02d%02d%02d",$year + 1900,$mon + 1,$mday,$hour,$min,$sec);
				}
			} 
			
			# METAタグの作者をチェック
			if ($line =~ /<meta name=\"author\" content=\"(.*)\">/i ) {
				$authorName = $1;
			} 
			
			# a-column で作ったHTMLかどうかをチェック
			if ($generator_check eq 1) {
				if ($line =~ /$meta_generator/i ) {
					$update_ng = 1; 
				}
			}
			
			#ヘッダタグを閉じたらHTMLファイル内のチェックを終了
			if ($line =~ /<\/head>/i ) {
				last;
			}
		}
		
		# METAタグでの更新日取得ができない場合ファイルの更新日付をチェック
		if ($metaTime eq "0000000000") {
			($sec,$min,$hour,$mday,$mon,$year,$wday,$yday,$isdst) = localtime((stat("$checkDirFile"))[9]);
			$metaTime = sprintf("%04d%02d%02d%02d%02d%02d",$year + 1900,$mon + 1,$mday,$hour,$min,$sec);
		}
		
		push(@files2,"$metaTime;;$checkFile;;$titleData;;$update_ng;;$authorName\n");
		}

		if (!open(DB,">$dataFilePath ")) { &error("データベース書き込みエラー <br>[$site_path$dirName/$dataFile]","設定ファイルの設定が間違っている可能性があります。"); }
		print DB @files2;
		close(DB);
		$ret = chmod(0666, "$dataFilePath");

	} else {
		$del = unlink $dataFilePath;
	}

	# $dirName/index.html 生成
	&genre_index ($dirName);
}

sub genre_index ($) {

	if (!($genre_index)) {
		return;
	}
	
	undef @OUTHTML2;
	undef @files2;
	$genre_data = shift;
	
	$checkDir = "$site_path/$genre_data";
	if (!(-e $checkDir)) {
		return;
	}
	
	if ($secret ne $genre_data) {
		&file_read2;
	}
	
	if ($title_zero eq 1) {
		$file_count = @files2;
	} else {
		$file_count = 1;
	}
	
	if($file_count ne 0) {

		if ($GENRE_TABLE{$genre_data} ne "") {
			$title_image = "$site_path/$photo_dir/$genre_data.gif";
			if (-e $title_image) {
				my ($format,$width, $height) = &GetImageSize($title_image);
				$msg = "<$list_title_tag><img src=\"$url/$photo_dir/$genre_data.gif\" width=\"$width\" height=\"$height\" alt=\"$GENRE_TABLE{$genre_data}\"></$list_title_tag>";
			} else {
				$msg = "<$list_title_tag>$GENRE_TABLE{$genre_data} </$list_title_tag>";
				
			}
			$genreTitleText = $GENRE_TABLE{$genre_data};
		}
		
		$msg = "$top_tag";
		push(@OUTHTML2,$msg);
		
		foreach (@files2) {
		
			chomp $_;
			($meta_time,$data_file,$title_data,$update_ng) = split(/\;;/,$_);
		
			$data_path = $data_file;
			
			if ($www_server ne ".") {
				$index_link = $www_server . "/" . $genre_data . "/";
			} else {
				$index_link = "";
			}
			
			$update_date = &date_time_print($meta_time);
			$printData = $listTag;
			
			$printData =~ s/{title}/$title_data/g;
			$printData =~ s/{url}/$cgi_link2$data_path/g;
			$printData =~ s/{date}/$update_date/g;
			
			push(@OUTHTML2,$printData);
		}
		# ----- HTMLファイルリスト分をループ ----- ( ここまで ) -----
		
		push(@OUTHTML2,$foot_tag);

	}
	
	if (!($template_file3)) {
		$template_file3 = "nasi";
	}
	$read_temp = "$site_path/$genre_data/$template_file3";
	if  (!(-e $read_temp)) {
		$read_temp =  $template_file3;
		if  (!(-e $read_temp)) {
			$read_temp = "$site_path/$genre_data/$template_file2";
			if  (!(-e $read_temp)) {
				$read_temp =  $template_file2;
			}
		}
	}

#	$print_time = &date_time_print("$now_year$now_month$now_day$now_hour$now_min$now_sec");
	$yobi = getwday($now_year,$now_month,$now_day);
	$print_time = &date_format($now_year,$now_month,$now_day,$yobi,$now_hour,$now_min,$now_sec,$dateFormat);

	open(TEMPFILE, $read_temp) || &error("ファイル読込エラー<br>[$read_temp]","テンプレートファイルが開けません。");
	@GENREHTML = <TEMPFILE>;
	close(TEMPFILE);

	$genreIndexFile = "$site_path/$genre_data/$genre_index";
	if (!open(OUT,">$genreIndexFile")) { &error("データベース書き込みエラー<br>[$genreIndexFile]","設定ファイルの設定が間違っている可能性があります。"); }

	foreach $line (@GENREHTML) {
	
		$line =~ s/<!--title_include-->/$genreTitleText/g;
		$line =~ s/<!--update_time-->/$print_time/ig;
		
		if ($line =~ /<!--from-->/i) {

			foreach $data (@OUTHTML2) {
				print OUT "$data\n";
			}
			
		} else {
			print OUT $line;
		}
	}

	close(OUT);
	$ret = chmod(0666, "$genreIndexFile");

}


sub new_html_out {

	if (!($new_html)) {
		return;
	}

	open(NEW, $column_file) || &error("ファイル読込エラー<br>[$column_file]","ファイルが開けません。");
	@NEW = <NEW>;
	close(NEW);
	
	$new_index = "$site_path/$in{'genre'}/$new_html";
	
	if (!open(HTML,">$new_index ")) { &error("ファイル書き込みエラー <br>[$new_index]","設定ファイルの設定が間違っている可能性があります。"); }
	print HTML @NEW;
	close(HTML);
	$ret = chmod(0666, "$new_index");
	
}

sub date_check ($) {

	my $date_check = shift;

    $date_check =~ s/\Q－\E/./g;
    $date_check =~ s/\Qー\E/./g;
    $date_check =~ s/．/./g;
    $date_check =~ s/０/0/g;
    $date_check =~ s/１/1/g;
    $date_check =~ s/２/2/g;
    $date_check =~ s/３/3/g;
    $date_check =~ s/４/4/g;
    $date_check =~ s/５/5/g;
    $date_check =~ s/６/6/g;
    $date_check =~ s/７/7/g;
    $date_check =~ s/８/8/g;
    $date_check =~ s/９/9/g;
	$date_check =~ s/\Q／\E/./g;
	$date_check =~ s/-/./g;
	$date_check =~ s/\//./g;
	$date_check =~ s/ /./g;
	
	my ($year,$month,$day) = split(/\./,$date_check);
	
	my ($day,$plus) = split(/\+/,$day);
	if ($plus =~ /^\d+$/) {
		$day = $day + $plus;
	}
	
	if ($year =~ /^\+(\d+)$/) {
		$year = $now_day + $1;
	}

	if (!($month)) {
		if ($year =~ /^\d+$/) {
	
			$inputLength = length($year); 
				
			if ($inputLength eq 4) {
				$day = substr($year,2,2);
				$month = substr($year,0,2);
				$year = $now_year;
			} elsif ($inputLength eq 6) {
				$day = substr($year,4,2);
				$month = substr($year,2,2);
				$year = "20" .substr($year,0,2);
			} elsif ($inputLength eq 8) {
				$day = substr($year,6,2);
				$month = substr($year,4,2);
				$year = substr($year,0,4);
			} else {
				$day = $year;
				$month = $now_month;
				$year = $now_year;
			}
			
			$month = $month + 0;
			if ($month > 12 || $month eq 0) {
				$day = $now_day;
				$month = $now_month;
				$year = $now_year;
			}
			
		} else {
				$day = $now_day;
				$month = $now_month;
				$year = $now_year;
		}
	}
	
	$month = $month + 0;
	$day = $day + 0;
	
	# 日だけの入力の場合
	if (!($month)) {
		$day = $year;	
		$month = $now_month;
		$year = $now_year;
	}
	
	# 月日だけの入力の場合
	if (!($day)) {
		$day = $month;	
		$month = $year;
		$year = $now_year;
	}

	my $lastDay = &mday($month,$year);

	while ($lastDay < $day) {
		
		# 月末の日を知る
		my $lastDay = &mday($month,$year);
		
		if ($lastDay < $day) {
			$month++;
			$day = $day - $lastDay;
			if ($month eq 13) {
				$year++;
				$month = 1;
			}
		}
	}
	
	if ($year < 100) { $year = $year + 2000; }
	
	my $returnDate = sprintf("%04d.%02d.%02d",$year,$month,$day);
	
	return $returnDate;

}

sub mday ($;$) {

	my ($month,$year) = @_;
	@days = (31,28,31,30,31,30,31,31,30,31,30,31);
	
	if ($month == 2 && leapyear($year)) {
		return 29;
	} else {
		return $days[$month -1];
	}	
}

sub leapyear ($) {
	my $year = shift;
	return ((($year % 4 == 0) && ($year % 100 != 0) || ($year % 400 == 0)) ? 1 : '');
}

sub rebuildCheck {

#	print "Content-type: text/html\n\n";
#	print "rebuildCheck<hr>";

	$convertFile = 0;
	$noConvertFile = 0;

	foreach $genre_data (@GENRE) {
		
		if ($genre_data eq $secret) {
			next;
		}
#		print "GENRE:".$genre_data . "<br>";
		&file_read2;

		foreach (@files2) {
			chomp $_;
			($meta_time,$data_file,$title_data,$update_ng) = split(/\;;/,$_);

#			print "　".$site_path."/".$genre_data."/".$data_file."<br>";
			$rebuildFile = $site_path."/".$genre_data."/".$data_file;
			
			if ($update_ng) {
				if ($in{'action'} eq "rebuildGo") {
					&rebuildChange($rebuildFile,$genre_data,$meta_time,$title_data);
				}
				$convertFile++;
			} else {
#				print "not update : " . $rebuildFile ."<br>";
				$linkData = "<a href=\"$www_server/$genre_data/$data_file\">$title_data</a>";
				push(@noConvert , $linkData);
				$noConvertFile++;
			}
			
		}
	}
	
#	exit;
}

sub rebuildChange {

	my($rebuildFile,$genre_data,$meta_time,$title_data) = @_;

	open(REBUILDFILE, $rebuildFile) || &error("ファイル読込エラー<br>[$rebuildFile]","データファイルが開けません。");
	@REBUILDFILE = <REBUILDFILE>;
	close(REBUILDFILE);

	undef @DATA;

	foreach $line (@REBUILDFILE) {

		if ($line =~ /<!--from-->/i) {
			$print_sw = 1;
		} elsif ($line =~ /<!--to-->/i) {
			$print_sw = 2;
		}

		if ($print_sw eq 0) {

			#更新日時を取得
			if ($line =~ /<meta name=\"update-time\" content=\"(.*)\">/i ) { $meta_time = $1; }
			#タイトルを取得
			if ($line =~ /<title>(.*)<\/title>/i ) { $title = $1; $titleName = $1; }
			#とりあえず著者情報取得
			if ($line =~ /<meta name=\"author\" content=\"(.*)\">/i ) { $author = $1; }

		} elsif ($print_sw eq 1) {

			$line =~ s/\n//g;
			if ($line eq "") { 
				next; 
			} elsif ($line =~ /<!--from-->/i) { 
				next;
			} elsif ($line =~ /class=title/i) { 
				next;
			} else { push(@DATA,$line); }
		}
		
	}

	$temp_check = "$site_path/$genre_data/$template_file2";
	if  (!(-e $temp_check)) {
		$temp_check =  $template_file2;
	}
	
	open(TEMPFILE2, $temp_check) || &error("ファイル読込エラー<br>[$temp_check]", "テンプレートファイルが開けません。<br>上記の場所にファイルがあるか確認してください。");
	@TEMPLATE2 = <TEMPFILE2>;
	close(TEMPFILE2);

	if (length($meta_time) eq 14) {
		$year = substr($meta_time,0,4);
		$month = substr($meta_time,4,2);
		$day = substr($meta_time,6,2);
		$hour = substr($meta_time,8,2);
		$min = substr($meta_time,10,2);
		$sec = substr($meta_time,12,2);
	} else {
		($sec,$min,$hour,$mday,$mon,$year,$wday,$yday,$isdst) = localtime($meta_time);
		$year = $year + 1900;
		$month = $mon + 1;
	}

	$meta_updatetime = "<meta name=\"update-time\" content=\"$year$month$day$hour$min$sec\">";
	$print_time = &date_time_print("$year$month$day$hour$min$sec");

	open (OUT,">$rebuildFile");

	foreach $line (@TEMPLATE2) {


		if ($genreTitlePrint eq 1) {
			$line =~ s/<!--genreTitle-->/$GENRE_TABLE{$genre_data}/ig;
		}
	
		$line =~ s/<!--title_include-->/$title_data/ig;
		$line =~ s/<!--update_time-->/$print_time/ig;
		
		if ($input_author eq 1) {
			$line =~ s/<!--writer_include-->/$writer/ig;
			$line =~ s/<\/head>/$author\n<\/head>/ig;
		}
		
		if ($generator_check eq 1) {
			$line =~ s/<\/head>/$meta_generator\n<\/head>/ig;
		}
		
		$line =~ s/<\/head>/$meta_updatetime\n<\/head>/ig;
		
		if ($line =~ /<!--from-->/i) {
			$ato_print = $'; 
			print OUT $`;
			print OUT "<!--from-->\n";
			if ($title_ichi ne 1) { 
				print OUT "<$title_tag class=title>$in{'title'}</$title_tag>\n";
			}
			$i = 0;
			$up_photo = $now_time - 1;
			
			foreach $p_data (@DATA) {
			
				print OUT $p_data."\n";
			}
			
			$ato_print =~ s/\n//g; 
			$ato_print =~ s/\r//g; 
			print OUT $ato_print;
		} else {
			print OUT $line;
		}
	}

	close(OUT);
}

sub date_format {

	my ($yearF,$monthF,$dayF,$yobiF,$hhF,$mmF,$ssF,$formatF) = @_;

	@monthFullArray = ("January","February","March","April","May","June","July","August","September","October","November","December");
	@monthArray = ("Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec");
	@yobiFullArrayE = ("Sunday","Monday","Tuesday","Wednesday","Thursday","Friday","Saturday");
	@yobiArrayE = ("Sun","Mon","Tue","Wed","Thu","Fri","Sat");
	@yobiArrayJ = ("日","月","火","水","木","金","土"); 

	$yearF = sprintf("%04d",$yearF);
	$formatF =~ s/YYYY/$yearF/g;
	$yearF = substr($yearF,2,2);
	$formatF =~ s/YY/$yearF/g;

	$dayF = sprintf("%02d",$dayF);
	$formatF =~ s/DD/$dayF/g;
	$dayF = $dayF + 0;
	$formatF =~ s/Dn/$dayF/g;

	$monthF = sprintf("%02d",$monthF);
	$formatF =~ s/MM/$monthF/g;
	$monthF = $monthF + 0;
	$formatF =~ s/Mn/$monthF/g;
	$formatF =~ s/MONTH/$monthFullArray[$monthF - 1]/g;
	$formatF =~ s/M3/$monthArray[$monthF - 1]/g;
	
	$formatF =~ s/WF/$yobiFullArrayE[$yobiF]/g;
	$formatF =~ s/W3/$yobiArrayE[$yobiF]/g;
	$formatF =~ s/YOBI/$yobiArrayJ[$yobiF]/g;

	$formatF =~ s/JJ/$hhF/g;
	$formatF =~ s/FF/$mmF/g;
	$formatF =~ s/BB/$ssF/g;

	return  $formatF;
}
