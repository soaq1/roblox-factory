# Reads what this game printed in Roblox Studio, out of Studio's own log file.
#   py game/tools/readlog.py                 the game's lines from the newest log
#   py game/tools/readlog.py --all           every warning and error too, ours or not
#   py game/tools/readlog.py --tail 40       only the last 40 matching lines
#   py game/tools/readlog.py --list          which log files there are, newest first
# Studio writes a log per session. Other plugins (F3X and the like) write there as well, so by
# default only this game's own marks are shown.
import argparse
import glob
import os
import re
import sys

FOLDERS = [
    os.path.expandvars(r"%LOCALAPPDATA%\Roblox\logs"),  # windows
    os.path.expanduser("~/Library/Logs/Roblox"),  # macos
]

# What this game prints. SELFTEST comes from server/SelfTest.luau, HANDVIEW from the temporary
# arm diagnostic in client/HandView.luau, "chat command from" from server/Commands.luau.
OURS = re.compile(r"SELFTEST|HANDVIEW|chat command from|did not start|FactorySelfTest")
# Roblox marks anything a game's own scripts print to the output window with these.
CREATOR = re.compile(r"FLog::(Creator|Output)")
NOISE = re.compile(r"StartPage|DiscoverBuildSeal|activation-eligibility|thumbnails\.roblox")


def logs() -> list:
    found = []
    for folder in FOLDERS:
        if os.path.isdir(folder):
            found += glob.glob(os.path.join(folder, "*Studio*.log"))
    return sorted(found, key=os.path.getmtime, reverse=True)


def clean(line: str) -> str:
    # Each line starts with a timestamp, elapsed seconds, thread ids and a channel; the message is
    # what comes after. Keep the clock time, drop the rest of the bookkeeping.
    match = re.match(r"^\S*?T(\d\d:\d\d:\d\d)\.\d+Z,[^,]*,[^,]*,[^,]*(?:,\w+)? \[[^\]]*\] ?(.*)$", line)
    if match:
        return match.group(1) + "  " + match.group(2)
    return line.rstrip("\n")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--all", action="store_true", help="every warning and error, not just ours")
    ap.add_argument("--tail", type=int, default=0, help="only the last N matching lines")
    ap.add_argument("--list", action="store_true", help="list the log files, newest first")
    ap.add_argument("--file", help="read this log file instead of the newest")
    args = ap.parse_args()

    found = logs()
    if args.list:
        for path in found[:12]:
            print(os.path.basename(path), os.path.getsize(path), "bytes")
        return 0
    path = args.file or (found[0] if found else None)
    if not path:
        print("No Studio log found. Looked in:", *FOLDERS, sep="\n  ")
        return 1

    print("# " + path)
    out = []
    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            if NOISE.search(line):
                continue
            if OURS.search(line) or (args.all and CREATOR.search(line)):
                out.append(clean(line))
    if args.tail:
        out = out[-args.tail :]
    for line in out:
        print(line)
    if not out:
        print("(nothing from the game in this log: has it been played yet?)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
