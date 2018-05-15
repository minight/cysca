#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import secrets

def main():
    flag = "FLAG{%s}" % (secrets.token_urlsafe(56))
    print(flag)

if __name__ == "__main__":
    main()
