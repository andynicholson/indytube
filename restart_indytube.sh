#!/bin/sh

INDYTUBEPID=`cat indytube.pid`

#kill possible subprocesses
killall qt-faststart
killall ffmpeg
killall mencoder

kill $INDYTUBEPID
sleep 2
kill -9 $INDYTUBEPID
rm indytube-encoder.lock.*
rm wetube.log
rm run_indytube.log
./run_indytube.sh 
