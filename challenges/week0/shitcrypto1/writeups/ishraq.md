# Key & Message length
We know the message starts with 'flag{', so xoring the first 5 bytes of
cipertext with flag{ gives the first 5 bytes of they key.  We also know the
last 32 bytes of ciphertext correspond to an md5 digest. If we try xoring each
5 consecutive bytes in the last 32 bytes of the ciphertext with the first 5
bytes of the key, and seeing if we get something that looks like a digest (i.e.
has characters 0-9,a-f), we should get all the positions in the last 32 bytes
which are a multiple of the key length. Actually we get no positions, which
suggests the key length is longer than 32 and almost divides to length of
the ciphertext. When we do the same, but xoring 3 consec bytes with 3 bytes of
key, we get one location at index 134 where we get nice characters. Luckily 134
has very few factors, it's 2 * 67. 2 probably isn't the key length, and 134 is
too long to be the key length (remember ciphertext length = key length +
message length + 32), so we know our key is 67 bytes and our message is 34 bytes.

# Recovering the key
Let ek = ciphertext[34:34+67], i.e. it's the ciphertext corresponding to the
key. We now ek[i] = key[i] ^ key[(i+34)%67]. Rearranging gives key[(i+34)%67] =
key[i] ^ ek[i]. We know key[0] is 'A', so this lets us work out key[34], which
lets us work out key[1] etc, so we have enough to recover the whole key (the
important fact being 34 and 67 are coprime).

```
import hashlib
import sys, string

def xor(s1,s2):
    return ''.join(chr(ord(a) ^ ord(b)) for a,b in zip(s1,s2))

def repeat(s, l):
    return (s*(int(l/len(s))+1))[:l]

b16s = '274c10121a0100495b502d551c557f0b0833585d1b27030b5228040d3753490a1c025415051525455118001911534a0052560a14594f0b1e490a010c4514411e070014615a181b02521b580305170002074b0a1a4c414d1f1d171d00151b1d0f480e491e0249010c150050115c505850434203421354424c1150430b5e094d144957080d4444254643'
s = b16s.decode('hex')

hl = len(hashlib.md5('').hexdigest())
print hl

k = xor(s[:5], 'flag{')
print k
u = 3
for i in xrange(len(s)-32,len(s)-u+1):
    dc = xor(k[:u], s[i:i+u])
    assert(len(dc) == u)
    p = all(c in (string.ascii_lowercase[:6] + string.digits) for c in dc)
    if p:
        print i, dc

kl = 67
wl = len(s)-hl-kl
print wl
ek = s[wl:len(s)-hl]

tk = [ord('A')] + [0] * (kl-1)
# ek[i] = k[i] ^ k[(i+wl)%kl]
i = 0
for z in xrange(67):
    j = (i+wl)%kl
    ntk = ord(ek[i]) ^ tk[i]
    tk[j] = ntk
    i = j

print tk
tks = ''.join(map(chr, tk))
print tks
print xor(s, repeat(tks, len(s)))
```
