#!/bin/bash

IMG_BASE="/var/lib/libvirt/images"

for i in `seq 1 8`; do 

    for j in $(virsh snapshot-list runner-${i} --name); do
        virsh snapshot-delete runner-${i} ${j}
    done    

    virsh undefine runner-${i}
    rm ${IMG_BASE}/runner-${i}*

done
