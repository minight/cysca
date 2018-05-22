badcharsrop
===========

checksec output:

```
RELRO           STACK CANARY      NX            PIE             RPATH      RUNPATH	FORTIFY	Fortified Fortifiable  FILE
Partial RELRO   No canary found   NX enabled    No PIE          No RPATH   No RUNPATH   No	0		8	badchars
```


Disassembly shows a function `pwnme` which calls `fgets` with a large value of `n`.  We will attempt to
overwrite the return address of `pwnme`.  However, before `pwnme` returns, it calls `checkBadchars`, which
will replace the given badchars in the buffer.  This makes loading data such as "/bin/sh" or "flag" into the
buffer more difficult.  `system` is linked in to the binary.

Quick experimentation shows that there are 40 bytes before the return address, and ASLR is enabled on the
target system.  We will use a ROP exploit.  The goal is to call `system` with a buffer to print the flag,
possibly by spawning an interactive shell.

Due to ASLR, we do not know the location of the buffer (on the heap) our input was read into. However, `pwnme`
will `memcpy` the buffer onto its stack, so we hold a reference to it via the stack pointer.

To call system, we will need `rdi` to contain a pointer to the buffer. We look for gadgets to do this.
The `usefulGadgets()` function contains a bunch of userful gadgets. Who would've thunk?

Just as `pwnme` returns, the offset 48 of our input buffer is on top of the stack.  One of the gadgets
(`0x400b34`) allows us to modify arbitrary memory in the 64-bit word at `r13` with the value in `r12`. To use
this, we need to put an appropriate address into `r13`, and the appropriate data into `r12`.

There is another gadget (`0x400b3b`) that pops data into `r12` and `r13`. We can use these two gadgets to
populate a buffer. But what buffer? There's a nice chunk of memory in the data segment. You can pick your
address from there, but be careful not to overwrite anything important.

Now, what exploit to use?

We know that the program runs in `/`, and the flag is located in `/flag`. (You can see this by calling
`usefulFunction()`, which runs `ls`.)

`system()` runs a shell, so we can use shell patterns to avoid any bad characters. So `*` will match any file,
including `flag`. There are many commands you can use to print the contents of files, `grep . *` being one
such command. Space is a badchar, but shells will accept other forms of whitespace too, such as tabs.

Finally, we pop the address of our buffer into `rdi` and call `system()`, printing out the flag.  And then
call `exit()`, for good measure.
