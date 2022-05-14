#!/bin/bash
#
# Deployment script for ensk.is
#

/usr/bin/rsync \
--exclude ".git" \
--exclude "venv" \
--delete \
-av "." \
root@ensk.is:/www/ensk.is/html/
