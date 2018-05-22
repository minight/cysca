(this method is very manual)

Inspecting the python source, we can see that this is an xor cipher, and the key is repeated for the length of the plaintext

Open up the ciphertext in cribdrag
guessing Flag{ (or variations on the capitalisation) is a good place to start

This will reveal some characters in the plaintext, allowing you to guess word endings in the plaintext, which allows you to guess more word endings in the ciphertext, etc.

You'll find that the key and plaintext are a flag concatenated with a sentence (one is flag | sentence, the other is sentence | flag)
