#!/bin/bash
git add .
git commit -m "${1:-Quick update}"
git push
ssh pi "cd pi-stream && git pull"

