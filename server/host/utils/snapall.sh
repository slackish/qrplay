#!/bin/bash

IMG_BASE="/var/lib/libvirt/images"

for i in `seq 1 8`; do 
    
    virsh snapshot-create runner-${i}
    virsh destroy runner-${i}

done
