#!/bin/bash

WAITING="WAITING"
RUNNING="RUNNING"

STATUS_FILE=/tmp/runner.status
MNT_DEST="/mnt"
TIMEOUT=120
STRACE_CMD="timeout -s KILL $TIMEOUT strace -o $MNT_DEST/strace -f -e trace=file -u nobody"
POST_RUN_HOOK="/bin/echo o > /proc/sysrq-trigger"

check_new() {
    mnt_line=$(blkid | grep 'LABEL="RUN_THIS"')
    if [ -n "$mnt_line" ]; then
        dir_to_mnt=${mnt_line%%:*}
        mount $dir_to_mnt $MNT_DEST
        return 0
    else
        return 1
    fi
}


update_status() {
    if [ -n "$1" ]; then
        echo $1 > $STATUS_FILE
    else
        echo "No status provided" 1>&2
    fi
}

run_code() {
    if [ ! -x "$MNT_DEST/prog" ]; then
        echo "No program provided" 1>&2
        return 1
    fi
    if [ -e "$MNT_DEST/0" ]; then
        cat $MNT_DEST/0 | $STRACE_CMD $MNT_DEST/prog 1> $MNT_DEST/1 2> $MNT_DEST/2
    else
        $STRACE_CMD $MNT_DEST/prog 1> $MNT_DEST/1 2> $MNT_DEST/2
    fi
    copy_files
    umount $MNT_DEST

    if [ -n "$POST_RUN_HOOK" ]; then
        eval $POST_RUN_HOOK
    fi
}

copy_files() {
    count=0
    for f in $(grep -o -P 'open\("[^"]*".*WR' $MNT_DEST/strace | cut -d\" -f2); do
        mkdir -p $MNT_DEST/files/$count
        cp $f $MNT_DEST/files/$count
        count=$((count+1))
    done
}

main_loop() {
    STATUS="WAITING"
    update_status $STATUS
    while true; do
        case $STATUS in
        $WAITING)
            if check_new; then
                STATUS=$RUNNING
                update_status $STATUS
            else
                sleep 1
            fi
            ;;
        $RUNNING)
            run_code
            STATUS="WAITING"
            update_status $STATUS
            ;;
        *)
            echo "Invalid status $STATUS" 1>&2
            STATUS="WAITING"
            update_status $STATUS
            ;;
        esac
    done 
}

main_loop
