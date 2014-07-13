#!/usr/bin/env python2.7


import libvirt


class LibVirt:
    
    def __init__(self, dsn, label, workers, logger, \
                        pre_hook="./prevm", post_hook="./postvm"):
        self.dsn = dsn
        self.dsn = logger
        self.pre_hook = pre_hook
        self.post_hook = post_hook
        self.label = label
        self.workers = workers
        self._validate()

    def _validate(self):
        
        

    def start(self, label):
        """ Fire up a machine """
        pass

    def force_stop(self, label):
        """ Fire up a machine """
        pass

    def cleanup(self, label):
        """ cleanup and reset a VM """
        pass

    def status(self, label):
        """ 
        get the status of a VM 

        @param label: vm to check
        @returns: true if ready, otherwise false
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
        
        if state[0] == 3 or state[0] == 4 or state[0] == 5:
            return True
        else:
            return False


    def _connect(self):
        """ 
        connect to libvirt system 

        @returns a connection to libvirt
        """
        try:
            return libvirt.open(self.dsn)
        except libvirt.libVirtError:
            logger.error("Unable to connect to libvirt")
            raise
            
    def _disconnect(self, conn):
        """ 
        disconnect from libvirt system 
            
        @param conn: the connection to disconnect from
        """
        try:
            conn.close()
        except libvirt.libvirtError:
            self.logger.error("Whoa, unable to disconnect from libvirt")
            raise


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
        @returns: pointer to snapshot
        """
        conn = self._connect()
        try:
            vm = conn.lookupByName(label)
            snapshot = vm.hasCurrentSnapshot(flags=0)
            if snapshot:
                return vm.snapshotCurrent(flags=0)
            else:
                raise Exception("No current snapshot for %s" % label)
        except libvirt.libvirtError:
            self._disconnect(conn)
            logger.error("No such machine named %s" % label)
            raise 
        finally:
            self._disconnect(conn)


if __name__ == "__main__":
    print "you should not be running this"
