#!/usr/bin/env python3
import sys
import json

data = json.load(sys.stdin)

for key, value in data.items():
    print(f"{key.lower()}: {value}")

