# this is messy because it provides a module for both
# apache2 and php with the help of the ADVX macros

%define	rname smbauth
%define	rversion 1.4.3
%define	phpversion 5.2.4

#Apache2 Module-Specific definitions
%define mod_version %{rversion}
%define mod_name mod_%{rname}
%define mod_conf 22_%{mod_name}.conf
%define mod_so %{mod_name}.so
%define sourcename %{mod_name}

%define apache_version 2.2.6

%define inifile 58_%{rname}.ini

Summary:	Set of modules for samba authentication
Name:		%{rname}
Version:	%{rversion}
Release:	%mkrel 34
License:	GPL
Group:		System/Servers
URL:		http://www.tekrat.com/smbauth.php
Source0:	%{rname}%{rversion}.tar.bz2
Source1:	%{mod_conf}.bz2
Patch0:		mod_smbauth-%{rversion}-register.patch
BuildRequires:	apache-devel >= %{apache_version}
BuildRequires:	file
BuildRequires:  php-devel >= 3:%{phpversion}
BuildRoot:	%{_tmppath}/%{name}-%{version}-%{release}-buildroot

%description
SMBAuth is a set of modules generated via SWIG and based off of
code by the SAMBA project. The modules can be used to authenticate
users with a SMB Server or NT Domain Controller. Current modules
include commandline, Apache, Apache2, PHP, Jabber, Java, Perl, and
Python.

%package -n	apache-%{mod_name}
Summary:	DSO module for the apache Web server
Version:	%{rversion}
Group:		System/Servers
Requires(pre): rpm-helper
Requires(postun): rpm-helper
Requires(pre):	apache-conf >= %{apache_version}
Requires(pre):	apache >= %{apache_version}
Epoch:		1

%description -n	apache-%{mod_name}
Mod_%{name} is a DSO module for the apache Web server.

%package -n	php-%{rname}
Summary:	Samba auth module for PHP
Version:	%{rversion}
Group:		System/Servers
Epoch:		1

%description -n	php-%{rname}
The php-%{rname} package contains a dynamic shared object that
will add %{rname} to PHP. PHP is an HTML-embeddable scripting
language. If you need %{name} support for PHP applications,
you will need to install this package and the php package.

%prep

%setup -q -n %{rname}%{rversion}
%patch0 -p1

# strip away annoying ^M
find . -type f|xargs file|grep 'CRLF'|cut -d: -f1|xargs perl -p -i -e 's/\r//'
find . -type f|xargs file|grep 'text'|cut -d: -f1|xargs perl -p -i -e 's/\r//'

%build
%serverbuild
export CFLAGS="$CFLAGS -fPIC"

# first build the lib
pushd samba-shared
    %make CFLAGS="$CFLAGS -fPIC"
popd

# build the apache2 module
pushd apache2
    %{_sbindir}/apxs "-L../samba-shared ../samba-shared/*.o" -c %{sourcename}.c
popd

pushd php
    %{_usrsrc}/php-devel/buildext %{rname} smbauth_wrap.c "-L../samba-shared ../samba-shared/*.o" "-DCOMPILE_DL_SMBAUTH"
popd

%install
[ "%{buildroot}" != "/" ] && rm -rf %{buildroot}

# install the apache2 module
mv apache2/.libs .
install -d %{buildroot}%{_libdir}/apache-extramodules
install -d %{buildroot}%{_sysconfdir}/httpd/modules.d

install -m0755 .libs/*.so %{buildroot}%{_libdir}/apache-extramodules/
bzcat %{SOURCE1} > %{buildroot}%{_sysconfdir}/httpd/modules.d/%{mod_conf}

# install the php module
install -d %{buildroot}%{_sysconfdir}/php.d
install -d %{buildroot}%{_libdir}/php/extensions
install -m755 php/%{rname}.so %{buildroot}%{_libdir}/php/extensions/

cat > %{buildroot}%{_sysconfdir}/php.d/%{inifile} << EOF
extension = %{rname}.so
EOF

%post -n apache-%{mod_name}
if [ -f %{_var}/lock/subsys/httpd ]; then
    %{_initrddir}/httpd restart 1>&2;
fi
    
%postun -n apache-%{mod_name}
if [ "$1" = "0" ]; then
    if [ -f %{_var}/lock/subsys/httpd ]; then
	%{_initrddir}/httpd restart 1>&2
    fi
fi

%clean
[ "%{buildroot}" != "/" ] && rm -rf %{buildroot}

%files -n apache-%{mod_name}
%defattr(-,root,root)
%doc README README.APACHE2 apache2/example-config
%attr(0644,root,root) %config(noreplace) %{_sysconfdir}/httpd/modules.d/%{mod_conf}
%attr(0755,root,root) %{_libdir}/apache-extramodules/%{mod_so}

%files -n php-%{rname}
%defattr(-,root,root)
%doc README.PHP php/test.php
%attr(0644,root,root) %config(noreplace) %{_sysconfdir}/php.d/%{inifile}
%attr(0755,root,root) %{_libdir}/php/extensions/%{rname}.so
