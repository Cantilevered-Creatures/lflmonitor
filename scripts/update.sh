#!/bin/bash

curCommit=$(curl --silent https://api.github.com/repos/HoveringHalibut/fllmonitor/git/refs/heads/master | jq -r '.object.sha')

if [ "$curCommit" != "$([ -f ./lastCommit ] && cat ./lastCommit)" ]; then
  git pull -q
  echo $curCommit > lastCommit
  sudo systemctl restart uwsgi.service
fi
