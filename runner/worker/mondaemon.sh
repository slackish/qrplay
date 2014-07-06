#!/bin/bash

WAITING="WAITING"
RUNNING="RUNNING"

STATUS_FILE=/tmp/runner.status
MNT_DEST="/mnt"

check_new() {
    mnt_line=$(blkid | grep LABEL="RUN_THIS")
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
