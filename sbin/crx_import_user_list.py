#!/usr/bin/python3
# Copyright (c) 2023 Peter Varkoly <pvarkoly@cephalix.eu> Nuremberg, Germany.  All rights reserved.
#
# Thin wrapper around cranix.user_import. The CRANIX Java API starts this
# script by its absolute path, so it must stay in /usr/sbin.

from cranix.user_import import main

if __name__ == "__main__":
    main()