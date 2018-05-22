import string

MD5_LEN = 32

def factor(x):
    return [i for i in range(2, x) if x % i == 0]

def de_hex(s):
    components = [s[i:i + 2] for i in range(0, len(s), 2)]
    return ''.join(chr(int(r, 16)) for r in components)

def xorc(a, b):
    return chr(ord(a) ^ ord(b))

def xors(s1, s2):
    return [xorc(s1[i], s2[i]) for i in range(min(len(s1), len(s2)))]

def repeat(s, l):
    return (s * (int(l / len(s)) + 1))[:l]

def find_key_remainder(key, md):
    endings = [key[:i + 1] for i in range(len(key))]
    for r in endings:
        end = xors(md[-len(r):], r)
        if all(c in string.hexdigits for c in end):
            return len(end)

def log_solve_it(msg, sz=None, tmp='\x00', non='-'):
    return ''.join(msg).replace(tmp, non)[:sz if sz is not None else len(msg)]

def get_plaintext(key, key_len, msg, msg_len, cip, verbose=False):
    temp = '\x00'

    key = ''.join(key) + temp * (key_len - len(key))
    msg = list(''.join(msg) + temp * (msg_len - len(msg)) + key)
    key = list(repeat(key, len(msg)))

    if verbose:
        print("Message" + " " * (msg_len - len("Message")) + "| " + "Key")
        print('-' * msg_len + '+-' + '-' * key_len)

    while temp in msg:
        for i in range(len(key)):
            if key[i] != temp and msg[i] == temp:
                msg[i] = xorc(key[i], cip[i])
            elif key[i] == temp and msg[i] != temp:
                key[i] = xorc(msg[i], cip[i])

        key = repeat(msg[msg_len:], len(msg))
        if verbose:
            print("{} | {}".format(log_solve_it(msg, sz=msg_len), log_solve_it(key, sz=key_len)))

    return msg


if __name__ == '__main__':
    encoded = open('enc', 'r').read().strip()

    ciphered = de_hex(encoded[:-MD5_LEN])
    md5ed    = de_hex(encoded[-MD5_LEN:])

    plain_flag = 'flag{'
    print("\n-- Getting first bytes of key --")
    print("> Using plain text: [%s]" % plain_flag)
    key = xors(ciphered, plain_flag)

    print("+ key: [%s]" % ''.join(key))

    print("\n-- Guessing key length --")

    key_rem = find_key_remainder(key, md5ed)
    print("> Determined that key length can be found by n * k = L - %d" % key_rem)

    solutions = factor(len(encoded) // 2 - key_rem)
    pairs = [(solutions[i], solutions[-(i + 1)]) for i in range(len(solutions) // 2)]

    print("+ Found candidate solutions (rejected n = 1): " + str(pairs))

    print("\n-- Solving --")

    msg = plain_flag
    for pair in pairs:
        key_len = pair[1]
        msg_len = len(encoded) // 2 - 32 - pair[1]  # The md5 digest was encoded, not the actual md5
        print("> Using n = %d --> key_len = %d, message_len = %d\n" % (pair[0], key_len, msg_len))

        plain = get_plaintext(key[:], key_len, msg[:], msg_len, ciphered, verbose=True)

        print("\n! Solution: " + ''.join(plain)[:msg_len])
