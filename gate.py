#!/usr/bin/env python3
"""Judge claim.json against LAW.md."""
import argparse, hashlib, json, subprocess, sys
from pathlib import Path

def commit(payload):
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(',', ':'), default=str).encode()).hexdigest()

def parse_laws(text):
    laws, current = {}, {}
    def flush():
        if not current: return
        law_id = current.get('id') or current.get('heading')
        if not law_id: return
        require = tuple(p.strip() for p in current.get('require', '').split(',') if p.strip())
        laws[law_id] = {'id': law_id, 'statement': current.get('statement', ''), 'check': current.get('check', 'none'), 'require': require}
    for raw in text.splitlines():
        line = raw.strip()
        if line.startswith('## '):
            flush(); current = {'heading': line[3:].strip()}; continue
        if line.startswith('- ') and ':' in line:
            key, value = line[2:].split(':', 1); current[key.strip()] = value.strip()
    flush(); return laws

def check_balance(evidence):
    start = int(evidence.get('opening_balance', 0)); running = start
    for amount in evidence.get('withdrawals', []):
        running -= int(amount)
        if running < 0:
            return {'opening_balance': start, 'withdrawal': int(amount), 'resulting_balance': running, 'broken_law': 'balance never negative'}
    return None

def check_email(evidence):
    for row in evidence.get('users_after_migration', []):
        if row.get('email') in (None, ''):
            return {'row_id': row.get('id'), 'email': row.get('email'), 'broken_law': 'users.email remains NOT NULL'}
    return None

def check_formula(evidence):
    for raw in evidence.get('samples', [0.5]):
        x = float(raw)
        if x * x < 2.0 * x:
            return {'x': x, 'left': x * x, 'right': 2.0 * x, 'broken_law': 'x^2 >= 2x for all real x'}
    return None

def check_facts(evidence):
    facts = evidence.get('facts')
    if not facts:
        return {'facts': facts, 'broken_law': 'SUCCESS/ALLOW requires non-empty facts'}
    return None

def check_consistency(evidence):
    score = float(evidence.get('consistency_score', 0))
    floor = float(evidence.get('consistency_floor', 0.70))
    if score < floor:
        return {'consistency_score': score, 'floor': floor, 'broken_law': 'consistency at or above floor for SUCCESS'}
    return None

def check_no_exfil(evidence):
    for call in evidence.get('outbound', []):
        dest = str(call.get('destination') or '')
        kind = str(call.get('kind') or '')
        if kind == 'model':
            continue
        if dest and dest not in ('browser-local', 'model'):
            return {'destination': dest, 'kind': kind, 'broken_law': 'notes stay in the browser except the model call'}
    return None

CHECKS = {
    'balance_never_negative': check_balance,
    'email_not_null': check_email,
    'formula_always_holds': check_formula,
    'facts_non_empty': check_facts,
    'consistency_floor': check_consistency,
    'no_exfil': check_no_exfil,
    'none': lambda _e: None,
}

def judge(law, claim):
    evidence = claim.get('evidence') or {}
    missing = [k for k in law['require'] if k not in evidence]
    if missing:
        return 'INCOMPLETE', {'missing_evidence': missing, 'producer_said_success': claim.get('claim_success')}
    checker = CHECKS.get(law['check'])
    if checker is None:
        return 'INCOMPLETE', {'unknown_check': law['check']}
    hit = checker(evidence)
    if hit:
        return 'REJECT', hit
    return 'ADMIT', None

def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('--claim', type=Path)
    parser.add_argument('--law', type=Path, default=Path('LAW.md'))
    parser.add_argument('--out', type=Path, default=Path('out'))
    parser.add_argument('--self-check', action='store_true')
    args = parser.parse_args(argv)
    here = Path(__file__).resolve().parent
    if args.self_check or args.claim is None:
        return subprocess.run([sys.executable, str(here / 'claimgate.py')]).returncode
    laws = parse_laws(args.law.read_text(encoding='utf-8'))
    claim = json.loads(args.claim.read_text(encoding='utf-8'))
    ids = claim.get('laws') or list(laws)
    overall, rank, rows = 'ADMIT', {'ADMIT': 0, 'INCOMPLETE': 1, 'REJECT': 2}, []
    for law_id in ids:
        law = laws.get(law_id)
        verdict, witness = ('INCOMPLETE', {'unknown_law': law_id}) if not law else judge(law, claim)
        if rank[verdict] > rank[overall]:
            overall = verdict
        rows.append((law_id, verdict, witness, commit({'law': law_id, 'verdict': verdict, 'witness': witness})))
    args.out.mkdir(parents=True, exist_ok=True)
    lines = ['## Claim Gate', '', f'**{overall}** — producer is untrusted. `claim_success` is not evidence.', '']
    for law_id, verdict, witness, receipt in rows:
        lines.append(f'### `{law_id}` — {verdict}')
        if witness:
            lines.append(f'- witness: `{json.dumps(witness)}`')
        lines.append(f'- receipt: `{receipt}`')
        lines.append('')
    if overall != 'ADMIT':
        lines.append('_Merge stays blocked until the law holds or the missing evidence arrives._')
    md = '\n'.join(lines) + '\n'
    (args.out / 'verdict.txt').write_text(overall + '\n')
    (args.out / 'comment.md').write_text(md)
    sys.stdout.write(md)
    return 0 if overall == 'ADMIT' else 1

if __name__ == '__main__':
    raise SystemExit(main())
