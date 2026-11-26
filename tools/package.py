"""Deterministic, allowlisted distribution builds. Python standard library only."""
import argparse
import hashlib
import re
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / 'skills' / 'skill-lifecycle-management'
FILES = (
    'SKILL.md', 'README.md', 'CHANGELOG.md', 'adapters/teleagent.md',
    'assets/feedback.example.json', 'assets/proposal.example.json', 'assets/task.example.json',
    'references/execution-protocol.md', 'references/protocol.md', 'scripts/slm.py',
    'specs/constitution.md', 'specs/plan.md', 'specs/protocol.md', 'specs/spec.md', 'specs/tasks.md',
    'tests/test_slm.py', 'tests/test_v020.py', 'tests/test_v021.py',
)

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, default=ROOT / 'dist')
    parser.add_argument('--tag', help='Require tag vVERSION to match core version')
    args = parser.parse_args()
    text = (SKILL / 'scripts/slm.py').read_text(encoding='utf-8')
    version = re.search(r"^VERSION = '([0-9]+\.[0-9]+\.[0-9]+)'$", text, re.M).group(1)
    if args.tag and args.tag != 'v' + version:
        parser.error('tag does not match core version')
    payload = {}
    for name in FILES:
        p = SKILL / name
        if p.is_symlink() or not p.is_file() or not p.resolve().is_relative_to(SKILL.resolve()):
            raise ValueError('Missing or unsafe file: ' + name)
        payload[name] = p.read_bytes()
    for name in ('LICENSE', 'NOTICE'):
        p = ROOT / name
        if p.is_file():
            if p.is_symlink(): raise ValueError('Unsafe ' + name)
            payload[name] = p.read_bytes()
    args.out.mkdir(parents=True, exist_ok=True)
    paths = []
    for teleagent in (False, True):
        target = args.out / ('skill-lifecycle-management-v' + version + ('-teleagent' if teleagent else '') + '.zip')
        with zipfile.ZipFile(target, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
            for name, data in sorted(payload.items()):
                filename = 'skill.md' if teleagent and name == 'SKILL.md' else name
                entry = zipfile.ZipInfo(filename, (2020, 1, 1, 0, 0, 0))
                entry.create_system = 3
                entry.external_attr = 0o100644 << 16
                entry.compress_type = zipfile.ZIP_DEFLATED
                z.writestr(entry, data, compresslevel=9)
        with zipfile.ZipFile(target) as z:
            assert z.testzip() is None
            assert ('skill.md' if teleagent else 'SKILL.md') in z.namelist()
            assert len(z.namelist()) == len(payload)
            assert target.stat().st_size < 50_000_000
        paths.append(target)
    manifest = ''.join(f'{sha(p)}  {p.name}\n' for p in paths)
    (args.out / 'SHA256SUMS.txt').write_bytes(manifest.encode('ascii'))
    print(manifest, end='')

if __name__ == '__main__':
    main()
