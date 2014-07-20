#!/usr/bin/env python2.7
"""
Does some stuff.  Maybe some cool stuff

Requirements:
libvirt (and qemu)
pyinotify
"""


import libvirt
import logging
import os
import sys

from multiprocessing import Process, Queue
from pyinotify import WatchManager, Notifier, Notifier, EventsCodes, ProcessEvent



DEFAULTS = {
        "IN_DIR": "/tmp/inqueue",
        "RUN_DIR": "/var/local/deckard/runqueue",
        "OUT_DIR": "/var/local/deckard/reports",
        "ARCH_HOOK": "./archive", 
        "RUNNERS": 1,
        "VM_LABEL": "runner_%d",
        }

###############################################################################
# File watching
###############################################################################

class FProcessor(ProcessEvent):
    """
    Watch for new jobs coming in and pass accordingly
    """
    
    def __init__(self, in_dir, run_dir, out_dir, logger, archive, file_comms):
        """
        XXX: Will be filled out
        """
        self.logger = logger
        self.archive = archive
        self.comms = file_comms
        self.in_dir = in_dir
        self.run_dir = run_dir
        self.out_dir = out_dir
        super(ProcessEvent, self).__init__()


    def _find_latest(self):
        """
        grab the highest report number and set self.count to it
        """
        highest = 1
        dirs = os.listdir(self.out_dir)
        dirs.extend(os.listdir(self.run_dir)
        for f in dirs:
            try:
                canidate = int(f)
                if canidate > highest:
                    highest = canidate
            except:
                pass
        self.count = highest


    def process_IN_CLOSE_WRITE(self, event):
        """
        File came in! lets do something
        """
        # archive
        infile = os.path.join(event.path, event.name)
        self.logger.info("New Job: %s" %  os.path.join(event.path, event.name))
        result = subprocess.call([self.archive, infile])
        if result == 0:
            self.logger.info("archived %s" % infile)
        else:
            self.logger.warn("failed to archive %s" % infile)
        # move to running directory

        # signal to start



def file_watcher(in_dir, run_dir, out_dir, logger, archive, file_comms):
    wm = WatchManager()
    mask = EventsCodes.ALL_FLAGS['IN_CLOSE_WRITE']
    notifier = Notifier(wm, FProcessor(in_dir, run_dir, out_dir, logger, archive, file_comms))
    wdd = wm.add_watch(in_dir, mask, rec=True)
    while True: 
        try:
            # process the queue of events as explained above
            notifier.process_events()
            if notifier.check_events():
                notifier.read_events()
            else:
                self.logger.debug("No new files in %s" % in_dir)
        except KeyboardInterrupt:
            notifier.stop()
            break

###############################################################################
# VM Handling
###############################################################################
# Need to Archive
# Ensure a VM is available
# Run Thing
# Wait for 

def fire_off_vms(args, file_comms, logger):
    """
    initialize vms
    """
    vm_managers = []
    for i in xrange(multiprocessing.cpu_count()):
        vm_managers.append(Process(target=vm, args=(i,
                                                    args.label,
                                                    file_comms,
                                                    logger)))

                                            

def vm(ident, label, file_comms, logger):
    # XXX left off here
    pass

###############################################################################
# Startup 
###############################################################################

def validate(args):
    passing = True
    log = []
    
    for d in (args['indir'], args['outdir'], args['rundir']):
        # ensure we can rwx each dir
        if not os.path.isdir(d):
            log.append("mkdir -p %s" % d)
            log.append("chown 755 %s" % d)
            passing = False
        elif not os.access(d, os.R_OK | os.W_OK | os.X_OK):
            log.append("chown 755 %s" % d)
            passing = False

    if passing == False:
        print "Failed to start.  Run the following:"
        print "\n".join(log)
        sys.exit(1)


def main(args):
    file_comms = Queue()
    fw = Process(target=file_watcher, args=(args['indir'], 
                                            args['rundir'], 
                                            args['outdir'], 
                                            logging, 
                                            args['archive'], 
                                            file_comms)
                 )
    fw.start()
    fw.join()


if __name__ == '__main__':
    try:
       import argparse
    except:
        logging.critical("I need to run from >python2.7")
        sys.exit(1)

    parser = argparse.ArgumentParser(description='Manages the queue to run code')
    parser.add_argument('-i','--indir', 
            help='Directory to monitor for incoming files',
            default=DEFAULTS["IN_DIR"]
            )
    parser.add_argument('-r','--rundir', 
            help='Directory to store temporary data',
            default=DEFAULTS["OUT_DIR"]
            )
    parser.add_argument('-o','--outdir', 
            help='Directory to write data',
            default=DEFAULTS["OUT_DIR"]
            )
    parser.add_argument('-a','--archive', 
            help='Executable for archival',
            default=DEFAULTS["ARCH_HOOK"]
            )
    parser.add_argument('-l','--label', 
            help='VM label to pull from',
            default=DEFAULTS["VM_LABEL"]
            )
    args = vars(parser.parse_args())
    args = vars(parser.parse_args())

    logging.basicConfig(level=logging.DEBUG)

    validate(args)
    main(args)
