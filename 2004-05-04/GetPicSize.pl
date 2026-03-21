#############################################################################
#
# 画像のサイズ(幅と高さ)を取得するサブルーチン
#
#                    2001-2003 Copyright (C) cachu <cachu@cocoa.ocn.ne.jp>
#
#  使い方:
#
#      ( $format, $width, $height ) =  &GetImageSize( $FileName, [$out] );
#
#            $format : 画像フォーマット
#             $width : 幅
#            $height : 高さ
#          $FileName : 画像ファイル名
#               $out : ファイルハンドル(省略可)
#
#
#      ファイル名を引数として渡すと画像フォーマット、幅、高さの情報を
#   返します。画像フォーマットの値は
#
#       'JPEG'       … JFIF フォーマットの JPEG 形式
#       'EXIF-JPEG'  … Exif フォーマットの JPEG 形式
#       'EXIF-TIFF'  … Exif フォーマットの TIFF 形式
#       'PNG'        … PNG 形式
#       'GIF'        … GIF 形式
#       'BMP'        … Windows ビットマップ形式
#       'TIFF'       … TIFF 形式
#       'PBM'        … PBM 形式
#       'PGM'        … PGM 形式
#       'PPM'        … PPM 形式
#       'TGA'        … TGA 形式
#
#   となります。 Exif フォーマットの JPEG 画像(デジカメの画像)には
#   さまざまな情報が記録されています。その内容を表示したい場合には
#   ExifInfo.pl をご利用下さい。
#
#
#   2003/05/27 現在対応済画像フォーマット:
#       - GIF
#       - Windows Bit Map
#       - JPEG (JFIF)
#       - JPEG (Exif)
#       - TIFF
#       - TIFF (Exif)
#       - PNG
#       - PPM/PGM/PBM
#       - TGA
#
#   更新履歴
#      
#      ・2003/08/22 - 某サイトで取得できないというものに対応してみた
#                         + 試しですので採用するかどうかはまだ分かりません
#      ・2003/07/13 - Exif 形式の TIFF 画像の処理を追加
#      ・2003/05/27 - バグ修正
#      ・2003/03/27 - Exif 情報に関しては独立して別サブルーチン化した
#      ・2003/01/06 - 引数の調整
#      ・2002/12/15 - Exif 情報を返すようにした
#                         + まだ不完全(Olympus C-2 ZOOM で使われている
#                           タグしか処理していません)
#      ・2002/07/17 - PGM/PBM, TGA 形式に対応 (TGA 形式はちょっとあやしい…)
#      ・2002/07/04 - Exif 形式データ取得に関するバグ修正
#      ・2002/06/05 - Exif 形式データ取得に関するバグ修正
#                   - 読み込みをファイルハンドルからファイル名に修正
#      ・2001/12/14 - 初期バージョン
#
sub GetImageSize{
    my ( $IMG, $in ) = @_;
    my ( %SHT, %LNG );
    my ( $buf, $mark, $type, $f_size, $width, $height );
    my ( $TAG, $TYPE, $COUNT, $V_OFFSET, $PK, $ENTRY, $Exif_IFD );
    my ( $endian, $dummy1, $dummy2, $dummy, $EOI, $APP1, $length, $exif );
    my ( $format, $offset, $line, $CODE );
    my @TGA;
    my $ntag;

    # 定数
    $mark = pack("C", 0xff);
    %SHT = ( 'II' => 'v', 'MM' => 'n' );
    %LNG = ( 'II' => 'V', 'MM' => 'N' );

    # 初期値
    $endian   = '';
    $width    = -1;
    $height   = -1;
    $format   = '';
    $Exif_IFD = -1;

    if( $in eq '' ){
	$in = 'IMG';
    }

    open( $in, $IMG ) || return( '', -1, -1 );

    binmode($in);
    seek( $in, 0, 0 );
    read( $in, $buf, 6 );

    # GIF 形式
    if($buf =~ /^GIF/i){
	$format = 'GIF';
	read( $in, $buf, 2 );
	$width  = unpack("v*", $buf);
	read( $in, $buf, 2);
	$height = unpack("v*", $buf);

    # Windows Bit Map 形式
    }elsif($buf =~ /BM/){
	$format = 'BMP';
	seek( $in, 12, 1 );
	read( $in, $buf, 8 );
	($width, $height) = unpack("VV", $buf);

    # TIFF 形式
    }elsif( $buf =~ /(II)/ || $buf =~ /(MM)/ ){
	$format = 'TIFF';
	$endian = $1;
	seek( $in, 0, 0 );
	read( $in, $buf, 8 );
	( $endian, $dummy1, $offset ) = 
	    unpack( "A2$SHT{$endian}$LNG{$endian}", $buf );

	seek( $in, $offset, 0 );
	read( $in, $buf, 2 );
	$ENTRY = unpack( $SHT{$endian}, $buf );

	for( $i = 0 ; $i < $ENTRY ; $i++ ){
	    read( $in, $buf, 8 );
	    $PK = "$SHT{$endian}$SHT{$endian}$LNG{$endian}";
	    ( $TAG, $TYPE, $COUNT ) = unpack( $PK, $buf );

	    read( $in, $buf, 4 );
	    ( $TAG != 256 && $TAG != 257 ) and next;
	    if( $TYPE == 3 ){
		$PK = "$SHT{$endian}";
	    }elsif( $TYPE == 4 ){
		$PK = "$LNG{$endian}";
	    }else{
		next;
	    }

	    $V_OFFSET = unpack( $PK, $buf );

	    # Image width and height
	    ( $TAG == 256   ) and ( $width  = $V_OFFSET   );
	    ( $TAG == 257   ) and ( $height = $V_OFFSET   );
	    ( $TAG == 34665 ) and ( $format = 'EXIF-TIFF' );
	}

    # PPM 形式
    }elsif( $buf =~ /^(P[123456])\n/ ){
	if( $1 eq 'P1' || $1 eq 'P4' ){
	    $format = 'PBM';
	}elsif( $1 eq 'P2' || $1 eq 'P5' ){
	    $format = 'PGM';
	}else{
	    $format = 'PPM';
	}
	seek( $in, 0, 0 );
	<$in>;
	while( <$in> ){
	    next if ( /^\#/ );
	    chomp;
	    ( $width, $height ) = split( /\s+/, $_ );
	    last;
	}

    # PNG 形式
    }elsif( $buf =~ /PNG/){
	$format = 'PNG';
	seek( $in, 8, 0 );

	while(1){
	    read( $in, $buf, 8 );
	    ( $offset, $CODE ) = unpack( "NA4", $buf );

	    if( $CODE eq 'IHDR' ){
		read( $in, $buf, 8 );
		( $width, $height ) = unpack( "NN", $buf );
		seek( $in, $offset-8+4, 1 );
		last;

	    }elsif( $CODE eq 'IEND' ){
		last;

	    }else{
		seek( $in, $offset+4, 1 );
	    }
	}

    # JFIF 形式の JPEG
    }elsif(read( $in, $buf, 4 ) && $buf eq 'JFIF'){
	$format = 'JPEG';
      JPEG:while(read( $in, $buf, 1 )){
	  if(($buf eq $mark) && read( $in, $buf, 3 )){
	      $type   = unpack("C*", substr($buf, 0, 1));
	      $f_size = unpack("n*", substr($buf, 1, 2));
	      read( $in, $buf, $f_size-2 );

	      if($type == 0xC0 || $type == 0xC2){
		  $height = unpack("n*", substr($buf, 1, 2));
		  $width  = unpack("n*", substr($buf, 3, 2));
		  last JPEG;
	      }
	  }
      }

    }else{
	# JPEG ?
	seek( $in, 0, 0 );
	read( $in, $buf, 2 );
	( $buf, $type ) = unpack("C*", $buf );
	if( $buf == 0xFF && $type == 0xD8 ){
	    $format = 'JPEG';
	  JPEG2:while(read( $in, $buf, 1 )){
	      if(($buf eq $mark) && read( $in, $buf, 3 )){
		  $type   = unpack("C*", substr($buf, 0, 1));
		  $f_size = unpack("n*", substr($buf, 1, 2));
		  read( $in, $buf, $f_size-2 );

		  if($type == 0xC0 || $type == 0xC2){
		      $height = unpack("n*", substr($buf, 1, 2));
		      $width  = unpack("n*", substr($buf, 3, 2));
		      last JPEG2;
		  }
	      }
	  }
	}

	if( $width > 0 && $height > 0 ){
	    close( $in );
	    return( $format, $width, $height );
	}

	# Exif 形式 JPEG
	seek( $in, 0, 0 );
	read( $in, $buf, 12 );
	$ntag = 0;
	( $EOI, $APP1, $length, $exif, $dummy ) = unpack( "H4H4nA4A2", $buf );
	if($exif eq 'Exif'){
	    $format = 'EXIF-JPEG';
	    read( $in, $buf, 8 );
	    ( $endian, $dummy1, $dummy2 ) = unpack( "A2H2H4", $buf );

	    read( $in, $buf, 2 );
	    $ENTRY = unpack( $SHT{$endian}, $buf );

	    for( $i = 0 ; $i < $ENTRY ; $i++ ){
		read( $in, $buf, 8 );
		$PK = "$SHT{$endian}$SHT{$endian}$LNG{$endian}";
		( $TAG, $TYPE, $COUNT ) = unpack( $PK, $buf );

		read( $in, $buf, 4 );
		if( $TYPE == 3 ){
		    $PK = "$SHT{$endian}";
		}elsif( $TYPE == 4 ){
		    $PK = "$LNG{$endian}";
		}else{
#		    $PK = "A*";
		    $PK = "$LNG{$endian}";
		}

		# Unpack following data
		#  [34665] Exif IDF Pointer
		#  [40962] Image Width
		#  [40963] Image Height
		if( $TYPE == 7 ){
		    $V_OFFSET = $buf;
		}else{
		    ( $V_OFFSET ) = unpack( $PK, $buf );
		}
		if( $TAG == 34665 || $TAG == 40962 || $TAG == 40963 ){
		    ( $TAG == 34665 ) and ( $Exif_IFD = $V_OFFSET + 12 );
		    ( $TAG == 40962 ) and ( $width    = $V_OFFSET      );
		    ( $TAG == 40963 ) and ( $height   = $V_OFFSET      );
		}

	    }

	    if( $width > 0 && $height > 0 ){
		close( $in );
		return( $format, $width, $height );
	    }

	    if( $Exif_IFD > 0 ){
		seek( $in, $Exif_IFD, 0 );
		read( $in, $buf, 2 );
		$ENTRY = unpack( $SHT{$endian}, $buf );
		for( $i = 0 ; $i < $ENTRY ; $i++ ){
		    read( $in, $buf, 4 );
		    $PK = "$SHT{$endian}$SHT{$endian}";
		    ( $TAG, $TYPE ) = unpack( $PK, $buf );

		    read( $in, $buf, 4 );
		    $COUNT = unpack( $LNG{$endian}, $buf );

		    read( $in, $buf, 4 );
		    if( $TYPE == 7 ){
			$V_OFFSET = $buf;
		    }elsif( $TYPE == 3 ){
			$PK = "$SHT{$endian}$SHT{$endian}";
			( $V_OFFSET, $dummy1 ) = unpack( $PK, $buf );
		    }else{
			$PK = "$LNG{$endian}";
			( $V_OFFSET ) = unpack( $PK, $buf );
		    }
		    
		    # Image width and height
		    ( $TAG == 40962 ) and ( $width  = $V_OFFSET );
		    ( $TAG == 40963 ) and ( $height = $V_OFFSET );
		}
	    }
	}

	if( $width > 0 && $height > 0 ){
	    close( $in );
	    return( $format, $width, $height );
	}

	# TGA 形式
	seek( $in, 0, 0 );
	read( $in, $buf, 18 );
	@TGA = unpack( "CCCvvCvvvvCC", $buf );
	if( $TGA[1] == 0 || $TGA[1] == 1 ){
	    if( $TGA[2] ==  0 || $TGA[2] == 1 || $TGA[2] ==  2 ||
		$TGA[2] ==  3 || $TGA[2] == 9 || $TGA[2] == 10 ||
		$TGA[1] == 11 ){
		$format = 'TGA';
		$width  = $TGA[8];
		$height = $TGA[9];
	    }
	}

    }

    close( $in );
    return( $format, $width, $height );
}

1;
