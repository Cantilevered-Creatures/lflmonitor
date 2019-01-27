#!/usr/bin/env bash

if [ -f /etc/lflmonitor/app.cfg ]; then
  source '/etc/lflmonitor/app.cfg'
else
  source './app.cfg.example'
fi

rrdtool create $RRD_PATH \
   --start now-2h --step 5s \
   DS:vbattery:GAUGE:5m:0:50 \
   DS:vpanel:GAUGE:5m:0:50 \
   RRA:AVERAGE:0.5:5s:10d \
   RRA:AVERAGE:0.5:1m:90d \
   RRA:AVERAGE:0.5:1h:18M \
   RRA:AVERAGE:0.5:1d:10y