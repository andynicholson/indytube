#!/bin/bash

#kick off indytube
#you should remember to check you have all the right permissions set.
cd /opt/indytube/indytube-prod/

rm encoder.lock.0
#with logs
#python2.5 indytube.py >run_indytube.log 2>&1 &

#without logs
python2.5 indytube.py >/dev/null 2>&1 &

echo $! > indytube.pid
