#!/bin/bash
cd ~/moneybot-radar
python3 build.py
git add .
git commit -m "Automated dashboard stats update"
git push https://x-access-token:$(gh auth token)@github.com/Kgarmon99/moneybot-research-radar.git main
