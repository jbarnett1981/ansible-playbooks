#!/bin/bash

#############
# PURPOSE: TO standardize system health checks for Linux systems
# AUTHORS: Joe Garbacik, Owen Hughes, Scott Stanford, Dan Audette
# MODIFICATIONS
# 27 MAR 2017   Initial Product
# 07 JAN 2019	Updates for Ubuntu, rkhunter
# 12 MAR 2019 Added Ubuntu Support
#~

## BEGIN VARIABLES
if [ -f /etc/rsyslog.d/99-remotelogging.conf ] ; then
	SyslogServer=`grep "*.*" /etc/rsyslog.d/99-remotelogging.conf  | awk '{print $2}' | cut -d: -f1 | cut -d@ -f2`
else
SyslogServer="svc-syslog.cls.eng.netapp.com"
fi
TimeServer="time.netapp.com"
ScapServer="svc-syslog.cls.eng.netapp.com"
UrlBase="https://www.redhat.com/security/data/oval/"
## END VARIABLES

Ubuntu=`uname -a | grep Ubuntu | wc -l`
if [ $Ubuntu == 1 ]; then
        OS="Ubuntu"
else
        OS="Redhat"
fi

#################
##= Sync Time =##
#################
echo "Syncing Time with " $TimeServer
/usr/sbin/ntpdate $TimeServer

###################
##= Set Banners =##
###################
echo "Resetting Banners in the event the hostname or banner changed"

HN=`hostname -f`
MYIP1=`host $HN | awk {'print $4'}  `
MYIP2=`/bin/hostname -i`
# Check to see if it matches a local IP
LI=`ip address | grep -c $MYIP1`
if [ $MYIP1 == $MYIP2 ] ; then 
	MYIP=$MYIP1
elif [ $MYIP2 == '127.0.0.1' ] ; then
	MYIP=$MYIP1
else 
	MYIP="Unknown/Mismatch IP"
fi
echo $MYIP

########################
#== Set /etc/banner ==##
########################
/bin/echo -en "\033[1;33m" > /etc/banner
/bin/echo -e "\n\n" >> /etc/banner
/bin/echo -e "\e[0;44m              \033[0m " >> /etc/banner
/bin/echo -e "\e[0;44m              \033[0m \e[0;32mYou are connected to: " >> /etc/banner
/bin/echo -e "\e[0;44m     \033[0m    \e[0;44m     \e[0;32m $HN" >> /etc/banner
/bin/echo -e "\e[0;44m     \033[0m    \e[0;44m     \033[0m $MYIP" >> /etc/banner
/bin/echo -e "\e[0;44m     \033[0m    \e[0;44m     \033[0m All connections are monitored " >> /etc/banner
/bin/echo -e "\e[0;31m\nDisconnect IMMEDIATELY if you are not an authorized user! " >> /etc/banner
/bin/echo -e "\n-------------------------------------------------------------------" >> /etc/banner
/bin/echo -en "\033[0m" >> /etc/banner
/bin/echo -e "\n\n" >> /etc/banner
/bin/chmod 644 /etc/banner

########################
##== Set /etc/issue  =##
########################
/bin/echo -e "\n---------------------------------------------------------\n" > /etc/issue
/bin/echo -e "You are connecting to:">> /etc/issue
/bin/echo -e " Hostname:   $HN ">> /etc/issue
/bin/echo -e " Primary IP: $MYIP" >> /etc/issue
/bin/echo -e "\nAll connections are monitored                             " >> /etc/issue
/bin/echo -e "Disconnect IMMEDIATELY if you are not an authorized user! " >> /etc/issue
/bin/echo -e "\n----------------------------------------------------------\n" >> /etc/issue
/bin/chmod 644 /etc/issue

#######################
##-- Set /etc/motd --##
#######################
/bin/echo -en "\033[1;33m" > /etc/motd
/bin/echo -e "\n\n" >> /etc/motd
/bin/echo -e "\e[0;44m              \033[0m " >> /etc/motd
/bin/echo -e "\e[0;44m              \033[0m \e[0;32mYou are connected to: " >> /etc/motd
/bin/echo -e "\e[0;44m     \033[0m    \e[0;44m     \e[0;32m $HN " >> /etc/motd
/bin/echo -e "\e[0;44m     \033[0m    \e[0;44m     \033[0m $MYIP " >> /etc/motd
/bin/echo -e "\e[0;44m     \033[0m    \e[0;44m     \033[0m All connections are monitored " >> /etc/motd
/bin/echo -e "\e[0;31m\nDisconnect IMMEDIATELY if you are not an authorized user! " >> /etc/motd
/bin/echo -e "\n-------------------------------------------------------------------" >> /etc/motd
/bin/echo -en "\033[0m" >> /etc/motd
/bin/echo -e "\n\n" >> /etc/motd
/bin/chmod 644 /etc/motd

###################################
##-- Set /etc/ssh/sshd-banner --###
###################################
/bin/echo -e "WARNING : Unauthorized access to this system is forbidden and will be" > /etc/ssh/sshd-banner
/bin/echo -e "prosecuted by law. By accessing this system, you agree that your actions" >> /etc/ssh/sshd-banner
/bin/echo -e "may be monitored if unauthorized usage is suspected.\n" >> /etc/ssh/sshd-banner
/bin/echo -e "Hostname:   $HN" >> /etc/ssh/sshd-banner
/bin/echo -e "Primary IP: $MYIP" >> /etc/ssh/sshd-banner
/bin/chmod 644 /etc/ssh/sshd-banner

##############
## rkhunter ##
##############
if [ -f /bin/rkhunter ]; then
	# Red hat
	# Initial the db with the system
	if [ ! -f /var/lib/rkhunter/db/rkhunter_prop_list.dat ]; then
		/bin/rkhunter --propupd
	fi
	/bin/rkhunter --update		# Update rkhunter signatures
	/bin/rkhunter --cronjob --report-warnings-only | logger -n $SyslogServer -p local3.info -t rkhunter -P 5302 -s >/dev/null 2>&1
elif [ -f /usr/bin/rkhunter ]; then
	# Ubuntu
	# Initial the db with the system
	if [ ! -f /var/lib/rkhunter/db/rkhunter_prop_list.dat ]; then
		/usr/bin/rkhunter --propupd
	fi
	/usr/bin/rkhunter --update		# Update rkhunter signatures
	/usr/bin/rkhunter --cronjob --report-warnings-only | logger -n $SyslogServer -p local3.info -t rkhunter -P 5302 -s >/dev/null 2>&1
else
	logger -n $SyslogServer -p local3.info -t rkhunter -P 5302 -s Unable to find rkhunter>/dev/null 2>&1
fi

##########
## aide ##
##########
####
# Check for initialzed database file and if not, send alert
if [ ! -f /var/lib/aide/aide.db ]; then
	logger -n $SyslogServer -p local3.info -t aide -P 5301 -s Unable to find aide_database=/var/lib/aide/aide.db  >/dev/null 2>&1
fi
if [ -f /usr/sbin/aide ]; then
	# Red hat
	/usr/sbin/aide --check | logger -n $SyslogServer -p local3.info -t aide -P 5301 -s >/dev/null 2>&1
elif [ -f /usr/bin/aide ]; then
	# Ubuntu
	/usr/bin/aide --check | logger -n $SyslogServer -p local3.info -t aide -P 5301 -s >/dev/null 2>&1
else 
	logger -n $SyslogServer -p local3.err -t aide -P 5301 -s Unable to find aide>/dev/null 2>&1
fi


############
## clamav ##
############
# Update AV signatures
if [ -f /usr/bin/freshclam ]; then
	/usr/bin/freshclam -l /var/log/clamav/freshclam.log
else 
	logger -n $SyslogServer -p local3.err -t clamav -P 5307 -s Unable to find freshclam>/dev/null 2>&1
fi

###########
## lynis ##
###########
if [ -f /bin/lynis ]; then
	# Red Hat
	# Update signaures
	/bin/lynis update release
	# Run an evaluation 
	/bin/lynis --cronjob --auditor `hostname` --quiet --no-log audit system | logger -n $SyslogServer -p local3.info -t lynis -P 5305 -s >/dev/null 2>&1
elif [ -f /usr/sbin/lynis ]; then
	# Ubuntu 
	# Update signatures
	timeout 600 /usr/sbin/lynis update release
	# Run an evaluation 
	/usr/sbin/lynis --cronjob --auditor `hostname` --quiet --no-log audit system | logger -n $SyslogServer -p local3.info -t lynis -P 5305 -s >/dev/null 2>&1
else
	logger -n $SyslogServer -p local3.err -t lynis -P 5305 -s Unable to find lynis>/dev/null 2>&1
fi


#######################################
##- Check for Expiring Certificates -##
#######################################
# To Be Added via something like  openssl x509 -noout -dates -in  /etc/pki/ca-trust/extracted/openssl/ca-bundle.trust.crt


######################################
##- Check for Expired Certificates -##
######################################
# To Be Added



##############
# SCAP STUFF #
##############
ScapInstalled=`which oscap  | wc -l`
if [ ScapInstalled == 1 ]; then
	## GET SIGNATURES ##
	if [[ ! -e /data/signatures ]]; then
	        mkdir -p /data/signatures
	fi

	OsVersion=`uname -r | awk -F. '{print $(NF-1)}' | tail -c 2`
	FullUrl1	=$UrlBase"com.redhat.rhsa-RHEL"$OsVersion".xml"
	FullUrl2=$UrlBase"Red_Hat_Enterprise_Linux_"$OsVersion".xml"
	LocalFile1="/data/signatures/com.redhat.rhsa-RHEL"$OsVersion".xml"
	LocalFile2="/data/signatures/Red_Hat_Enterprise_Linux_"$OsVersion".xml"
	/bin/echo $FullUrl1
	/bin/echo $FullUrl2
	/bin/echo $LocalFile1
	/bin/echo $LocalFile2

	/bin/echo "OS Version: $OsVersion …  `uname -r`"
	/bin/echo "Retrieving: "$FullUrl1
	/bin/curl $FullUrl1 > $LocalFile1
	/bin/echo "Retrieving: "$FullUrl2
	/bin/curl $FullUrl2 > $LocalFile2
	sleep 3
	/bin/chown -R scap:scap /data/signatures

	## RUN OSCAP ##
	yum install -y openscap-scanner scap-workbench
	yum update -y openscap-scanner scap-workbench

	OvalFile="/data/signatures/Red_Hat_Enterprise_Linux_"$OsVersion".xml"
	Profile="stig-rhel"$OsVersion"-server-upstream"
	VariableFile="/root/ssg-rhel"$OsVersion"-oval.xml-0.variables-0.xml"

	#rpm -qa | grep "^(redhat|centos)-release"
	OSName=` awk '{print $1}' /etc/redhat-release`

	shopt -s nocasematch
	if [ "$OSName" == "CentOS" ]; then
    		XccdfFile="/usr/share/xml/scap/ssg/content/ssg-centos"$OSVersion"-xccdf.xml"
	elif  [ "$OSName" == "CentOS" ]; then
    		XccdfFile="/usr/share/xml/scap/ssg/content/ssg-rhel"$OsVersion"-xccdf.xml"
	fi
	shopt -u nocasematch

	if [ -f "/usr/bin/oscap" ]; then
        	OscapExec="/usr/bin/oscap"
	fi
	if [ -f "/bin/oscap" ]; then
        	OscapExec="/bin/oscap"
	fi

	echo "Generating Hashes, please wait ..."
	OvalFileDate=`ls -la $OvalFile |  awk {'print $6 $7'}`
	echo $OvalFile
	if [[ -e $OvalFile ]]; then
      	  	OvalFileHash=`sha256sum $OvalFile | awk '{print $1'}`
	fi
	XccdfFileDate=`ls -la $XccdfFile |  awk {'print $6 $7'}`
	if [[ -e $XccdfFile ]]; then
        	XccdfFileHash=`sha256sum $XccdfFile | awk '{print $1'}`
	fi

	# Send to syslog for graylog  - syslog-ng should not use the anycast address else logs come from anycast
	/bin/echo "OS Version: $OsVersion …  `uname -r`"
	/bin/echo "Oval File: $OvalFile"
	/bin/echo "Oval File Date: $OvalFileDate"
	/bin/echo "Oval File Hash: $OvalFileHash"
	/bin/echo "XCCDF File:    $XccdfFile"
	/bin/echo "XCCDF File Date: $XccdfFileDate"
	/bin/echo "XCCDF File Hash: $XccdfFileHash"
	/bin/echo "Variable File: $VariableFile"
	/bin/echo "Profile:       $Profile"
	/bin/echo "-----------------------------------------------------"

	cd /root
	echo "$OscapExec xccdf --fetch-remote-resources export-oval-variables --profile $Profile $XccdfFile $OvalFile"
	$OscapExec xccdf --fetch-remote-resources export-oval-variables --profile $Profile $XccdfFile $OvalFile
	echo "-----------------------------------------------------"
	$OscapExec oval eval --variables $VariableFile  --results /root/oval-results.xml  $OvalFile | grep true | logger --tcp -n  $ScapServer -p local3.info -t oscap -P 5151 -s

	# Yes these are opposite as the test check for the presence of old version therefore a pass is the inverse of the finding
	FailScore=`oscap oval eval --results /root/oval-results.xml  $OvalFile | grep -c true`
	PassScore=`oscap oval eval --results /root/oval-results.xml  $OvalFile | grep -c false`
	/bin/echo Pass Score: $PassScore
	/bin/echo Fail Score: $FailScore

	/bin/echo Sending results to $ScapServer
	/usr/bin/logger --tcp -n  $ScapServer -p local3.info -t oscap -P 5151 -s oscap_pass_score=$PassScore oscap_fail_score=$FailScore oval_file=$OvalFile oval_file_date=$OvalFileDate oval_file_hash=$OvalFileHash xccdf_file=$XccdfFile xccdf_file_date=$Xccdf_File_Date xccdf_file_hash=$XccdfFileHash profile=$Profile os_version=$OsVersion environment=$LabEnv product=OSCAP

	$OscapExec oval generate report /root/oval-results.xml > /root/report.html
fi
