#!/usr/bin/env bash

if [ -f /etc/lflmonitor/app.cfg ]; then
  echo '/etc/lflmonitor/app.cfg'
else
  echo './app.cfg.example'
fi