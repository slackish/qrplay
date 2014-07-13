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
        """ get the status of a VM """
        pass

    def _connect(self):
        """ connect to libvirt system """
        try:
            return libvirt.open(self.dsn)
        except libvirt.libVirtError:
            logger.error("Unable to connect to libvirt")
            raise
            
    def _disconnect(self, conn):
        """ disconnect to libvirt system """
        pass

    def valid_label(self, label):
        for i in xrange(1,self.workers+1):
            if self.label % i == label:
                return True
        return False

    def _latest_snap(self, label):
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
