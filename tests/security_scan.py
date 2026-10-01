"""Conservative source-tree secret checks; not a certification or a credential detector."""
from pathlib import Path
import re
import subprocess

PATTERNS = [r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----',
            r'\bAKIA[0-9A-Z]{16}\b', r'\bgh[pousr]_[A-Za-z0-9]{30,}\b',
            r'\bgithub_pat_[A-Za-z0-9_]{50,}\b', r'\bsk-[A-Za-z0-9]{40,}\b',
            r'(?i)(?:password|api_key|client_secret)\s*[:=]\s*["\'][^"\'\s]{12,}["\']']


def main():
    files=subprocess.check_output(['git','ls-files','--cached','--others','--exclude-standard'],text=True).splitlines()
    hits=[]
    for name in files:
        path=Path(name)
        if path.suffix.lower() in ('.png','.jpg','.ico','.sqlite') or not path.is_file():continue
        content=path.read_text(encoding='utf-8',errors='replace')
        for pattern in PATTERNS:
            if re.search(pattern,content):hits.append(name)
        if path.name=='.env' or path.suffix in ('.pem','.key','.pfx'):hits.append(name)
    if hits:raise SystemExit('Potential secret material; inspect files without logging values: '+', '.join(sorted(set(hits))))
    print(f'PASS: {len(files)} tracked/nonignored files checked for configured credential patterns; values not logged')

if __name__=='__main__':main()
