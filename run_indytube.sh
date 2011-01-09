#!/bin/bash

#kick off indytube
#you should remember to check you have all the right permissions set.
cd /opt/indytube/indytube-prod/

rm encoder.lock.0
python2.5 indytube.py >run_indytube.log 2>&1 &
echo $! > indytube.pid
