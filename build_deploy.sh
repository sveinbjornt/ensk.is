#!bin/bash
#
# Build dictionary and audio files, then deploy to ensk.is
#

source venv/bin/activate
python gen.py
python audio.py

/usr/bin/rsync \
--exclude ".git" \
--exclude "venv" \
--exclude "p312" \
--exclude "__pycache__" \
--exclude "*.pyc" \
--exclude ".ruff_cache" \
--delete \
-av "." \
root@ensk.is:/www/ensk.is/html/
