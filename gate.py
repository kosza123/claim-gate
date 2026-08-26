#!/usr/bin/env python3
import argparse, hashlib, json, sys
from pathlib import Path

def commit(x):
    return hashlib.sha256(json.dumps(x, sort_keys=True, separators=(',', ':'), default=str).encode()).hexdigest()

def parse_laws(text):
    laws, cur = {}, {}
    def flush():
        if not cur: return
        lid = cur.get('id') or cur.get('heading')
        if not lid: return
        req = tuple(p.strip() for p in cur.get('require', '').split(',') if p.strip())
        laws[lid] = {'id': lid, 'statement': cur.get('statement', ''), 'check': cur.get('check', 'none'), 'require': req}
    for raw in text.splitlines():
        line = raw.strip()
        if line.startswith('## '):
            flush(); cur = {'heading': line[3:].strip()}; continue
        if line.startswith('- ') and ':' in line:
            k, v = line[2:].split(':', 1); cur[k.strip()] = v.strip()
    flush(); return laws

def check_balance(ev):
    start = int(ev.get('opening_balance', 0)); run = start
    for w in ev.get('withdrawals', []):
        run -= int(w)
        if run < 0:
            return {'opening_balance': start, 'withdrawal': int(w), 'resulting_balance': run, 'broken_law': 'balance never negative'}
    return None

CHECKS = {'balance_never_negative': check_balance, 'email_not_null': lambda ev: None, 'formula_always_holds': lambda ev: None, 'none': lambda ev: None}

def judge(law, claim):
    ev = claim.get('evidence') or {}
    missing = [k for k in law['require'] if k not in ev]
    if missing:
        return 'INCOMPLETE', {'missing_evidence': missing, 'producer_said_success': claim.get('claim_success')}
    fn = CHECKS.get(law['check']) or (lambda e: None)
    hit = fn(ev)
    if hit:
        return 'REJECT', hit
    return 'ADMIT', None

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--claim', type=Path)
    p.add_argument('--law', type=Path, default=Path('LAW.md'))
    p.add_argument('--out', type=Path, default=Path('out'))
    p.add_argument('--self-check', action='store_true')
    args = p.parse_args()
    here = Path(__file__).resolve().parent
    if args.self_check or args.claim is None:
        import subprocess
        return subprocess.run([sys.executable, str(here / 'claimgate.py')]).returncode
    laws = parse_laws(args.law.read_text())
    claim = json.loads(args.claim.read_text())
    ids = claim.get('laws') or list(laws)
    overall, rows = 'ADMIT', []
    rank = {'ADMIT': 0, 'INCOMPLETE': 1, 'REJECT': 2}
    for lid in ids:
        law = laws.get(lid)
        v, w = ('INCOMPLETE', {'unknown_law': lid}) if not law else judge(law, claim)
        if rank[v] > rank[overall]:
            overall = v
        rows.append((lid, v, w, commit({'law': lid, 'verdict': v, 'witness': w})))
    args.out.mkdir(parents=True, exist_ok=True)
    lines = ['## Claim Gate', '', f'**{overall}** — producer is untrusted.', '']
    for lid, v, w, rec in rows:
        lines.append(f'### `{lid}` — {v}')
        if w: lines.append(f'- witness: `{json.dumps(w)}`')
        lines.append(f'- receipt: `{rec}`')
        lines.append('')
    if overall != 'ADMIT':
        lines.append('_Merge stays blocked._')
    md = '\n'.join(lines) + '\n'
    (args.out / 'verdict.txt').write_text(overall + '\n')
    (args.out / 'comment.md').write_text(md)
    sys.stdout.write(md)
    return 0 if overall == 'ADMIT' else 1

if __name__ == '__main__':
    raise SystemExit(main())
