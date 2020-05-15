#!/usr/bin/env python3

# Transform cookies.txt files (downloaded from browser extension)
# to cookies.pkl (format understood by the gphotos_deleter).

import pickle

COOKIE_KEYS = ["domain", "httpOnly", "path", "secure", "expiry", "name", "value"]
cookies = []

with open("cookies.txt", "r") as infile:
    for line in infile.read().split("\n"):

        # skip empty lines and comments
        if not line or line.startswith("#"):
            continue

        # create dict from values
        cookie = dict(zip(COOKIE_KEYS, line.split("\t")))

        # convert some values to booleans and integers
        cookie['httpOnly'] = cookie['httpOnly'] == "TRUE"
        cookie['secure'] = cookie['secure'] == "TRUE"
        cookie['expiry'] = int(cookie['expiry'])

        cookies.append(cookie)

with open("cookies.pkl", "wb") as ofile:
    pickle.dump(cookies, ofile)
