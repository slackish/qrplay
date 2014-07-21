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

    def __init__(self, label, file_comms, logger, dsn='qemu:///system', \
                    pre_hook="./prevm", post_hook="./postvm", \
                    disk_hook="./prepdisk", store="./store", runtime=180):
        self.dsn = dsn
        self.logger = logger
        self.pre_hook = pre_hook
        self.post_hook = post_hook
        self.disk_hook = disk_hook
        self.store = store
        self.label = label
        self.file_comms = file_comms
        self.runtime = runtime
        #self._validate()
        self._connected = False
        self._conn = None
        self._conn_count = 0
        self.diskimg = None


    def _status(self):
        """
        attempt to find libvirt vm with this label
        """
        #XXX
        pass


    def _validate(self):
        """
        Ensure all VMs are DTF (down to finish)
        """
        if not self._status(self.label):
            raise Exception("VM %s not DTF" % self.label)

        if not (self.pre_hook != None and os.path.isfile(self.pre_hook) and \
                        os.access(self.pre_hook, os.X_OK)):
            self.pre_hook = None
        if not (self.post_hook != None and os.path.isfile(self.post_hook) and \
                        os.access(self.post_hook, os.X_OK)):
            self.post_hook = None
        if not (self.disk_hook != None and os.path.isfile(self.disk_hook) and \
                        os.access(self.disk_hook, os.X_OK)):
            self.disk_hook = None


    def start(self, diskimg_param):
        """ 
        Fire up a machine 

        http://virtips.virtwind.com/2012/05/attaching-disk-via-libvirt-using-python/

        @params diskimg_param: the file or files to pack in the disk image
        @returns: boolen true if fired up, false if cannot
        """
        self.logger.debug("firing up %s" % self.label)

        # pre hook
        if self.pre_hook != None:
            if subprocess.call([self.pre_hook]):
                self.logger.debug("Prehook '%s' ok" % self.pre_hook)
            else:
                self.logger.debug("Prehook '%s' returned error" % self.pre_hook)

        runnable, state = self.status(self.label)
        if not runnable:
            self.logger.warn("VM is in %d state" % state)
            return false

        conn = self._connect()

        # start vm from snapshot
        vm, snap = self._latest_snap(self.label)

        if vm != None and snap != None:
            try:
                vm.revertToSnapshot(snap, flags=0)
            except libvirt.libvirtError:
                self.logger.warn("Unable to restore snapshot on %s" % self.label)
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

        self.wait_status(RUNNING)
        # attach diskimg
        if diskimg != None:
            self.logger.debug("attempting to attach %s to %s" % \
                                (diskimg, self.label))
            template = DISK_TEMPLATE.format(path=diskimg, dev="vdb")
            vm.attachDevice(template)
            self.diskimg = diskimg

        self._disconnect()

    
    def run_job(self):
        """
        Wait for a job to come in and execute it.
        """
        while True:
            try:
                jobfile = self.file_comms.get()
                self.logger.info("Received jobfile %s for %s" % (jobfile, \
                                                self.label))

                # start
                self.start(jobfile)

                # wait for completion
                self.wait_status(SHUTOFF, timeout=self.runtime)
                self.logger.info("jobfile %s completed on %s" % (jobfile, \
                                                self.label))

                # prep things to store




                # run post-game thing as needed
                subprocess.call([self.store, self.diskimg,....)

                # reset
                self.cleanup()
            

        

    def force_stop(self):
        """ Fire up a machine """
        pass


    def cleanup(self):
        """ cleanup and reset a VM """
        pass


    def wait_status(self, desired_state, timeout=120):
        """
        Waits a period of time for a VM to enter a state
        
        @param desired_state: the state to wait for
        @param timeout: peroid of time to wait for state change
        """
        conn = self._connect()

        _, cur_state = self.status(self.label)

        waittime = 0
        while cur_state != desired_state:
            time.sleep(1)
            waittime += 1
            _, cur_state = self.status(self.label)
            if waittime >= timeout:
                self.logger.critical("ZOMG! %s not entering state %d" % \
                                    (self.label, desired_state))
                raise Exception("ZOMG! %s not entering state %d" % \
                                    (self.label, desired_state))
        self._disconnect()


    def status(self):
        """ 
        get the status of a VM 

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
            vm = conn.lookupByName(self.label)
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


    def _latest_snap(self):
        """
        grabs the latest snapshot

        @returns: pointer to vm and snapshot in a tuple
        """
        conn = self._connect()
        try:
            vm = conn.lookupByName(self.label)
            snapshot = vm.hasCurrentSnapshot(flags=0)
            if snapshot:
                return vm, vm.snapshotCurrent(flags=0)
            else:
                raise Exception("No current snapshot for %s" % self.label)
        except libvirt.libvirtError:
            self._disconnect()
            self.logger.error("No such machine named %s" % self.label)
            raise 
        finally:
            self._disconnect()


if __name__ == "__main__":
    print "you should not be running this"
