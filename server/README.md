Qemu Code Execution
===================

Not much to see yet, but this is the code execution system

Hopefully it's secure.  I'm sure one of you dorks will find something to break
it.


2 parts, the host and the runner.  The runner does the *legwork* by executing
code. The host is what manages incoming code and assigns it to a runner.


Building a Host
---------------



Building a Worker
-----------------

Ubuntu server 14.04, make sure to 
 * no server updates
 * install ssh server

apt-get install sudo vim build-essential
