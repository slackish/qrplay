#!/usr/bin/env python2.7


DEFAULTS = {
        "IN_DIR": "/tmp/runqueue",
        "OUT_DIR": "/var/local/runqueue",
        "ARCH_HOOK": "./archive"
        }



def main(args):
    pass


if __name__ == '__main__':
    try:
       import argparse
    except:
        print >>sys.stderr, "I need to run from >python2.7"

    parser = argparse.ArgumentParser(description='Manages the queue to run code')
    parser.add_argument('-i','--indir', 
            help='Directory to monitor for incoming files',
            default=DEFAULTS["IN_DIR"]
            )
    parser.add_argument('-o','--outdir', 
            help='Directory to write data',
            default=DEFAULTS["OUT_DIR"]
    parser.add_argument('-a','--archive', 
            help='Executable for archival',
            default=DEFAULTS["ARCH_HOOK"]
    args = vars(parser.parse_args())
