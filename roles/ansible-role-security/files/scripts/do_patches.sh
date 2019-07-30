#!/bin/bash

if [ -f /etc/rsyslog.d/99-remotelogging.conf ] ; then
	SyslogServer=`grep "*.*" /etc/rsyslog.d/99-remotelogging.conf  | awk '{print $2}' | cut -d: -f1 | cut -d@ -f2`
else
SyslogServer="svc-syslog.cls.eng.netapp.com"

fi

Host=`hostname | cut -d. -f1 | tail -c 2`
echo "Host: "$Host

Ubuntu=`uname -a | grep Ubuntu | wc -l`
if [ $Ubuntu == 1 ]; then
        OS="Ubuntu"
else
        OS="Redhat"
fi
echo "Operating System: "$OS

Day=`date | awk '{print $1}'`

do_patch () {
	# /etc/do_patches.exempt should contain the name of the manager who approved excluding the system from automated patching
	if [ -f /etc/do_patches.exempt ] ; then
logger -n $SyslogServer -p local3.info -t do_patches -P 5151 -s state=Exempt operating_system=$OS file=/etc/do_pathes.exempt >/dev/null 2>&1
	else 
echo "Patching " $Hostname " which is running " $OS
logger -n $SyslogServer -p local3.info -t do_patches -P 5151 -s state=Start operating_system=$OS >/dev/null 2>&1

		if [ $OS == "Ubuntu" ] ; then
		# Exclude docker from upgrades
		apt-mark hold docker-ce  docker-ce-cli containerd.io	
           	DEBIAN_FRONTEND='noninteractive' apt upgrade -yq --fix-broken -o Dpkg::Options::="--force-confdef" -o Dpkg::Options::="--force-confold"
		else 
	yum update -y --skip-broken   # maybe yum -y update --security
		fi
		logger -n $SyslogServer -p local3.info -t do_patches -P 5151 -s state=Stop operating_system=$OS >/dev/null 2>&1
	fi

# Start sssd due to it always dies during an update, (daudette)
service sssd start
}

########
# MAIN #
########
if [ $Host == 0 ] || [ $Host == 2 ] || [ $Host == 4 ] || [ $Host == 6 ] || [ $Host == 8 ]; then
        echo "System is even"
        if [ $Day == "Tue" ]; then
           do_patch
        fi
elif [ $Host == 1 ] || [ $Host == 3 ] || [ $Host == 5 ] || [ $Host == 7 ] || [ $Host == 9 ]; then
        echo "System is odd"
        if [ $Day == "Thr" ]; then
           do_patch
        fi
else
        echo "System is a letter"
        if [ $Day == "Wed" ]; then
           do_patch
        fi
fi
