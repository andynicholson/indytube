#!/bin/sh

#move to right directory
cd /opt/indytube/indytube-prod/
#get the PID
INDYTUBEPID=`cat indytube.pid`

#kill possible subprocesses
killall qt-faststart
killall ffmpeg
killall mencoder

#kill indytube
kill $INDYTUBEPID
#wait
sleep 2
#kill it again, possibly
kill -9 $INDYTUBEPID

#clear all logs
#these filenames MUST sync with settings in indytube.conf
rm encoder.lock.*
rm wetube.log
rm run_indytube.log

#run the indytube process
./run_indytube.sh 
