# super secret cysca training series 2018

This is the repo where we will be coodinating all our CTF challenges and our writeups and tools.

**Writeup Submission**
Fork the repo and add your challenges. Make a PR with your writeup with filename `yourhandle.md`

**Challenge Creation**
Fork the repo and add your challenges. Add me to your private fork. Pull request and merge after the challenge week and during the writeup week

## Repo Structure

```
├── challenges
│   ├── setup-scripts
│   ├── templates
│   └── week[0-n]
├── readme.md
├── teams
└── tools
```

## Challenges

Contains the challenges for each week and the writeups.

### Creation
* Use `challenges/setup-scripts/genflag.py` for the flag
* Use `challenges/templates/challenge` for your directory structure
* Use `challenges/templates/*` for the relevant challenge type

## Tools

Add any tools/scripts for the challenge category

### pwn

* pwntools (https://github.com/Gallopsled/pwntools)
* pwndbg (https://github.com/pwndbg/pwndbg)
* ppp (./tools/pwn/ppp.py)

### reversing

* radare2 (https://github.com/radare/radare2)
* angr (https://github.com/angr/angr)
* z3 (https://github.com/Z3Prover/z3)
* binary ninja (https://binary.ninja/)
* IDA 7

### crypto


