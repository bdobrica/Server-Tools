#!/usr/bin/perl
#
# vhostcfg script
#
use strict;
use DBI;
#
# one function =)
#
sub extract_zone {
	my @fqdn = split ('\.',$_[0]);
	return $fqdn[$#fqdn-1].".".$fqdn[$#fqdn];
	}
#
# reading config
#
open(FILE,"/etc/conf.d/gemini");
my %config = ();
while (<FILE>) {
	next if m/^\s*#/;	# commented lines
	next if m/^\s*\n/;	# blank lines
	$_ =~ s/\s#.*$//;	# remove comments
	if (/^\s*(\w+)\s*=\s*(.*)\s*\n/) {
		$config{$1}="$2";
		}
	}
close(FILE);

my $HT_NAME = $config{'HT_NAME'};
my $DB_NAME = $config{'DB_NAME'};
my $DB_USER = $config{'DB_USER'};
my $DB_PASS = $config{'DB_PASS'};
my $WEB_UID = $config{'WEB_UID'};
my $WEB_GID = $config{'WEB_GID'};
my $T_HOSTS = $config{'T_HOSTS'};
my $ETC_DIR = $config{'NGNXDIR'};
my $LOG_DIR = $config{'NGNXLOG'};
my $SPAWNCF = $config{'SPAWNCF'};
my $WEB_DIR = $config{'WEB_DIR'};
my $AWS_DIR = $config{'AWS_DIR'};
my $AWSTATS = $config{'AWSTATS'};
my $STATICC = "gif|png|ico|css|js";
#
# checking auxilliary directory
#
unless (-e "$WEB_DIR" && -d "$WEB_DIR") {
	mkdir ("$WEB_DIR",0775);
	chown $WEB_UID,$WEB_GID,$WEB_DIR;
	}
#
# environment settings
#
my $IS_CLUSTER = 0;
my $IS_REWRITE = 0;
my $FAST_USERS = '';
my $FAST_GROUP = '';
my $FAST_CROOT = '';

my $db = DBI->connect ("DBI:mysql:$DB_NAME:localhost",$DB_USER,$DB_PASS) || die "Error: Database connection failed!";

my $q = $db->prepare ("desc $T_HOSTS;");
$q->execute();
while (my $r = $q->fetchrow_hashref()) {
	$IS_CLUSTER = 1 if ($r->{'Field'} eq 'nodes');
	$IS_REWRITE = 1 if ($r->{'Field'} eq 'nginxrw');
	}

$q = $db->prepare ("select lpad(id,6,'0') pid,server,alias,".($IS_REWRITE?'nginxrw':'rewrite')." as genrw,options,overide,stats,uid,gid from $T_HOSTS".($IS_CLUSTER?" where nodes like '%$HT_NAME%'":'')." order by id;");
$q->execute();

open (MOUT,'>'.$ETC_DIR.'/nginx.conf');
print MOUT "user\t\t\twebsrv websrv;\n";
print MOUT "worker_processes\t8;\n";
#print MOUT "keepalive_requests\t0;\n";
#print MOUT "keepalive_timeout\t30;\n";

#print MOUT "error_log\t\t$LOG_DIR/error_log;\n";
print MOUT "error_log\t\t/dev/null;\n";
#print MOUT "pid\t\t\t$LOG_DIR/nginx.pid;\n";

print MOUT "\n";

print MOUT "events {\n";
print MOUT "\tworker_connections\t4096;\n";
print MOUT "\t}\n";

print MOUT "\n";

print MOUT "http {\n";
print MOUT "\tlog_format main '\$remote_addr - \$remote_user [\$time_local] \$status '\n";
print MOUT "\t\t'\"\$request\" \$body_bytes_sent \"\$http_referer\" '\n";
print MOUT "\t\t'\"\$http_user_agent\" \"\$http_x_forwarded_for\"';\n";
print MOUT "\t\tclient_max_body_size 224M;\n";
print MOUT "\t\tclient_body_buffer_size 512k;\n";
print MOUT "\n";
print MOUT "\t\tserver_names_hash_bucket_size 128;\n";
print MOUT "\n";
print MOUT "\t\tinclude /etc/nginx/mime.types;\n";
print MOUT "\t\tdefault_type application/octet-stream;\n";
print MOUT "\n";
my $fcgiproc = 1;
while (my $r = $q->fetchrow_hashref()) {
	print $r->{'server'}."\n";
	#
	# check vhost directory
	#
	my $zone = extract_zone($r->{'server'});
	my $sdir = $zone."/".$r->{'server'};
	if ($r->{'alias'} eq '') { $r->{'alias'} = 'www.'.$r->{'server'}; }

	unless (-e "$WEB_DIR/$zone" && -d "$WEB_DIR/$zone") {
		mkdir ("$WEB_DIR/$zone",0775);
		chown $WEB_UID,$WEB_GID,"$WEB_DIR/$zone";
		}
		
	unless (-e "$WEB_DIR/$sdir" && -d "$WEB_DIR/$sdir") {
		mkdir ("$WEB_DIR/$sdir",0775);
		chown $WEB_UID,$WEB_GID,"$WEB_DIR/$sdir";
		}
	
	if (-e "$WEB_DIR/$sdir/awstats" && -d "$WEB_DIR/$sdir/awstats") {
		rmdir ("$WEB_DIR/$sdir/awstats");
		}

	unless (-e "$WEB_DIR/$sdir/erp" && -d "$WEB_DIR/$sdir/erp") {
                mkdir ("$WEB_DIR/$sdir/erp",0775);
                chown $WEB_UID,$WEB_GID,"$WEB_DIR/$sdir/erp";
                }

	unless (-e "$WEB_DIR/$sdir/erp/401.html") {
                open (EOUT,">$WEB_DIR/$sdir/erp/401.html");
                print EOUT '<?xml version="1.0" encoding="UTF-8"?>'."\n";
                print EOUT '<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"'."\n";
                print EOUT "\t".'"http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">'."\n";
                print EOUT '<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en">'."\n";
                print EOUT "\t<head>\n";
                print EOUT "\t\t<title>401: Authorization required!</title>\n";
                print EOUT "\t</head>\n";
                print EOUT "\t<body>\n";
                print EOUT "\t</body>\n";
                print EOUT "\t</html>";
                close EOUT;
                }

	unless (-e "$WEB_DIR/$sdir/erp/404.html") {
                open (EOUT,">$WEB_DIR/$sdir/erp/404.html");
                print EOUT '<?xml version="1.0" encoding="UTF-8"?>'."\n";
                print EOUT '<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"'."\n";
                print EOUT "\t".'"http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">'."\n";
                print EOUT '<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en">'."\n";
                print EOUT "\t<head>\n";
                print EOUT "\t\t<title>404: Page not found!</title>\n";
                print EOUT "\t</head>\n";
                print EOUT "\t<body>\n";
                print EOUT "\t</body>\n";
                print EOUT "\t</html>";
                close EOUT;
                }

        unless (-e "$WEB_DIR/$sdir/erp/500.html") {
                open (EOUT,">$WEB_DIR/$sdir/erp/500.html");
                print EOUT '<?xml version="1.0" encoding="UTF-8"?>'."\n";
                print EOUT '<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"'."\n";
                print EOUT "\t".'"http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">'."\n";
                print EOUT '<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en">'."\n";
                print EOUT "\t<head>\n";
                print EOUT "\t\t<title>500: Bad Gateway!</title>\n";
                print EOUT "\t</head>\n";
                print EOUT "\t<body>\n";
                print EOUT "\t</body>\n";
                print EOUT "\t</html>";
                close EOUT;
                }		
	
	#exec ("chown -R $r->{'uid'}:$r->{'gid'} $WEB_DIR/$sdir");
	
	$FAST_USERS .= `cat /etc/passwd | grep ":x:$r->{'uid'}" | awk -F ':' '{print(\$1);}'`;
	chop($FAST_USERS); $FAST_USERS .= ' ';
	$FAST_GROUP .= `cat /etc/group  | grep   ":$r->{'gid'}" | awk -F ':' '{print(\$1);}'`;
	chop($FAST_GROUP); $FAST_GROUP .= ' ';
	$FAST_CROOT .= "$WEB_DIR/$sdir ";
	
	print MOUT "\tserver {\n";
	print MOUT "\t\tlisten\t\t80;\n";
	print MOUT "\t\tserver_name\t".$r->{'server'}." ".$r->{'alias'}.";\n";
	print MOUT "\t\taccess_log\t$LOG_DIR/".$r->{'server'}.".log main;\n";
	print MOUT "\t\troot\t$WEB_DIR/$sdir;\n";

	print MOUT "\n";

	print MOUT "\t\tlocation / {\n";
	print MOUT "\t\t\tindex\tindex.php;\n";

	my $staticc = "$STATICC|jpg|jpeg|html|htm";
	if ($r->{'genrw'} eq "[wp]") {
		print MOUT "\n";
		print MOUT "\t\t\tif (-f \$request_filename) {\n";
		print MOUT "\t\t\t\texpires 30d;\n";
		print MOUT "\t\t\t\tbreak;\n";
		print MOUT "\t\t\t\t}\n";
		print MOUT "\t\t\tif (!-e \$request_filename) {\n";
		print MOUT "\t\t\t\trewrite ^(.+)\$ /index.php?q=\$1;\n";
		print MOUT "\t\t\t\t}\n";
		print MOUT "\n";
		}
	else {
		if ($r->{'genrw'} =~ m/\[wp:html\]/) {
			print MOUT "\n";
			print MOUT "\t\t\tif (-f \$request_filename) {\n";
			print MOUT "\t\t\t\texpires 30d;\n";
			print MOUT "\t\t\t\tbreak;\n";
			print MOUT "\t\t\t\t}\n";
			print MOUT "\t\t\tif (!-e \$request_filename) {\n";
			print MOUT "\t\t\t\trewrite ^(.+)\$ /index.php?q=\$1;\n";
			print MOUT "\t\t\t\t}\n";
			print MOUT "\n";
			$staticc = "$STATICC|jpg|jpeg";	
			}
		else {
			if ($r->{'genrw'} =~ m/\[wp:full\]/) {
				print MOUT "\n";
				print MOUT "\t\t\tif (-f \$request_filename) {\n";
				print MOUT "\t\t\t\texpires 30d;\n";
				print MOUT "\t\t\t\tbreak;\n";
				print MOUT "\t\t\t\t}\n";
				print MOUT "\t\t\tif (!-e \$request_filename) {\n";
				print MOUT "\t\t\t\trewrite ^(.+)\$ /index.php?q=\$1;\n";
				print MOUT "\t\t\t\t}\n";
				print MOUT "\n";
				$staticc = "$STATICC";
				}
			else {
				if ($r->{'genrw'} =~ m/\[wp:([A-z]+)\]/) {
					print MOUT "\n";
					print MOUT "\t\t\tif (-f \$request_filename) {\n";
					print MOUT "\t\t\t\texpires 30d;\n";
					print MOUT "\t\t\t\tbreak;\n";
					print MOUT "\t\t\t\t}\n";
					print MOUT "\t\t\tif (!-e \$request_filename) {\n";
					print MOUT "\t\t\t\trewrite ^/$1/(.+)\$ /$1/index.php?q=\$1;\n";
					print MOUT "\t\t\t\t}\n";
					print MOUT "\n";
					}
				}
			}
		}

	print MOUT "\t\t\t}\n";

	print MOUT "\n";

	print MOUT "\t\tlocation ~* ^.+\\.($staticc)\$ {\n";
	print MOUT "\t\t\taccess_log\toff;\n";
	print MOUT "\t\t\texpires\t\t30d;\n";
	print MOUT "\t\t\t}\n";

	print MOUT "\n";

	print MOUT "\t\tlocation ~ \\.php\$ {\n";
### EXTRA BUFFERS? ###	
#	print MOUT "\t\t\tfastcgi_buffers\t8\t32k;\n";
#	print MOUT "\t\t\tfastcgi_buffer_size\t32k;\n";
### EXTRA BUFFERS ###
	print MOUT "\t\t\tfastcgi_pass\t\t\tunix:/var/run/fastcgi.socket-$fcgiproc;\n";
	print MOUT "\t\t\tfastcgi_param\tGATEWAY_INTERFACE\tCGI/1.1;\n";
	print MOUT "\t\t\tfastcgi_param\tSERVER_SOFTWARE\t\tnginx;\n";
	print MOUT "\t\t\tfastcgi_param\tQUERY_STRING\t\t\$query_string;\n";
	print MOUT "\t\t\tfastcgi_param\tREQUEST_METHOD\t\t\$request_method;\n";
	print MOUT "\t\t\tfastcgi_param\tCONTENT_TYPE\t\t\$content_type;\n";
	print MOUT "\t\t\tfastcgi_param\tCONTENT_LENGTH\t\t\$content_length;\n";
	print MOUT "\t\t\tfastcgi_param\tSCRIPT_FILENAME\t\t$WEB_DIR/$sdir\$fastcgi_script_name;\n";
	print MOUT "\t\t\tfastcgi_param\tSCRIPT_NAME\t\t\$fastcgi_script_name;\n";
	print MOUT "\t\t\tfastcgi_param\tREQUEST_URI\t\t\$request_uri;\n";
	print MOUT "\t\t\tfastcgi_param\tDOCUMENT_URI\t\t\$document_uri;\n";
	print MOUT "\t\t\tfastcgi_param\tDOCUMENT_ROOT\t\t$WEB_DIR/$sdir;\n";
	print MOUT "\t\t\tfastcgi_param\tSERVER_PROTOCOL\t\t\$server_protocol;\n";
	print MOUT "\t\t\tfastcgi_param\tREMOTE_ADDR\t\t\$remote_addr;\n";
	print MOUT "\t\t\tfastcgi_param\tREMOTE_PORT\t\t\$remote_port;\n";
	print MOUT "\t\t\tfastcgi_param\tSERVER_ADDR\t\t\$server_addr;\n";
	print MOUT "\t\t\tfastcgi_param\tSERVER_PORT\t\t\$server_port;\n";
	print MOUT "\t\t\tfastcgi_param\tSERVER_NAME\t\t\$server_name;\n";
	print MOUT "\t\t\tfastcgi_param\tREDIRECT_STATUS\t\t200;\n";
	print MOUT "\t\t\tfastcgi_index\t\t\tindex.php;\n";
	#print MOUT "\t\t\tfastcgi_param\n";
	print MOUT "\t\t\tfastcgi_intercept_errors\ton;\n";
	print MOUT "\t\t\t}\n";

	print MOUT "\n";

	print MOUT "\t\tlocation ~ /\\.ht {\n";
	print MOUT "\t\t\tdeny\tall;\n";
	print MOUT "\t\t\t}\n";

	print MOUT "\t\t}\n";
	
	$fcgiproc++;
	}
print MOUT "\t}";
close MOUT;

open (SPAWN,$SPAWNCF);
open (MOUT,'>'.$SPAWNCF.'.php');
while (<SPAWN>) {
	next if m/^\s*#/;	# commented lines
	next if m/^\s*\n/;	# blank lines
	$_ = "FCGI_CHILDREN=".($fcgiproc-1)."\n" if (m/^FCGI_CHILDREN=/);
	#$_ = "PHP_FCGI_CHILDREN=".($fcgiproc-1)."\n" if (m/^PHP_FCGI_CHILDREN=/);
	$_ = "PHP_FCGI_CHILDREN=8\n" if (m/^PHP_FCGI_CHILDREN=/);
	print MOUT $_;
	}
$FAST_USERS =~ s/\s+$//;
$FAST_GROUP =~ s/\s+$//;
$FAST_CROOT =~ s/\s+$//;
print MOUT "FCGI_RUN_USER=($FAST_USERS)\n";
print MOUT "FCGI_RUN_GROUP=($FAST_GROUP)\n";
print MOUT "FCGI_RUN_CHROOT=($FAST_CROOT)\n";
close MOUT;
close SPAWN;

#print "FastCGI Children: ".($fcgiproc-1)."\n";

$q->finish();
$db->disconnect();

my $n = 3;
print "stopping php-cgi: ";
while ($n--) {
	sleep (1);
	print '.';
	system ("killall","-9","php-cgi");
	}
print "[ok]\n";

print "starting php-cgi: ";
$n = 3;
while ($n--) {
	sleep (1);
	print '.';
	}
print "[ok]\n";
system ("/etc/init.d/spaw-fcgi.php","start");
$n = 3;
print "stopping nginx: ";
while ($n--) {
	sleep (1);
	print '.';
	}
print "[ok]\n";
system ("/etc/init.d/nginx","stop");
$n = 3;
print "starting nginx: ";
while ($n--) {
	sleep (1);
	print '.';
	}
print "[ok]\n";
system ("/etc/init.d/nginx","start");


#system ("/etc/init.d/apache2","reload");
