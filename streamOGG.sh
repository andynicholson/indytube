#!/bin/bash

#seach through all encoded files, named "<something>ogg"

find /var/www/indytube-files/ -name "*ogg" -print > playlist.txt

for i in $(cat playlist.txt);
do
	echo "streaming $i to icecast2 streamer ... ";
	cat $i | oggfwd -p -n "Our TV" localhost 8000 hackme /em.ogg
	echo "DONE with $i" ;

done
