import sys
from secrets import token_hex
if len(sys.argv) < 2:
    print("Usage: python generate_passphrase.py <number of bytes>")
    sys.exit(1)
print(token_hex(int(sys.argv[1])))

