#!/bin/bash
#
# Prep a regex to be run
#

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
RFILE=$(basename $DEST)/regex.in

cat >$DEST << EOF
#!/bin/bash
grep -f regex.in /data/*
EOF
cat $PROG >> $RFILE
chmod 755 $DEST
chmod 644 $RFILE

