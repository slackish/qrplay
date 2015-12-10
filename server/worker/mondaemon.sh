#!/bin/bash
#
# Find new material to run, and execute it.
#
# It's expecting one or two filesystems that will be labeled "RUN_THIS" and 
# "DATA".
# DATA is the optional partition to allow data to be fed into the program.
# RUN_THIS is rw filesystem that should contain an executable named "prog" and 
# optionally a file named 0 for stdin.
# 
# To avoid race conditions, attach DATA before attaching RUN_THIS
#

WAITING="WAITING"
RUNNING="RUNNING"

STATUS_FILE=/tmp/runner.status
RUN_THIS_DEST="/mnt"
DATA_DEST="/data"
TIMEOUT=120
STRACE_CMD="timeout -s KILL $TIMEOUT strace -o ${RUN_THIS_DEST}/strace -f -e trace=file -u nobody"
POST_RUN_HOOK="/bin/echo o > /proc/sysrq-trigger"


#
# See if a disk label exists and mount it
#
# @param $1: Label of what to look for
# @param $2: Mount point, if specified label exists
#
check_and_mount_label() {
    LABEL=$1
    DEST=$2

    mnt_line=$(blkid | grep 'LABEL="'${LABEL}'"')
    if [ -n "$mnt_line" ]; then
        dir_to_mnt=${mnt_line%%:*}
        if [ ! -d "$DEST" ]; then
            mkdir -p $DEST
        fi
        mount ${dir_to_mnt} ${DEST}
        return 0
    else
        return 1
    fi
}

#
# Look for new filesystems.
#
check_new() {
    ret_status=1

    if check_and_mount_label "RUN_THIS" "${RUN_THIS_DEST}"; then
        ret_status=0
    fi
    check_and_mount_label "DATA" "${DATA_DEST}"

    return ${ret_status}
}


#
# Update the status file
#
# @param 1: Label of status
#
update_status() {
    if [ -n "$1" ]; then
        echo $1 > $STATUS_FILE
    else
        echo "No status provided" 1>&2
    fi
}

#
# Go out and execute code
#
run_code() {
    if [ ! -x "${RUN_THIS_DEST}/prog" ]; then
        echo "No program provided" 1>&2
        return 1
    fi
    if [ -e "${RUN_THIS_DEST}/0" ]; then
        cat ${RUN_THIS_DEST}/0 | ${STRACE_CMD} ${RUN_THIS_DEST}/prog 1> ${RUN_THIS_DEST}/1 2> ${RUN_THIS_DEST}/2
    else
        ${STRACE_CMD} ${RUN_THIS_DEST}/prog 1> ${RUN_THIS_DEST}/1 2> ${RUN_THIS_DEST}/2
    fi
    copy_files
    umount ${RUN_THIS_DEST}

    if [ -n "${POST_RUN_HOOK}" ]; then
        eval ${POST_RUN_HOOK}
    fi
}

#
# Go out and execute code
#
copy_files() {
    count=0
    for f in $(grep -o -P 'open\("[^"]*".*WR' $RUN_THIS_DEST/strace | cut -d\" -f2); do
        mkdir -p ${RUN_THIS_DEST}/files/${count}
        cp $f ${RUN_THIS_DEST}/files/${count}
        count=$((count+1))
    done
}

#
# Go out and execute code
#
main_loop() {
    STATUS=${WAITING}
    update_status $STATUS
    while true; do
        case $STATUS in
        ${WAITING})
            if check_new; then
                STATUS=${RUNNING}
                update_status $STATUS
            else
                sleep 1
            fi
            ;;
        ${RUNNING})
            run_code
            STATUS=${WAITING}
            update_status $STATUS
            ;;
        *)
            echo "Invalid status $STATUS" 1>&2
            STATUS=${WAITING}
            update_status $STATUS
            ;;
        esac
    done 
}

# default start
main_loop
