Problem
===

Find the two inputs to `cipher.py` such that it produces the output given (enc).

cipher.py:
```python
import hashlib
import sys

# xors 2 strings together
def xor(s1, s2):
    return ''.join(chr(ord(a) ^ ord(b)) for a, b in zip(s1, s2))

# Repeats a string util it is length n
def repeat(s, l):
    return (s * (int(l / len(s)) + 1))[:l]


key = sys.argv[1]

plaintext = sys.argv[2] + key
plaintext += hashlib.md5(plaintext).hexdigest()

cipher = xor(plaintext, repeat(key, len(plaintext)))

print(cipher.encode('hex'))
```

enc:
```
274c10121a0100495b502d551c557f0b0833585d1b27030b5228040d3753490a1c025415051525455118001911534a0052560a14594f0b1e490a010c4514411e070014615a181b02521b580305170002074b0a1a4c414d1f1d171d00151b1d0f480e491e0249010c150050115c505850434203421354424c1150430b5e094d144957080d4444254643
```

Introduction
===
_We will refer to argv[1] as the key and argv[2] as the flag_

cipher.py uses a xor cipher to encrypt the plain text. i.e.
```
ciphertext = plaintext ^ key <==> plaintext = ciphertext ^ key
```

## Determine the start of the key
Our first step will be to initialize the value of our key. As we already know the first 5 characters of our plain text are
"flag{" we can xor these agains the first 5 characters of our ciphertext to find the first 5 characters of our key.
` "flag{" ^ "\x27\x4c\x10\x12\x1a" = "A qua" `

#### Key starts with "A qua"

## Determine Key Length

The plaintext that is encrypted in `enc` will have the form `flag + key + md5digest(flag + key)`. As the md5digest of the
key is a hex-string representation of the actual hash, we know the last 32 characters must decrypt to `1234567890abcdef`.
Working from the back, we can then try different lengths of our key against the final few bytes of our ciphertext and
check which ones result in a valid charset.

```python
# Returns 3 for our input
def find_key_remainder(key, md):
    endings = [key[:i + 1] for i in range(len(key))]
    for r in endings:
        end = xors(md[-len(r):], r)
        if all(c in string.hexdigits for c in end):
            return len(end)
```

Once we know what the length the final repeat of the key is we can find possible key lengths by solving
` n * k_len = c_len - find_key_remainder `
For our input this results in `(2, 67)` as possible key lengths, we can reject 2 based on the fact our key must be at least 5 bytes long

#### Key length = 67

## Solve cipher
Once we know the key length, as well as part of the key we can iteratively solve for our plaintext. 
We pad the key and the message with \x00 and continuously xor the known parts of the key and the message until each
no longer has \x00 in the string
```python
def get_plaintext(key, key_len, msg, msg_len, cip):
    temp = '\x00'

    key = ''.join(key) + temp * (key_len - len(key))
    msg = list(''.join(msg) + temp * (msg_len - len(msg)) + key)
    key = list(repeat(key, len(msg)))

    while temp in msg:
        for i in range(len(key)):
            if key[i] != temp and msg[i] == temp:
                msg[i] = xorc(key[i], cip[i])
            elif key[i] == temp and msg[i] != temp:
                key[i] = xorc(msg[i], cip[i])

        key = repeat(msg[msg_len:], len(msg))

    return msg
```

This gives us our flag
