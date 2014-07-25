#!/bin/bash

IMG_BASE="/var/lib/libvirt/images"

for i in `seq 1 8`; do 
    qemu-img create -f qcow2 -b ${IMG_BASE}/runner.qcow2 ${IMG_BASE}/runner-${i}.qcow2

    virt-install --name "runner-${i}" \
        --ram=512 \
        --vcpus=1 \
        --os-type=linux \
        --disk=${IMG_BASE}/runner-${i}.qcow2 \
	--import \
        --vnc

done
