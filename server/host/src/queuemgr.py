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
        "OUT_DIR": "/var/local/deckard/donequeue",
        "ARCH_HOOK": "./archive", 
        "RUNNERS": 4,
        "VM_LABEL": "deckard_%d",
        }

###############################################################################
# File watching
###############################################################################

class FProcessor(ProcessEvent):
    """
    Watch for new jobs coming in and pass accordingly
    """
    
    def __init__(self, in_dir, run_dir, logger, file_comms):
        """
        XXX: Will be filled out
        """
        self.logger = logger
        self.comms = file_comms
        self.run_dir = run_dir
        super(ProcessEvent, self).__init__()


    def process_IN_CLOSE_WRITE(self, event):
        """
        File came in! lets do something
        """
        self.logger.info("New Job: %s" %  os.path.join(event.path, event.name))


def file_watcher(in_dir, run_dir, logger, file_comms):
    wm = WatchManager()
    mask = EventsCodes.ALL_FLAGS['IN_CLOSE_WRITE']
    notifier = Notifier(wm, FProcessor(in_dir, run_dir, logger, file_comms))
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
                                            logging, 
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
    args = vars(parser.parse_args())

    logging.basicConfig(level=logging.DEBUG)

    validate(args)
    main(args)
