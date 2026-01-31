
import os

filepath = "/Users/tomhoel/Documents/eurobonus/eurobonus/eurobonus/venv/lib/python3.14/site-packages/nodriver/cdp/network.py"

with open(filepath, 'rb') as f:
    content = f.read()

# Replace the problematic byte sequence \xb1 with +/- or just remove it
# In the output it looked like the character was at index corresponding to line 1365
# Let's do a more general replacement of the problematic line or the byte itself.
# Looking at the error: \xb1 is the problematic byte.

new_content = content.replace(b'\xb1', b'+/-')

with open(filepath, 'wb') as f:
    f.write(new_content)

print(f"Successfully patched {filepath}")
