# SPDX-License-Identifier: GPL-3.0-or-later
"""Synthetic parity test; no disc, model or capture is needed."""
import struct
import subprocess
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / 'guests'))
from build_guest import _link_hair_two_sided
model = bytearray([0x5a]) * (0x80 + 17 * 0x50)
model[:4] = b'VMX.'
struct.pack_into('<H', model, 0x14, 17)
struct.pack_into('<I', model, 0x1c, 0x80)
for i in (3, 4): struct.pack_into('<I', model, 0x80 + i * 0x50, 0x08000002)
fixed = _link_hair_two_sided(model)
assert sum(a != b for a, b in zip(model, fixed)) == 2
assert _link_hair_two_sided(fixed) == fixed
assert subprocess.check_output([sys.argv[1], '--bytes']) == fixed
for bad in (0, 1, 2):
    broken = bytearray(model)
    if bad == 0: struct.pack_into('<H', broken, 0x14, 16)
    if bad == 1: struct.pack_into('<I', broken, 0x80 + 4 * 0x50, 7)
    if bad == 2: del broken[0x80 + 4 * 0x50:]
    before = bytes(broken)
    try:
        _link_hair_two_sided(broken)
    except (ValueError, struct.error): pass
    else: raise AssertionError('accepted malformed model')
    assert broken == before
print('PASS: C++/Python byte parity, scoped flags, idempotence and invalid input')
