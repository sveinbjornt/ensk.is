#!/bin/bash
#
# Deployment script for ensk.is
#

/usr/bin/rsync \
--exclude ".git" \
--exclude "venv" \
-av "." \
root@sveinbjorn.org:/www/ensk.is/html/
