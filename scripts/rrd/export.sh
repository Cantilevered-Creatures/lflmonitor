#!/usr/bin/env bash

rrdtool xport -s now-3h -e now --step 300 \
DEF:a=$1:vbattery:AVERAGE \
DEF:b=$1:vpanel:AVERAGE \
XPORT:a:"Battery" \
XPORT:b:"Panel" > $2/voltage3h.xml

rrdtool xport -s now-24h -e now --step 900 \
DEF:a=$1:vbattery:AVERAGE \
DEF:b=$1:vpanel:AVERAGE \
XPORT:a:"Battery" \
XPORT:b:"Panel" > $2/voltage24h.xml

rrdtool xport -s now-48h -e now --step 1800 \
DEF:a=$1:vbattery:AVERAGE \
DEF:b=$1:vpanel:AVERAGE \
XPORT:a:"Battery" \
XPORT:b:"Panel" > $2/voltage48h.xml

rrdtool xport -s now-8d -e now --step 7200 \
DEF:a=$1:vbattery:AVERAGE \
DEF:b=$1:vpanel:AVERAGE \
XPORT:a:"Battery" \
XPORT:b:"Panel" > $2/voltage1w.xml

rrdtool xport -s now-1month -e now --step 10800 \
DEF:a=$1:vbattery:AVERAGE \
DEF:b=$1:vpanel:AVERAGE \
XPORT:a:"Battery" \
XPORT:b:"Panel" > $2/voltage1m.xml

rrdtool xport -s now-3month -e now --step 43200 \
DEF:a=$1:vbattery:AVERAGE \
DEF:b=$1:vpanel:AVERAGE \
XPORT:a:"Battery" \
XPORT:b:"Panel" > $2/voltage3m.xml

rrdtool xport -s now-1y -e now --step 86400 \
DEF:a=$1:vbattery:AVERAGE \
DEF:b=$1:vpanel:AVERAGE \
XPORT:a:"Battery" \
XPORT:b:"Panel" > $2/voltage1y.xml