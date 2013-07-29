#! /usr/bin/perl

use strict;
use warnings;
use utf8;

use Net::Twitter::Lite::WithAPIv1_1;
use Mojolicious::Lite;

my $consumer_key ="***";
my $consumer_secret = "***";

my $nt = Net::Twitter::Lite::WithAPIv1_1->new(

	consumer_key => $consumer_key,
	consumer_secret => $consumer_secret
);

get '/auth_cb' => sub {
	my $self = shift;
	my $verifier = $self->param('oauth_verifier') || '';
	my $token = $self->session('token') || '';
	my $token_secret = $self->session('token_secret') || '';

	$nt->request_token( $token );
	$nt->request_token_secret( $token_secret );

	# Access token取得
	my ($access_token, $access_token_secret, $user_id, $screen_name)
	= $nt->request_access_token( verifier => $verifier );

	# Sessionに格納
	$self->session( access_token => $access_token );
	$self->session( access_token_secret => $access_token_secret );
	$self->session( screen_name => $screen_name );

	$self->redirect_to( 'index' );
} => 'auth_cb';

get '/auth' => sub {
	my $self = shift;
	my $cb_url = 'http://retrorocket.biz/fav/fav.cgi/auth_cb';
	my $url = $nt->get_authorization_url( callback => $cb_url );

	$self->session( token => $nt->request_token );
	$self->session( token_secret => $nt->request_token_secret );

	$self->redirect_to( $url );
} => 'auth';

# Session削除
get '/logout' => sub {
	my $self = shift;
	$self->session( expires => 1 );
	#$self->render;
} => 'logout';

get '/' => sub {
	my $self = shift;
	my $access_token = $self->session( 'access_token' ) || '';
	my $access_token_secret = $self->session( 'access_token_secret' ) || '';
	my $screen_name = $self->session( 'screen_name' ) || '';

	# セッションにaccess_token/access_token_secretが残ってなければ認証処理へ
	return $self->redirect_to( 'auth' ) unless ($access_token && $access_token_secret);

} => 'index';


# Index
post '/fav' => sub {

	my $self = shift;
	my $access_token = $self->session( 'access_token' ) || '';
	my $access_token_secret = $self->session( 'access_token_secret' ) || '';
	my $screen_name = $self->session( 'screen_name' ) || '';

	# セッションにaccess_token/access_token_secretが残ってなければ認証処理へ
	return  $self->render_json({'error' => "Not Authorized"}) unless ($access_token && $access_token_secret);

	$nt->access_token( $access_token );
	$nt->access_token_secret( $access_token_secret );

	##### スコア計算 #####

	my %score=();

	my $favs = $nt->favorites({count => 200});
	my $j = @$favs;

	if ($j == 0){
		$self->session( expires => 1 );
		return $self->render_json({'error' => "You have no favs."});
	}

	foreach my $hash (@$favs){
		my $user_name = $hash->{user}{screen_name};
		$score{$user_name}++;
		#$j++;
	}

	my $i = 0;
	my $top_user;
	my $second;
	my $third;

	foreach(sort {$score{$b} <=> $score{$a}} keys %score) { #連想配列の値が大きい順にソート
		if ($i == 0) { $top_user = $_; }
		elsif ($i == 1) { $second = $_; }
		else  { $third = $_; }
		$i++;
		if ( $i == 3 ) { last; }
	}

##### 結果出力 #####

	my $top = $nt->show_user({screen_name=>$top_user});
	my $uri = $top->{profile_image_url};
	my %first_list=('name' => $top_user, 'img' => $uri, 'score' => $score{$top_user}+0);
	my %list=();
	$list{'first'}=\%first_list;

	if (defined $second) {

		$top = $nt->show_user({screen_name=>$second});
		my $uri2 = $top->{profile_image_url};
		my %second_list=('name' => $second, 'img' => $uri2, 'score' => $score{$second}+0);
		$list{'second'}=\%second_list;
	}

	if (defined $third) {

		$top = $nt->show_user({screen_name=>$third});
		my $uri3 = $top->{profile_image_url};
		my %third_list=('name' => $third, 'img' => $uri3, 'score' => $score{$third}+0);
		$list{'third'}=\%third_list;

	}
	$list{'screen'} =$screen_name;
	$list{'tortal'} =$j+0;
	$self->session( expires => 1 );
	$self->render_json(\%list);

} => 'fav';

app->secret("morimoriunco"); # セッション管理のために付けておく
app->start;

