#!/usr/bin/perl
use Mail::IMAPClient;
use strict;
my $user = shift;

my $passwd=`grep de.cranix.dao.User.Register.Password= /opt/cranix-java/conf/cranix-api.properties | /usr/bin/sed 's/de.cranix.dao.User.Register.Password=//'`;
chomp $passwd;
my $imap = Mail::IMAPClient->new(
  Server   => 'localhost',
  User     => 'register',
  Password => $passwd,
  Ssl      => 0,
  Uid      => 1,
);

print $imap->quota_usage("user".$imap->separator.$user)." ";
print $imap->quota("user".$imap->separator.$user)."\n";

