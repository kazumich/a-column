#!/usr/local/bin/perl
 
require './cgi-lib.pl';

#バッファ展開処理

&ReadParse();

$crypted = crypt ( $in{'pass'} , $in{'pass'} );

print "Content-type: text/html\n\n";

print <<"EOF";
<html><head><title>crypt</title></head>
<body bgcolor="#FFFFFF">
パスワードは8文字までです。
<form action="crypt.cgi" method="POST">
変換前<input type=text name=pass size=10 value="$in{'pass'}"><br>
変換後<input type=text name=crypt size=30 value="$crypted"><br>
<input type=submit value="変換">
</form>

</body></html>
EOF

exit;