#!/bin/bash

#kick off indytube
#you should remember to check you have all the right permissions set.
cd /opt/indytube/indytube-prod/

#clear all logs
#these filenames MUST sync with settings in indytube.conf
rm encoder.lock.*
rm wetube.log
rm run_indytube.log

#with logs
#python2.5 indytube.py >run_indytube.log 2>&1 &

#without logs
python2.5 indytube.py >/dev/null 2>&1 &

echo $! > indytube.pid
