#Captive portal configuration file

#Debian specific
<IfDefine debian>
  <IfModule !mod_perl.c>
    LoadModule perl_module /usr/lib/apache2/modules/mod_perl.so
  </IfModule>
  <IfModule !mod_log_config.c>
    LoadModule log_config_module /usr/lib/apache2/modules/mod_log_config.so
  </IfModule>
  <IfModule !mod_ssl.c>
    LoadModule ssl_module /usr/lib/apache2/modules/mod_ssl.so
  </IfModule>
  <IfModule !mod_headers.c>
    LoadModule headers_module /usr/lib/apache2/modules/mod_headers.so
  </IfModule>
  <IfModule !mod_proxy.c>
    LoadModule proxy_module /usr/lib/apache2/modules/mod_proxy.so
  </IfModule>
  <IfModule !proxy_http.c>
    LoadModule proxy_http_module /usr/lib/apache2/modules/mod_proxy_http.so
  </IfModule>
  <IfModule !mod_authz_host.c>
    LoadModule authz_host_module /usr/lib/apache2/modules/mod_authz_host.so
  </IfModule>
  <IfModule !mod_setenvif.c>
    LoadModule setenvif_module /usr/lib/apache2/modules/mod_setenvif.so
  </IfModule>
  <IfModule !mod_rewrite.c>
    LoadModule rewrite_module /usr/lib/apache2/modules/mod_rewrite.so
  </IfModule>
  <IfModule !mod_alias.c>
    LoadModule alias_module /usr/lib/apache2/modules/mod_alias.so
  </IfModule>
  <IfModule !mod_mime.c>
    LoadModule mime_module /usr/lib/apache2/modules/mod_mime.so
  </IfModule>
  <IfModule !mod_apreq2.c>
    LoadModule apreq_module /usr/lib/apache2/modules/mod_apreq2.so
  </IfModule>
  <IfModule !mod_unique_id.c>
    LoadModule unique_id_module /usr/lib/apache2/modules/mod_unique_id.so
  </IfModule>
  <IfModule !mod_qos.c>
    LoadModule qos_module /usr/lib/apache2/modules/mod_qos.so
  </IfModule>
</IfDefine>

#RHEL specific
<IfDefine rhel>
  <IfModule !mod_perl.c>
    LoadModule perl_module modules/mod_perl.so
  </IfModule>
  <IfModule !mod_log_config.c>
    LoadModule log_config_module modules/mod_log_config.so
  </IfModule>
  <IfModule !mod_ssl.c>
    LoadModule ssl_module modules/mod_ssl.so
  </IfModule>
  <IfModule !mod_headers.c>
    LoadModule headers_module modules/mod_headers.so
  </IfModule>
  <IfModule !mod_proxy.c>
    LoadModule proxy_module modules/mod_proxy.so
  </IfModule>
  <IfModule !proxy_http.c>
    LoadModule proxy_http_module modules/mod_proxy_http.so
  </IfModule>
  <IfModule !mod_authz_host.c>
    LoadModule authz_host_module modules/mod_authz_host.so
  </IfModule>
  <IfModule !mod_setenvif.c>
    LoadModule setenvif_module modules/mod_setenvif.so
  </IfModule>
  <IfModule !mod_rewrite.c>
    LoadModule rewrite_module modules/mod_rewrite.so
  </IfModule>
  <IfModule !mod_alias.c>
    LoadModule alias_module modules/mod_alias.so
  </IfModule>
  <IfModule !mod_mime.c>
    LoadModule mime_module modules/mod_mime.so
  </IfModule>
  <IfModule !mod_apreq2.c>
    LoadModule apreq_module modules/mod_apreq2.so
  </IfModule>
  <IfModule !mod_unique_id.c>
    LoadModule unique_id_module modules/mod_unique_id.so
  </IfModule>
  <IfModule !mod_qos.c>
    LoadModule qos_module modules/mod_qos.so
  </IfModule>
</IfDefine>

PerlSwitches -I/usr/local/pf/lib
#AddHandler perl-script .cgi
#Options +ExecCGI
#PerlHandler ModPerl::PerlRun

# Prevent Browsers (Chrome and Firefox) to cache DNS while under the captive portal
Header always set X-DNS-Prefetch-Control off
AcceptMutex posixsem

<Proxy *>
  Order deny,allow
  Allow from all
</Proxy>

<Files ~ "\.(cgi?)$">
  SSLOptions +StdEnvVars
</Files>

SetEnvIf User-Agent ".*MSIE.*" \
  nokeepalive ssl-unclean-shutdown \
  downgrade-1.0 force-response-1.0

TypesConfig /etc/mime.types

<Perl>
BEGIN {
    use pf::log 'service' => 'httpd.portal', no_stderr_trapping => 1, no_stdout_trapping => 1;
}
use pf::config qw();
use Tie::DxHash;
use pf::services::manager::httpd();
use Apache::SSLLookup;

sub gen_conf {
    my %conf;
    tie %conf, 'Tie::DxHash';

    %conf = @_;
    return \%conf;
} 

my $PfConfig = \%pf::config::Config;
my $management_network = $pf::config::management_network;
my $install_dir = $pf::config::install_dir;
my $var_dir = $pf::config::var_dir;
my @internal_nets = @pf::config::internal_nets;
my $host;

$PidFile = $install_dir.'/var/run/httpd.portal.pid';

$Include = $install_dir.'/conf/httpd.conf.d/log.conf';

$User = "pf";
$Group = "pf";

$PerlOptions = "+GlobalRequest";
$ProxyRequests = "Off";

if (defined($PfConfig->{'alerting'}{'fromaddr'}) && $PfConfig->{'alerting'}{'fromaddr'} ne '') {
    $ServerAdmin = $PfConfig->{'alerting'}{'fromaddr'};
} else {
    $ServerAdmin = "root\@".$PfConfig->{'general'}{'hostname'}.".".$PfConfig->{'general'}{'domain'};
}

$ServerTokens = "Prod";
$ServerSignature = "Off";
$UseCanonicalName = "Off";
$Timeout = "50";
$KeepAliveTimeout = "10";

$MaxClients = pf::services::manager::httpd::calculate_max_clients(pf::services::manager::httpd::get_total_system_memory());
$StartServers =  pf::services::manager::httpd::calculate_start_servers($MaxClients);
$MinSpareServers = pf::services::manager::httpd::calculate_min_spare_servers($MaxClients);

if( pf::config::isenabled ($PfConfig->{services}{httpd_mod_qos})) {
    my $qos = $MaxClients * .7;
    $QS_SrvMaxConnClose = $qos;
    $QS_SrvMaxConnPerIP = $PfConfig->{services}{httpd_mod_qos_maximum_connections_per_device};
}

$HostnameLookups = "off";
$MaxRequestsPerChild = "1000";
$PerlInitHandler = "pf::WebAPI::InitHandler";


$SSLPassPhraseDialog = "builtin";
$SSLSessionCache = "dbm:".$install_dir."/var/ssl_scache";
$SSLSessionCacheTimeout = "300";
$SSLMutex = "file:".$install_dir."/var/ssl_mutex";
$SSLRandomSeed = "startup builtin";
$SSLRandomSeed = "startup file:/dev/urandom 1024";
$SSLRandomSeed = "connect builtin";
$SSLRandomSeed = "connect file:/dev/urandom 1024";
$SSLProtocol = "All -SSLv2";
$SSLCipherSuite = "ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-AES256-GCM-SHA384:DHE-RSA-AES128-GCM-SHA256:DHE-DSS-AES128-GCM-SHA256:kEDH+AESGCM:ECDHE-RSA-AES128-SHA256:ECDHE-ECDSA-AES128-SHA256:ECDHE-RSA-AES128-SHA:ECDHE-ECDSA-AES128-SHA:ECDHE-RSA-AES256-SHA384:ECDHE-ECDSA-AES256-SHA384:ECDHE-RSA-AES256-SHA:ECDHE-ECDSA-AES256-SHA:DHE-RSA-AES128-SHA256:DHE-RSA-AES128-SHA:DHE-DSS-AES128-SHA256:DHE-RSA-AES256-SHA256:DHE-DSS-AES256-SHA:DHE-RSA-AES256-SHA:AES128-GCM-SHA256:AES256-GCM-SHA384:ECDHE-RSA-RC4-SHA:ECDHE-ECDSA-RC4-SHA:AES128:AES256:RC4-SHA:HIGH:!aNULL:!eNULL:!EXPORT:!DES:!3DES:!MD5:!PSK";
$SSLHonorCipherOrder = "on";

$ErrorLog = $install_dir.'/logs/portal_error_log';

foreach my $interface (@internal_nets) {
    push (@Listen,$interface->{'Tip'}.":80");
    push (@Listen,$interface->{'Tip'}.":443");
    push (@NameVirtualHost,$interface->{'Tip'}.":80");
    push (@NameVirtualHost,$interface->{'Tip'}.":443");
    push (@{ $VirtualHost{$interface->{'Tip'}.":80"} }, gen_conf(
         ServerName => $PfConfig->{'general'}{'hostname'}.".".$PfConfig->{'general'}{'domain'},
         DocumentRoot => $install_dir.'/html/captive-portal',
         ErrorLog => $install_dir.'/logs/portal_error_log',
         CustomLog => $install_dir.'/logs/portal_access_log combined',
         Include => $var_dir.'/conf/captive-portal-common.conf',
         Include => $var_dir.'/conf/block-unwanted.conf',
         Include => $var_dir.'/conf/captive-portal-cleanurls.conf',
    ));
    push (@{ $VirtualHost{$interface->{'Tip'}.":443"} }, gen_conf(
         ServerName => $PfConfig->{'general'}{'hostname'}.".".$PfConfig->{'general'}{'domain'},
         DocumentRoot => $install_dir.'/html/captive-portal',
         ErrorLog => $install_dir.'/logs/portal_error_log',
         CustomLog => $install_dir.'/logs/portal_access_log combined',
         SSLEngine => 'on',
         SSLProxyEngine    => 'on',
         Include => $var_dir.'/conf/ssl-certificates.conf',
         Include => $var_dir.'/conf/captive-portal-common.conf',
         Include => $var_dir.'/conf/block-unwanted.conf',
         Include => $var_dir.'/conf/captive-portal-cleanurls.conf',
    ));
}

if (defined($management_network->{'Tip'}) && $management_network->{'Tip'} ne '') {
    if (defined($management_network->{'Tvip'}) && $management_network->{'Tvip'} ne '') {
        $host = $management_network->{'Tvip'};
    } else {
        $host = $management_network->{'Tip'};
    }

    push (@Listen,$host.":80");
    push (@Listen,$host.":443");
    push (@NameVirtualHost,$host.":80");
    push (@NameVirtualHost,$host.":443");

    push @{ $VirtualHost{$host.":80"} }, gen_conf(
         ServerName          => $PfConfig->{'general'}{'hostname'}.".".$PfConfig->{'general'}{'domain'},
         DocumentRoot        => $install_dir.'/html/pfappserver/lib',
         ErrorLog            => $install_dir.'/logs/portal_error_log',
         CustomLog           => $install_dir.'/logs/portal_access_log combined',
         Include             => $var_dir.'/conf/captive-portal-common.conf',
         Include             => $var_dir.'/conf/block-unwanted.conf',
         Include             => $var_dir.'/conf/captive-portal-cleanurls.conf',
    );
    push @{ $VirtualHost{$host.":443"} }, gen_conf(
         ServerName          => $PfConfig->{'general'}{'hostname'}.".".$PfConfig->{'general'}{'domain'},
         DocumentRoot        => $install_dir.'/html/pfappserver/lib',
         ErrorLog            => $install_dir.'/logs/portal_error_log',
         CustomLog           => $install_dir.'/logs/portal_access_log combined',
         SSLEngine           => 'on',
         Include             => $var_dir.'/conf/ssl-certificates.conf',
         Include             => $var_dir.'/conf/captive-portal-common.conf',
         Include             => $var_dir.'/conf/block-unwanted.conf',
         Include             => $var_dir.'/conf/captive-portal-cleanurls.conf',
    );

} 

</Perl>


