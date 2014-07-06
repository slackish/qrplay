#!/bin/bash

if [ -z "$1" -o ! -e "$1" ]; then
    echo "I need a program to manipulate"
    exit 1
fi

if [ -z "$2" ]; then
    echo "I need a destination"
    exit 2
fi

PROG=$1
DEST=$2

echo "#!/usr/bin/env ruby" > $DEST
cat $1 >> $DEST
chmod 755 $DEST

