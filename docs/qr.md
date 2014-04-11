QR Format Intro
===============

QR codes are how players transmit code to the server.


Format
======

Colon deliniated in 6 parts separated by colon.

'''
gameid:teamid:epochcompiletime:partnumber:totalparts:encrypted parts
'''

Game
----
Single digit int to represent the game being played.

teamid
------
randomly generated 8 character string that gets set WHEN the team initiates
upload via terminal.  teamid is the cleartext association for identifing the
OTP for encryption.

No colons allowed.

Epoch Compile Time
------------------
Not set on this.  Basically a uniq identifier to identify replay attacks 


partnumber/totalparts
---------------------
Used for multi QR uploads.  I bet you can guess what the names mean

encrypted parts
---------------
Mainly the program, gzip and  XOR'd by OTP pass(in that order).

