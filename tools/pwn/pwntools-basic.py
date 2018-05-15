from pwn import *
import struct
context.log_level = 'info'

IP = ['']
PORT = 9447
FILENAME = "derp"
if IP:
    tube = remote(IP[0], PORT)
else:
    tube = process(FILENAME)

# hax
payload = ''
payload += struct.pack("<I", 0x41414141)
 # hax

tube.recvuntil("> ")
tube.sendline(payload)
tube.interactive()
