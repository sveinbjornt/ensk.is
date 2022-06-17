#!bin/bash

source venv/bin/activate
python gen.py
python audio.py
bash deploy.sh
