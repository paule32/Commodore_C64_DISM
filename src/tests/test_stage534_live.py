"""Windows integration smoke test: repeat a Pascal EXE and capture crashes.

Example:
    py -3 test_stage534_live.py runtime/pascal/test/pe32/test_raise.exe -n 100
The test provides one newline for the example's final ReadLn.
"""
import argparse
import subprocess
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('exe', type=Path)
    parser.add_argument('-n', '--iterations', type=int, default=30)
    parser.add_argument('--timeout', type=float, default=12)
    parser.add_argument('--log', type=Path, default=Path('stage534_windows_test.log'))
    args = parser.parse_args()
    exe = args.exe.expanduser().resolve()
    if not exe.is_file():
        parser.error(f'EXE nicht gefunden: {exe}')
    expected = ['xxxxxxx', 'TFoo Destroy', 'TFaz Destroy', 'ennndddeee',
                'nach APPLICATION', 'freee APP']
    failure_count = 0
    with args.log.open('w', encoding='utf-8') as log:
        for i in range(1, args.iterations + 1):
            try:
                result = subprocess.run([str(exe)], cwd=exe.parent,
                    input='\n', text=True, encoding='cp1252', errors='replace',
                    stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                    timeout=args.timeout)
                output = result.stdout or ''
                found = [output.find(text) for text in expected]
                ok = result.returncode == 0 and all(n >= 0 for n in found) and found == sorted(found)
                if not ok:
                    failure_count += 1
                marker = 'OK' if ok else 'FEHLER'
                log.write(f'=== Lauf {i}: {marker}, exit={result.returncode} ===\n{output}\n')
            except subprocess.TimeoutExpired as exc:
                failure_count += 1
                marker = 'TIMEOUT'
                log.write(f'=== Lauf {i}: {marker}, {exc} ===\n')
            print(f'{i}/{args.iterations}: {marker}')
    print(f'Fehler: {failure_count}, Protokoll: {args.log.resolve()}')
    return 1 if failure_count else 0


if __name__ == '__main__':
    sys.exit(main())
