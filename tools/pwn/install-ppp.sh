#!/bin/sh

# Only for OSX
if [[ $(uname) == 'Darwin' ]]; then
    cp -v ppp.py ~/Library/Python/3.6/lib/python/site-packages/ppp.py
    cp -v ppp.py ~/Library/Python/2.7/lib/python/site-packages/ppp.py
else
    echo "we don't support your OS. Check the script pls"
fi
