#!/usr/bin/env python2.7


import libvirt
import os
import subprocess
import time

DISK_TEMPLATE = \
'''<disk type="file" device="disk">
        <driver name="qemu" type="raw" />
        <source file="{path}"/>
        <target bus='virtio' dev="{dev}"/>
</disk>
'''

(NOSTATE,
RUNNING,
BLOCKED,
PAUSED,
SHUTDOWN,
SHUTOFF,
CRASHED,
PMSUSPENDED,
LAST) = range(9)

class LibVirtGlue:

    def __init__(self, label, workers, logger, dsn='qemu:///system', \
                    pre_hook="./prevm", post_hook="./postvm", \
                    disk_hook="./prepdisk"):
        self.dsn = dsn
        self.logger = logger
        self.pre_hook = pre_hook
        self.post_hook = post_hook
        self.disk_hook = disk_hook
        self.label = label
        self.workers = int(workers)
        #self._validate()
        self._connected = False
        self._conn = None
        self._conn_count = 0

    def _validate(self):
        """
        Ensure all VMs are DTF (down to finish)
        """
        for i in xrange(1,self.workers+1):
            label = self.label % i
            if not self._status(label):
                raise Exception("VM %s not DTF" % label)

        if not (self.pre_hook != None and os.path.isfile(self.pre_hook) and \
                        os.access(self.pre_hook, os.X_OK)):
            self.pre_hook = None
        if not (self.post_hook != None and os.path.isfile(self.post_hook) and \
                        os.access(self.post_hook, os.X_OK)):
            self.post_hook = None
        if not (self.disk_hook != None and os.path.isfile(self.disk_hook) and \
                        os.access(self.disk_hook, os.X_OK)):
            self.disk_hook = None


    def start(self, label, diskimg_param):
        """ 
        Fire up a machine 

        http://virtips.virtwind.com/2012/05/attaching-disk-via-libvirt-using-python/

        @params label: label of the vm to fire up
        @params diskimg_param: the file or files to pack in the disk image
        @returns: boolen true if fired up, false if cannot
        """
        self.logger.debug("firing up %s" % label)

        # pre hook
        if self.pre_hook != None:
            if subprocess.call([self.pre_hook]):
                self.logger.debug("Prehook '%s' ok" % self.pre_hook)
            else:
                self.logger.debug("Prehook '%s' returned error" % self.pre_hook)

        runnable, state = self.status(label)
        if not runnable:
            self.logger.warn("VM is in %d state" % state)
            return false

        conn = self._connect()
        # start vm from snapshot
        vm, snap = self._latest_snap(label)

        if vm != None and snap != None:
            try:
                vm.revertToSnapshot(snap, flags=0)
            except libvirt.libvirtError:
                self.logger.warn("Unable to restore snapshot on %s" % label)
                self._disconnect()
                return False

        # build disk image
        if self.disk_hook:
            try:
                diskimg = subprocess.check_output([self.disk_hook, \
                                            diskimg_param])
                diskimg = diskimg.strip()
                if not (os.path.exists(diskimg) and os.access(diskimg, \
                                    os.R_OK | os.W_OK)):
                    self.logger.warn("failed to build diskimg with args '%s'" \
                        % diskimg_param)
                    diskimg = None 
                else:
                    self.logger.debug("disk image %s built ok" % diskimg)
            except subprocess.CalledProcessError:
                self.logger.debug("cmd '%s' failed to run with args '%s'" \
                        % (self.disk_hook, diskimg_param))
        else:
            self.logger.warn("Forgoing building disk image entirely")

        self.wait_status(label, RUNNING)
        # attach diskimg
        if diskimg != None:
        #XXX left off here
            self.logger.debug("attempting to attach %s to %s" % \
                                (diskimg, label))
            template = DISK_TEMPLATE.format(path=diskimg, dev="vdb")
            vm.attachDevice(template)

        

    def force_stop(self, label):
        """ Fire up a machine """
        pass

    def cleanup(self, label):
        """ cleanup and reset a VM """
        pass

    def wait_status(self, label, desired_state, timeout=120):
        """
        Waits a period of time for a VM to enter a state
        
        @param label: vm to check
        @param desired_state: the state to wait for
        @param timeout: peroid of time to wait for state change
        """
        conn = self._connect()

        _, cur_state = self.status(label)

        waittime = 0
        while cur_state != desired_state:
            time.sleep(1)
            waittime += 1
            _, cur_state = self.status(label)
            if waittime >= timeout:
                self.logger.critical("ZOMG! %s not entering state %d" % \
                                    (label, desired_state))
                raise Exception("ZOMG! %s not entering state %d" % \
                                    (label, desired_state))
        self._disconnect()

    def status(self, label):
        """ 
        get the status of a VM 

        @param label: vm to check
        @returns: a tuple, first value being true if ready, otherwise false
                second value is the actual found status
        """
        
        #states according to 
        #http://libvirt.org/html/libvirt-libvirt.html#virDomainState
        #VIR_DOMAIN_NOSTATE  =   0   
        #VIR_DOMAIN_RUNNING  =   1   
        #VIR_DOMAIN_BLOCKED  =   2   
        #VIR_DOMAIN_PAUSED   =   3   
        #VIR_DOMAIN_SHUTDOWN =   4   
        #VIR_DOMAIN_SHUTOFF  =   5   
        #VIR_DOMAIN_CRASHED  =   6   
        #VIR_DOMAIN_PMSUSPENDED  =   7   
        #VIR_DOMAIN_LAST =   8   

        conn = self._connect()
        try:
            vm = conn.lookupByName(label)
            state = vm.state(flags=0)
        except libvirt.libvirtError:
            self.logger.error("wut? no status")
            raise
        finally:
            self._disconnect()
        
        if state[0] == PAUSED or state[0] == SHUTOFF:
            return True, state[0]
        else:
            return False, state[0]


    def _connect(self):
        """ 
        connect to libvirt system 

        @returns a connection to libvirt
        """
        if self._connected:
            self._conn_count += 1
            return self._conn
        else:
            try:
                self._conn = libvirt.open(self.dsn)
                self._connected = True
                self._conn_count = 0
                return self._conn
            except libvirt.libVirtError:
                self.logger.error("Unable to connect to libvirt")
                raise
            

    def _disconnect(self):
        """ 
        disconnect from libvirt system 
            
        @param conn: the connection to disconnect from
        """
        if self._connected and self._conn_count == 1:
            try:
                self._conn.close()
                self._conn = None
                self._connected = False
                self._conn_count = 1
            except libvirt.libvirtError:
                self.logger.error("Whoa, unable to disconnect from libvirt")
                raise
        elif self._connected:
            self._conn_count -= 1
        else:
            self.logger.error("received disconnect without a matching connect")



    def valid_label(self, label):
        """
        sees if the label is valid in what the program was setup for

        @param label: the label to check
        @returns: true if ok, otherwise false
        """
        for i in xrange(1,self.workers+1):
            if self.label % i == label:
                return True
        return False


    def _latest_snap(self, label):
        """
        grabs the latest snapshot

        @param label: the label to check
        @returns: pointer to vm and snapshot in a tuple
        """
        conn = self._connect()
        try:
            vm = conn.lookupByName(label)
            snapshot = vm.hasCurrentSnapshot(flags=0)
            if snapshot:
                return vm, vm.snapshotCurrent(flags=0)
            else:
                raise Exception("No current snapshot for %s" % label)
        except libvirt.libvirtError:
            self._disconnect()
            self.logger.error("No such machine named %s" % label)
            raise 
        finally:
            self._disconnect()


if __name__ == "__main__":
    print "you should not be running this"
