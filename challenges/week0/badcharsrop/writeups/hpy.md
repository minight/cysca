# BadCharRop #
#
#
##### Run the Program #####
If we run the program it tells us this message:
badchars are: b i c / <space> f n s
and then lets us input a string before exiting
#
##### Check Security Settings ##### 
I like to use checksec -> checksec ./badchars

NX is Enabled (Non-Executable Stack, but no canary, pie ond only partial relro.
So we know we don't have to worry about aslr or stack smashing.
#
##### Dissassemble #####
I use r2 to disassemble my binaries, and after opening it up and looking at the functions available there is one of interest - checkBadChars

 
Looking inside badchars there is a loop that is entered that strips out the characters listed as badchars before storing our entered string onto the stack. This could be a problem if we need to write bin/sh to get our shell!

Lets have a look at our pwnme function!
Alright so a fair bits going on in here. But Ill walk through it:

1) It takes in input from the user of 512 bytes, but it has only allocated a buffer of size 32

2) It then passes this buffer into the checkBadchars function which strips out the bad chars before returning

3) it then memcopies the buffer of max 512 bytes onto the 32 byte buffer -> overflowing it

Ok so we have an overflow what else do we have?

There is a function by the name: usefulFunction

It does a system call but uses bin/ls... and we cannot change that string to bin/sh which we need to have a shell.

So we need a bin/sh string.... HOW?
By writing /bin/sh to somewhere we know the addresss of in memory!

I like to use a tool called rabin2 -> rabin2 -S ./badchars
This will show us all the Sections of the binary. Of importance is those that are writeable!

###### 19 0x00000e10     8 0x00600e10     8 -rw- .init_array ######
###### 20 0x00000e18     8 0x00600e18     8 -rw- .fini_array ######
###### 21 0x00000e20     8 0x00600e20     8 -rw- .jcr ######
###### 22 0x00000e28   464 0x00600e28   464 -rw- .dynamic ######
###### 23 0x00000ff8     8 0x00600ff8     8 -rw- .got ######
###### 24 0x00001000   112 0x00601000   112 -rw- .got.plt ######
###### 25 0x00001070    16 0x00601070    16 -rw- .data ######
###### 26 0x00001080     0 0x00601080    48 -rw- .bss ######
#
The .bss or .dynamic sections are often the best to use, but I will use the .data section -> 0x00601070

Now the main issues we need to solve now are:

1) How to write our string into memory.
2) How to get past the badchar check that strips out /bin/sh.

The first thing I think of when I see something stripping characters is... can I slip a bin/sh past it? for example in web sec you can often get past filters by doing things like:

/bin/sh into //bbiinn//sshh and because it only does a single pass it strips out the first occurrence onlly of the bad char etc. This wont work in this situation.

So my next thought was could we possible xor it? then unxor it with a gadget?

###### $ ROPgadget --binary ./badchars | grep xor ######
###### 0x0000000000400b2a : add byte ptr [rax], al ; add byte ptr [rax], al ; add byte ptr [rax], al ; xor byte ptr [r15], r14b ; ret ######
###### 0x0000000000400b2c : add byte ptr [rax], al ; add byte ptr [rax], al ; xor byte ptr [r15], r14b ; ret ######
###### 0x0000000000400b2e : add byte ptr [rax], al ; xor byte ptr [r15], r14b ; ret ######
###### 0x0000000000400b30 : xor byte ptr [r15], r14b ; ret ######
###### 0x0000000000400b31 : xor byte ptr [rdi], dh ; ret ######
#
There are some xor gadgets... now can we use them? because we need to be able to control r15, r14...

###### 0x0000000000400bac : pop r12 ; pop r13 ; pop r14 ; pop r15 ; ret ######
###### 0x0000000000400b3b : pop r12 ; pop r13 ; ret ######
###### 0x0000000000400bae : pop r13 ; pop r14 ; pop r15 ; ret ######
###### 0x0000000000400b3d : pop r13 ; ret ######
###### 0x0000000000400b40 : pop r14 ; pop r15 ; ret ######
###### 0x0000000000400b42 : pop r15 ; ret ######

YES! :D

ALright so we can xor. Theres one annoying thing about this xor tho... it only xors one byte at a time at the address of r15!

But we can get around that if we start xoring at the bottom, and then do a xor operation incrementing the address by 1 byte each time.

So we can do a xor... but how do we write to our new memory location?

Because there is no move gadget to move r14 to r15 or vice versa...

But if we look at our gadgets again we can get around this if we use r12  and r13 to move our xor'd /bin/sh\x00 string into our target addresss

###### 0x0000000000400b34 : mov qword ptr [r13], r12 ; ret ######

Alright we are ready to build our exploit!
