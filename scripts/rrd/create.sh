#!/usr/bin/env bash

if [ -f /etc/lflmonitor/app.cfg ]; then
  source '/etc/lflmonitor/app.cfg'
else
  source './app.cfg.example'
fi

rrdtool create $RRD_PATH \
   --start now-2h --step 1s \
   DS:vbattery:GAUGE:5m:0:24000 \
   DS:vpanel:GAUGE:5m:0:24000 \
   RRA:AVERAGE:0.5:1s:10d \
   RRA:AVERAGE:0.5:1m:90d \
   RRA:AVERAGE:0.5:1h:18M \
   RRA:AVERAGE:0.5:1d:10y