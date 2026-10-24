"""Renumber the manuscript references in order of first citation in the main body (Abstract to Methods), with
references cited only in figure captions after them and those cited only in the Supplementary Information last,
and rewrite every citation in the main text, the main figure captions and the Supplementary Information to the new
numbers. The reference list is reordered to match.

    python tools/renumber_references.py          # rewrites the three files in place (line endings preserved)
    python tools/renumber_references.py --check  # exit 1 if a renumbering is needed

The citation forms are those of tools/audit_live_manuscript_truth.py: [n], [n,m], [n–m] and "ref. n".
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAIN = ROOT / "docs/MANUSCRIPT_MAIN_TEXT.md"
CAPS = ROOT / "docs/MAIN_FIGURE_CAPTIONS.md"
SI = ROOT / "docs/SUPPLEMENTARY_INFORMATION.md"
CIT = re.compile(r"\[(\d+(?:\s*[–-]\s*\d+)?(?:\s*,\s*\d+(?:\s*[–-]\s*\d+)?)*)\]|\b(refs?\.\s*)(\d+)")
HEAD = "## Working references"


def expand(group):
    out = []
    for part in group.split(","):
        ends = [int(x) for x in re.split(r"\s*[–-]\s*", part.strip())]
        out.extend(range(ends[0], ends[-1] + 1))
    return out


def cited(s):
    out = []
    for m in CIT.finditer(s):
        out.extend([int(m.group(3))] if m.group(3) else expand(m.group(1)))
    return out


def first_order(seq):
    seen = []
    for n in seq:
        if n not in seen:
            seen.append(n)
    return seen


def compress(nums):
    nums = sorted(set(nums))
    parts, i = [], 0
    while i < len(nums):
        j = i
        while j + 1 < len(nums) and nums[j + 1] == nums[j] + 1:
            j += 1
        if j - i >= 2:
            parts.append(f"{nums[i]}–{nums[j]}")
        else:
            parts.extend(str(n) for n in nums[i:j + 1])
        i = j + 1
    return ",".join(parts)


def rewrite(s, mp):
    def sub(m):
        if m.group(3):
            return m.group(2) + str(mp[int(m.group(3))])
        return "[" + compress(mp[n] for n in expand(m.group(1))) + "]"
    return CIT.sub(sub, s)


def main():
    raw = {p: p.read_bytes().decode("utf-8") for p in (MAIN, CAPS, SI)}
    body, refs = raw[MAIN].split(HEAD, 1)
    entries = re.findall(r"^(\d+)\.\s(.*?)$", refs, re.M)
    ids = [int(n) for n, _ in entries]
    order = first_order(cited(body))
    cap_only = [n for n in first_order(cited(raw[CAPS])) if n not in order]
    # references that only the Supplementary Information cites stay in the pool after the main list; the manuscript
    # builder leaves them out and the SI builder numbers its own list
    si_only = [n for n in first_order(cited(raw[SI])) if n not in order and n not in cap_only]
    new_order = order + cap_only + si_only
    missing = sorted(set(ids) - set(new_order))
    assert not missing, f"listed but never cited: {missing}"
    assert set(new_order) <= set(ids), sorted(set(new_order) - set(ids))
    mp = {old: k + 1 for k, old in enumerate(new_order)}
    if all(mp[n] == n for n in ids):
        print("references already in order of first citation")
        return 0
    if "--check" in sys.argv:
        print("renumbering needed:", {o: n for o, n in mp.items() if o != n})
        return 1
    text = dict(entries)
    nl = "\r\n" if "\r\n" in refs else "\n"
    lines = [f"{mp[old]}. {text[str(old)].rstrip(chr(13))}" for old in new_order]
    pre = refs[:refs.index(entries[0][0] + ". ")]
    last = refs.rstrip("\r\n").rsplit(nl, 1)[-1]
    tail = refs[refs.index(last) + len(last):]
    new_refs = pre + nl.join(lines) + tail
    out = {MAIN: rewrite(body, mp) + HEAD + new_refs, CAPS: rewrite(raw[CAPS], mp), SI: rewrite(raw[SI], mp)}
    for p, s in out.items():
        p.write_bytes(s.encode("utf-8"))
    print("renumbered:", {o: n for o, n in mp.items() if o != n})
    return 0


if __name__ == "__main__":
    sys.exit(main())
