#!/bin/sh
if [ $1 = '-h' ] || [ $1 = '--help' ]; then

	echo "usage: $0 [nmap option] <target>"
else
	nmap --script ./iptv-eds.nse --max-hostgroup 40 -n -sn --open -PS8082 $@
fi
