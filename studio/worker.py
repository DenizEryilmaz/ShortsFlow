"""Single GPU worker, independent of browser and API request lifetimes."""
import argparse
import os
import subprocess
import sys
import time
from pathlib import Path

from dotenv import load_dotenv

from .store import Store


def start(root):
    root = Path(root).resolve()
    root.mkdir(parents=True, exist_ok=True)
    with (root / 'worker.log').open('a', encoding='utf-8') as log:
        subprocess.Popen(
            [sys.executable, '-m', 'studio.worker', str(root)],
            cwd=Path(__file__).resolve().parents[1],
            stdout=log,
            stderr=subprocess.STDOUT,
            creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0),
        )


def work(root):
    store = Store(root)
    lock = (store.root / 'worker.lock').open('a+b')
    lock.seek(0)
    lock.write(b'0')
    lock.flush()
    lock.seek(0)
    try:
        if os.name == 'nt':
            import msvcrt
            msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        lock.close()
        return
    # Holding the OS lock proves no other studio worker can own these jobs.
    with store.connect() as db:
        db.execute("UPDATE jobs SET status='queued',error=NULL WHERE status='running'")
    from .pipeline import execute
    from .providers import JobCancelled, ResourceWait
    try:
        while True:
            job = store.claim()
            if job is None:
                time.sleep(2)
                continue
            try:
                result = execute(store, job)
                store.finish(job['id'], 'completed', result)
                store.event(job['id'], 'Tamamlandı.')
            except JobCancelled:
                store.finish(job['id'], 'failed', error='Kullanıcı tarafından iptal edildi.')
                store.event(job['id'], 'Üretim iptal edildi.')
            except ResourceWait as error:
                store.finish(job['id'], 'queued', error=str(error))
                store.event(job['id'], str(error))
                time.sleep(20)
            except Exception as error:
                store.finish(job['id'], 'failed', error=str(error)[-4000:])
                store.event(job['id'], str(error)[-2000:])
    finally:
        lock.close()


if __name__ == '__main__':
    load_dotenv(Path(__file__).resolve().parents[1] / '.env')
    parser = argparse.ArgumentParser()
    parser.add_argument('root', type=Path)
    work(parser.parse_args().root)
