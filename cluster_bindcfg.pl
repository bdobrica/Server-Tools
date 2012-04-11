#!/usr/bin/perl
#
# updating bind configuration
#
use strict;
use DBI;
use Socket;
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
#
# loading config vars
#
my $HT_NAME = $config{'HT_NAME'};
my $DB_NAME = $config{'DB_NAME'};
my $DB_USER = $config{'DB_USER'};
my $DB_PASS = $config{'DB_PASS'};
my $BINDUID = $config{'BINDUID'};
my $BINDGID = $config{'BINDGID'};
my $WEB_UID = $config{'WEB_UID'};
my $WEB_GID = $config{'WEB_GID'};
my $MAILUID = $config{'MAILUID'};
my $MAILGID = $config{'MAILGID'};
my $T_ZONES = $config{'T_ZONES'};
my $T_RECDS = $config{'T_RECDS'};
my $ETC_DIR = $config{'BINDDIR'};
my $WEB_DIR = $config{'WEB_DIR'};
#
# checking auxiliary directory
#
#unless (-e "$WEB_DIR" && -d "$WEB_DIR") {
#	mkdir ("$WEB_DIR",0775);
#	chown $WEB_UID,$WEB_GID,$WEB_DIR;
#	}
#
# updateing bind config files
#	
open (FILE,$ETC_DIR.'/named.conf.example');
open (MOUT,'>'.$ETC_DIR.'/named.conf');

while (my $line = <FILE>) {
	print MOUT $line;
	}
	
my $db = DBI->connect ("DBI:mysql:$DB_NAME:localhost",$DB_USER,$DB_PASS);

#my $q = $db->prepare ("update $T_ZONES set serial=(case left(serial,8) when date_format(now(),'%Y%m%d') then concat(left(serial,8),1+right(serial,1)) else concat(date_format(now(),'%Y%m%d'),1) end) where nodes like '%$HT_NAME%';");
my $q = $db->prepare ("update $T_ZONES set serial=(case left(serial,8) when date_format(now(),'%Y%m%d') then concat(left(serial,8),1) else concat(date_format(now(),'%Y%m%d'),1) end) where nodes like '%$HT_NAME%';");
$q->execute();
$q->finish();

$q = $db->prepare ("select * from $T_ZONES where nodes like '%$HT_NAME%' order by id;");
$q->execute();

while (my $r = $q->fetchrow_hashref()) {
	#
	# named.conf output
	#
#	unless (-e "$WEB_DIR/".$r->{'zone'} && -d "$WEB_DIR/".$r->{'zone'}) {
#		mkdir ("$WEB_DIR/".$r->{'zone'},0775);
#		chown $WEB_UID,$WEB_GID,"$WEB_DIR/".$r->{'zone'};
#		}
	print MOUT "zone \"".$r->{'zone'}."\" IN {\n";
	print MOUT "\ttype master;\n";
	print MOUT "\tfile \"$ETC_DIR/pri/".$r->{'zone'}.".zone\";\n";
	print MOUT "\tnotify no;\n";
	print MOUT "};\n\n";
	#
	# pri/zonename.zone output
	#
	open (SOUT,'>'.$ETC_DIR.'/pri/'.$r->{'zone'}.'.zone');
	print SOUT "\$TTL 3D\n";
	print SOUT "\$ORIGIN ".$r->{'zone'}.".\n";

	my @nsrv = split(/;/,$r->{'nameserver'});
	print SOUT "\@\tIN\tSOA\t".$nsrv[0].". ".$r->{'email'}.". (\n";
	print SOUT "\t\t\t".$r->{'serial'}."\n";
	print SOUT "\t\t\t".$r->{'refresh'}."\n";
	print SOUT "\t\t\t".$r->{'retry'}."\n";
	print SOUT "\t\t\t".$r->{'expire'}."\n";
	print SOUT "\t\t\t".$r->{'minimum'}." )\n";
	print SOUT ";\n";
	foreach (@nsrv) {
		print SOUT "\t\t\tNS\t\t".$_.".\n";
		}
#	print SOUT "\t\tIN\tMX 10\t\t$HT_NAME\n";
	print SOUT ";\n";

	my $qq = $db->prepare ("select * from $T_RECDS where zoneid=".$r->{'id'}." order by id;");
	$qq->execute();
	
	my $spec = '';
	while (my $rr = $qq->fetchrow_hashref()) {
		if ($rr->{'type'} eq 'GLUED') {
			$spec .= "; delegated sub-zone\n";
			$spec .= "\$ORIGIN ".$rr->{'name'}.".".$r->{'zone'}.".\n";
			my @dleg = split(/;/,$rr->{'value'});
			my $c = 0;
			my $glue = '';
			foreach (@dleg) {
				my $pip = gethostbyname($_);
				if (defined $pip) {
					my $gip = inet_ntoa($pip);
				
					$spec .= ($c++ == 0 ? "@" : "")."\t\t\tIN NS\t".$_.".\n";
					if (length($_)>7) {
						$glue .= $_.".\tA\t".$gip."\n";
						}
					else {
						$glue .= $_.".\t\tA\t".$gip."\n";
						}
					}
				}
			$spec .= $glue;
			}
		else {
			if ($rr->{'type'} eq 'IN TXT') {
				if (length($rr->{'name'})>7) {
					print SOUT $rr->{'name'}."\t".$rr->{'type'}."\t\t\"".$rr->{'value'}."\"\n";
					}
				else {
					print SOUT $rr->{'name'}."\t\t".$rr->{'type'}."\t\t\"".$rr->{'value'}."\"\n";
					}
				}
			else {
				if (length($rr->{'name'})>7) {
					print SOUT $rr->{'name'}."\t".$rr->{'type'}."\t\t".$rr->{'value'}."\n";
					}
				else {
					print SOUT $rr->{'name'}."\t\t".$rr->{'type'}."\t\t".$rr->{'value'}."\n";
					}
				}
			}
		}
	if ($spec) {
		print SOUT $spec;
		}
	
	$qq->finish();	
	close (SOUT);
	
	chmod 0644,$ETC_DIR.'/pri/'.$r->{'zone'}.'.zone';
	chown $BINDUID,$BINDGID,$ETC_DIR.'/pri/'.$r->{'zone'}.'.zone';
	}
	
$q->finish();
$db->disconnect();

close (MOUT);
close (FILE);
chmod 0775,$ETC_DIR.'pri';
chown $BINDUID,$BINDGID,$ETC_DIR.'pri';
chmod 0644,$ETC_DIR.'named.conf';
chown $BINDUID,$BINDGID,$ETC_DIR.'named.conf';

system ("/etc/init.d/bind9","restart");
