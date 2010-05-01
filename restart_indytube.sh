#!/bin/sh

INDYTUBEPID=`cat indytube.pid`
kill $INDYTUBEPID
sleep 2
kill -9 $INDYTUBEPID
rm indytube-encoder.lock.*
./run_indytube.sh
