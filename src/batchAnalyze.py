
import os
import sys
import time
import traceback
from pathlib import Path

from AnaylizeFenFile import analyzeFenFile


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
QIPU_DIR = REPO_ROOT / 'qipu'
LOG_PATH = REPO_ROOT / 'qipu' / 'batchAnalyze.log'


def listPending():
    pending = []
    for p in sorted(QIPU_DIR.iterdir()):
        if p.suffix != '.txt' or not p.is_file():
            continue
        csvPath = p.with_suffix('.csv')
        if csvPath.exists():
            continue
        pending.append(p)
    return pending


def logLine(msg):
    ts = time.strftime('%Y-%m-%d %H:%M:%S')
    line = f'[{ts}] {msg}\n'
    sys.stdout.write(line)
    sys.stdout.flush()
    with open(LOG_PATH, 'a') as f:
        f.write(line)


def main():
    pending = listPending()
    logLine(f'start: {len(pending)} pending')
    if not pending:
        return 0

    done = 0
    failed = 0
    t0 = time.time()
    for idx, txtPath in enumerate(pending, start=1):
        csvPath = txtPath.with_suffix('.csv')
        tmpPath = csvPath.with_suffix('.csv.partial')
        logLine(f'[{idx}/{len(pending)}] analyzing {txtPath.name} ...')
        try:
            stepT = time.time()
            analyzeFenFile(str(txtPath), str(tmpPath))
            os.rename(tmpPath, csvPath)
            done += 1
            logLine(f'  done in {time.time()-stepT:.1f}s (overall {(time.time()-t0)/60:.1f}min, done={done}/{len(pending)}, failed={failed})')
        except Exception as e:
            failed += 1
            logLine(f'  FAILED {txtPath.name}: {e}')
            logLine(traceback.format_exc())
            if tmpPath.exists():
                try:
                    os.remove(tmpPath)
                except Exception:
                    pass

    logLine(f'finished: done={done}, failed={failed}, total_time={(time.time()-t0)/60:.1f}min')
    return 0 if failed == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
