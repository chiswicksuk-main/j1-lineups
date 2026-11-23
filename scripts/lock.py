"""Freeze the round at teamsheet time, for scoring later.

Usage: python scripts/lock.py [gw]
Copies final.csv to locked.csv with a timestamp. Replaces the manual
'GW15 SNAPSHOT' copies. Refuses to re-lock unless --force.
"""
import os
import shutil
import sys
from common import gw_path, current_gw, now_gmt

args = [a for a in sys.argv[1:] if not a.startswith("--")]
gw = int(args[0]) if args else current_gw()
dst = gw_path(gw, "locked.csv")
if os.path.exists(dst) and "--force" not in sys.argv:
    sys.exit(f"gw{gw:02d} already locked")
shutil.copyfile(gw_path(gw, "final.csv"), dst)
with open(gw_path(gw, "LOCKED_AT"), "w") as f:
    f.write(now_gmt() + " GMT\n")
print(f"gw{gw:02d} locked at {now_gmt()} GMT")
