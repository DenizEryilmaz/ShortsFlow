"""Owner-scoped documents and durable job snapshots in SQLite."""
import json
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path


def now():
    return datetime.now(timezone.utc).isoformat()


class Conflict(ValueError):
    pass


class Store:
    def __init__(self, root):
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        self.path = self.root / 'studio.sqlite3'
        with self.connect() as db:
            db.executescript('''
                CREATE TABLE IF NOT EXISTS documents (
                    id TEXT PRIMARY KEY, owner TEXT NOT NULL, kind TEXT NOT NULL,
                    revision INTEGER NOT NULL, data TEXT NOT NULL,
                    created TEXT NOT NULL, updated TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS studio_documents ON documents(owner, kind, updated);
                CREATE TABLE IF NOT EXISTS revisions (
                    id TEXT NOT NULL, revision INTEGER NOT NULL, data TEXT NOT NULL,
                    created TEXT NOT NULL, PRIMARY KEY(id, revision)
                );
                CREATE TABLE IF NOT EXISTS jobs (
                    id TEXT PRIMARY KEY, owner TEXT NOT NULL, project_id TEXT,
                    kind TEXT NOT NULL, status TEXT NOT NULL, snapshot TEXT NOT NULL,
                    result TEXT, error TEXT, created TEXT NOT NULL, updated TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS studio_jobs ON jobs(owner, created);
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY, job_id TEXT NOT NULL,
                    created TEXT NOT NULL, message TEXT NOT NULL
                );
            ''')

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.path, timeout=30)
        db.row_factory = sqlite3.Row
        try:
            db.execute('PRAGMA foreign_keys=ON')
            yield db
            db.commit()
        except BaseException:
            db.rollback()
            raise
        finally:
            db.close()

    @staticmethod
    def document(row):
        return {**dict(row), 'data': json.loads(row['data'])} if row else None

    def list(self, owner, kind):
        with self.connect() as db:
            return [self.document(r) for r in db.execute(
                'SELECT * FROM documents WHERE owner=? AND kind=? ORDER BY updated DESC', (owner, kind))]

    def get(self, owner, identifier):
        with self.connect() as db:
            return self.document(db.execute('SELECT * FROM documents WHERE owner=? AND id=?',
                                           (owner, identifier)).fetchone())

    def save(self, owner, kind, data, identifier=None, revision=None):
        identifier = identifier or str(uuid.uuid4())
        timestamp = now()
        encoded = json.dumps(data, ensure_ascii=False)
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            old = db.execute('SELECT * FROM documents WHERE id=?', (identifier,)).fetchone()
            if old and (old['owner'] != owner or old['kind'] != kind):
                raise LookupError('Kayıt bulunamadı.')
            if old and old['revision'] != revision:
                raise Conflict('Kayıt başka bir sekmede değişti. Yeniden açıp değişiklikleri uygulayın.')
            next_revision = old['revision'] + 1 if old else 1
            db.execute('INSERT OR REPLACE INTO documents VALUES(?,?,?,?,?,?,?)',
                       (identifier, owner, kind, next_revision, encoded,
                        old['created'] if old else timestamp, timestamp))
            db.execute('INSERT INTO revisions VALUES(?,?,?,?)', (identifier, next_revision, encoded, timestamp))
        return self.get(owner, identifier)

    def history(self, owner, identifier):
        if not self.get(owner, identifier):
            raise LookupError('Kayıt bulunamadı.')
        with self.connect() as db:
            return [dict(r, data=json.loads(r['data'])) for r in db.execute(
                'SELECT * FROM revisions WHERE id=? ORDER BY revision DESC', (identifier,))]

    def delete(self, owner, identifier):
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            row = db.execute('SELECT * FROM documents WHERE owner=? AND id=?', (owner, identifier)).fetchone()
            if not row or row['kind'] not in ('series', 'project', 'character', 'template'):
                raise LookupError('Kayıt bulunamadı.')
            timestamp = now()
            if row['kind'] == 'series':
                for kind_name in ('project', 'character'):
                    docs = db.execute(
                        'SELECT * FROM documents WHERE owner=? AND kind=?',
                        (owner, kind_name),
                    ).fetchall()
                    for doc in docs:
                        data = json.loads(doc['data'])
                        changed = False
                        if kind_name == 'project' and data.get('series_id') == identifier:
                            data['series_id'] = ''
                            changed = True
                        if kind_name == 'character' and identifier in data.get('series_ids', []):
                            data['series_ids'] = [sid for sid in data.get('series_ids', []) if sid != identifier]
                            changed = True
                        if changed:
                            encoded = json.dumps(data, ensure_ascii=False)
                            next_rev = doc['revision'] + 1
                            db.execute(
                                'UPDATE documents SET revision=?, data=?, updated=? WHERE id=?',
                                (next_rev, encoded, timestamp, doc['id']),
                            )
                            db.execute('INSERT INTO revisions VALUES(?,?,?,?)', (doc['id'], next_rev, encoded, timestamp))
            if row['kind'] == 'character':
                projects = db.execute(
                    "SELECT * FROM documents WHERE owner=? AND kind='project'",
                    (owner,),
                ).fetchall()
                for proj in projects:
                    data = json.loads(proj['data'])
                    changed = identifier in data.get('character_ids', [])
                    if changed:
                        data['character_ids'] = [cid for cid in data.get('character_ids', []) if cid != identifier]
                    script = data.get('script')
                    if script and script.get('scenes'):
                        for scene in script['scenes']:
                            if identifier in scene.get('character_ids', []):
                                scene['character_ids'] = [cid for cid in scene['character_ids'] if cid != identifier]
                                changed = True
                            if scene.get('speaker_id') == identifier:
                                scene['speaker_id'] = ''
                                changed = True
                    if changed:
                        encoded = json.dumps(data, ensure_ascii=False)
                        next_rev = proj['revision'] + 1
                        db.execute(
                            'UPDATE documents SET revision=?, data=?, updated=? WHERE id=?',
                            (next_rev, encoded, timestamp, proj['id']),
                        )
                        db.execute('INSERT INTO revisions VALUES(?,?,?,?)', (proj['id'], next_rev, encoded, timestamp))
                series_rows = db.execute(
                    "SELECT * FROM documents WHERE owner=? AND kind='series'",
                    (owner,),
                ).fetchall()
                for srow in series_rows:
                    sdata = json.loads(srow['data'])
                    if identifier in sdata.get('character_ids', []):
                        sdata['character_ids'] = [cid for cid in sdata['character_ids'] if cid != identifier]
                        encoded = json.dumps(sdata, ensure_ascii=False)
                        next_rev = srow['revision'] + 1
                        db.execute(
                            'UPDATE documents SET revision=?, data=?, updated=? WHERE id=?',
                            (next_rev, encoded, timestamp, srow['id']),
                        )
                        db.execute('INSERT INTO revisions VALUES(?,?,?,?)', (srow['id'], next_rev, encoded, timestamp))
            db.execute('DELETE FROM revisions WHERE id=?', (identifier,))
            db.execute('DELETE FROM documents WHERE id=? AND owner=?', (identifier, owner))
        return row['kind']

    def migrate_series(self, owner):
        """Idempotently promote legacy project.series text names into first-class series documents."""
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            series_rows = db.execute(
                "SELECT * FROM documents WHERE owner=? AND kind='series'",
                (owner,),
            ).fetchall()
            by_name = {json.loads(r['data']).get('name', '').strip().lower(): r['id'] for r in series_rows}
            proj_rows = db.execute(
                "SELECT * FROM documents WHERE owner=? AND kind='project' ORDER BY created ASC",
                (owner,),
            ).fetchall()
            grouped: dict[str, list[sqlite3.Row]] = {}
            for row in proj_rows:
                data = json.loads(row['data'])
                sname = (data.get('series') or '').strip()
                if sname and not data.get('series_id'):
                    grouped.setdefault(sname, []).append(row)
            if not grouped:
                return
            timestamp = now()
            char_rows = db.execute(
                "SELECT * FROM documents WHERE owner=? AND kind='character'",
                (owner,),
            ).fetchall()
            char_map = {r['id']: r for r in char_rows}
            for sname, rows in grouped.items():
                key = sname.lower()
                sid = by_name.get(key)
                all_cids: list[str] = []
                for r in rows:
                    for cid in json.loads(r['data']).get('character_ids', []):
                        if cid not in all_cids:
                            all_cids.append(cid)
                if not sid:
                    first_data = json.loads(rows[0]['data'])
                    script = first_data.get('script') or {}
                    cover = ''
                    for cid in all_cids:
                        if cid in char_map:
                            refs = json.loads(char_map[cid]['data']).get('references', [])
                            if refs:
                                cover = refs[0]
                                break
                    sid = str(uuid.uuid4())
                    series_data = {
                        'name': sname,
                        'logline': script.get('logline') or first_data.get('brief', '')[:300],
                        'tone': '',
                        'audience': '',
                        'style': first_data.get('style', 'animation_2d'),
                        'continuity_note': script.get('continuity_note', ''),
                        'cover_asset': cover,
                        'character_ids': all_cids,
                        'episode_duration': int(first_data.get('duration', 30)),
                        'episode_count': max(int(first_data.get('episode_count', 1)), len(rows)),
                        'defaults': first_data.get('settings', {}),
                    }
                    encoded = json.dumps(series_data, ensure_ascii=False)
                    db.execute('INSERT INTO documents VALUES(?,?,?,?,?,?,?)',
                               (sid, owner, 'series', 1, encoded, timestamp, timestamp))
                    db.execute('INSERT INTO revisions VALUES(?,?,?,?)', (sid, 1, encoded, timestamp))
                    by_name[key] = sid
                for r in rows:
                    pdata = json.loads(r['data'])
                    pdata['series_id'] = sid
                    encoded = json.dumps(pdata, ensure_ascii=False)
                    next_rev = r['revision'] + 1
                    db.execute(
                        'UPDATE documents SET revision=?, data=?, updated=? WHERE id=?',
                        (next_rev, encoded, timestamp, r['id']),
                    )
                    db.execute('INSERT INTO revisions VALUES(?,?,?,?)', (r['id'], next_rev, encoded, timestamp))
                for cid in all_cids:
                    crow = char_map.get(cid)
                    if not crow:
                        continue
                    cdata = json.loads(crow['data'])
                    sids = list(cdata.get('series_ids') or [])
                    if sid not in sids:
                        sids.append(sid)
                        cdata['series_ids'] = sids
                        encoded = json.dumps(cdata, ensure_ascii=False)
                        next_rev = crow['revision'] + 1
                        db.execute(
                            'UPDATE documents SET revision=?, data=?, updated=? WHERE id=?',
                            (next_rev, encoded, timestamp, crow['id']),
                        )
                        db.execute('INSERT INTO revisions VALUES(?,?,?,?)', (crow['id'], next_rev, encoded, timestamp))
                        char_map[cid] = db.execute('SELECT * FROM documents WHERE id=?', (cid,)).fetchone()

    def delete_job(self, owner, identifier):
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            row = db.execute('SELECT * FROM jobs WHERE id=? AND owner=?', (identifier, owner)).fetchone()
            if not row:
                raise LookupError('Üretim bulunamadı.')
            if row['status'] == 'running':
                raise Conflict('Çalışmakta olan üretim silinemez.')
            db.execute('DELETE FROM events WHERE job_id=?', (identifier,))
            db.execute('DELETE FROM jobs WHERE id=? AND owner=?', (identifier, owner))

    def submit(self, owner, kind, snapshot, project_id=None):
        identifier = str(uuid.uuid4())
        timestamp = now()
        with self.connect() as db:
            db.execute('INSERT INTO jobs VALUES(?,?,?,?,?,?,?,?,?,?)',
                       (identifier, owner, project_id, kind, 'queued', json.dumps(snapshot, ensure_ascii=False),
                        None, None, timestamp, timestamp))
        return self.job(owner, identifier)

    def job(self, owner, identifier):
        with self.connect() as db:
            row = db.execute('SELECT * FROM jobs WHERE id=? AND owner=?', (identifier, owner)).fetchone()
            if not row:
                return None
            result = dict(row)
            result['snapshot'] = json.loads(result['snapshot'])
            result['result'] = json.loads(result['result']) if result['result'] else None
            result['events'] = [dict(r) for r in db.execute(
                'SELECT created,message FROM (SELECT * FROM events WHERE job_id=? ORDER BY id DESC LIMIT 100) ORDER BY id',
                (identifier,))]
            return result

    @staticmethod
    def estimate_job_seconds(kind, snap):
        proj = snap.get('project') or {}
        settings = proj.get('settings') or snap.get('settings') or {}
        img = settings.get('image', 'flux2-klein-4b')
        vid = settings.get('video', 'freevideo-h3')
        img_sec = 24 if img == 'flux2-klein-4b' else 240
        vid_sec = 75 if vid in ('wan22-ti2v-5b', 'ltxv-distilled') else (5 if vid == 'still-motion' else 195)
        if kind in ('script', 'scene_rewrite'):
            return 25
        if kind == 'character':
            return img_sec
        if kind == 'style_sample':
            return img_sec
        if kind == 'style_demo':
            mode = snap.get('video_mode', 'balanced')
            if mode == 'still':
                return 4 * img_sec + 15
            if mode == 'ltxv':
                return 4 * (2 * 32 + 80) + 15
            if mode == 'balanced':
                return 4 * (2 * 32 + 290) + 15
            return 4 * (2 * 260 + 290) + 15
        if kind == 'scene_audio':
            return 4
        if kind in ('scene_first', 'scene_last'):
            return img_sec
        if kind == 'scene_clip':
            return vid_sec
        if kind == 'scene_all':
            return 2 * img_sec + vid_sec + 8
        scenes = (proj.get('script') or {}).get('scenes') or []
        n = max(1, len(scenes) or int(proj.get('scene_count') or 4))
        pending_cost = 0
        for sc in scenes:
            if not sc.get('first_asset'):
                pending_cost += img_sec
            if sc.get('end_prompt') and not sc.get('last_asset'):
                pending_cost += img_sec
            if not sc.get('clip_asset'):
                pending_cost += vid_sec
        if not scenes:
            pending_cost = n * (2 * img_sec + vid_sec)
        return pending_cost + 25

    def prioritize_job(self, owner, identifier):
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            target = db.execute(
                "SELECT id, status FROM jobs WHERE id=? AND owner=?",
                (identifier, owner),
            ).fetchone()
            if not target:
                raise LookupError('Üretim bulunamadı.')
            if target['status'] != 'queued':
                raise Conflict('Yalnızca sıradaki iş öne alınabilir.')
            earliest = db.execute(
                "SELECT MIN(created) AS m FROM jobs WHERE status='queued'"
            ).fetchone()['m']
            if earliest:
                dt = datetime.fromisoformat(earliest)
                from datetime import timedelta
                earlier = (dt - timedelta(seconds=5)).isoformat()
                db.execute('UPDATE jobs SET created=?, updated=? WHERE id=?', (earlier, now(), identifier))
        return self.job(owner, identifier)

    def reorder_queue(self, owner, job_ids):
        if not job_ids:
            return
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            queued = db.execute(
                "SELECT id, created FROM jobs WHERE owner=? AND status='queued' ORDER BY created ASC",
                (owner,),
            ).fetchall()
            if not queued:
                return
            from datetime import timedelta
            base = datetime.fromisoformat(queued[0]['created'])
            valid_ids = {r['id'] for r in queued}
            ordered = [jid for jid in job_ids if jid in valid_ids]
            ordered.extend(r['id'] for r in queued if r['id'] not in ordered)
            ts = now()
            for idx, jid in enumerate(ordered):
                slot = (base + timedelta(milliseconds=idx * 50)).isoformat()
                db.execute('UPDATE jobs SET created=?, updated=? WHERE id=? AND owner=?', (slot, ts, jid, owner))

    def jobs(self, owner):
        with self.connect() as db:
            rows = db.execute(
                '''SELECT id,project_id,kind,status,error,created,updated,result,snapshot,
                          (SELECT message FROM events WHERE job_id=jobs.id ORDER BY id DESC LIMIT 1) AS latest_event
                   FROM jobs WHERE owner=? ORDER BY created DESC LIMIT 250''',
                (owner,),
            ).fetchall()
            items = []
            for r in rows:
                item = dict(r)
                snap = json.loads(item.pop('snapshot') or '{}')
                item['result'] = json.loads(item['result']) if item.get('result') else None
                proj = snap.get('project') or {}
                label = proj.get('name', '')
                scene_id = snap.get('scene_id')
                if scene_id and proj.get('script'):
                    for idx, sc in enumerate(proj['script'].get('scenes', []), 1):
                        if sc.get('id') == scene_id:
                            label = f"{label} · Sahne {idx}: {sc.get('title') or 'Sahne'}"
                            break
                elif item['kind'] == 'character':
                    label = snap.get('character', {}).get('data', {}).get('name', 'Bileşen')
                elif item['kind'] == 'style_sample':
                    label = snap.get('style_name') or snap.get('style_id') or 'Stil örneği'
                elif item['kind'] == 'style_demo':
                    label = f"{snap.get('style_name') or snap.get('style_id')} · 20 sn Demo"
                item['label'] = label
                item['series_id'] = proj.get('series_id', '')
                item['series_name'] = proj.get('series', '')
                item['aspect_ratio'] = (proj.get('settings') or {}).get('aspect_ratio', '9:16')
                item['estimate_seconds'] = self.estimate_job_seconds(item['kind'], snap)
                items.append(item)
            return items

    def cancel_job(self, owner, identifier):
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            row = db.execute('SELECT status FROM jobs WHERE id=? AND owner=?', (identifier, owner)).fetchone()
            if not row:
                raise LookupError('Üretim bulunamadı.')
            timestamp = now()
            if row['status'] == 'queued':
                db.execute(
                    "UPDATE jobs SET status='failed', error=?, updated=? WHERE id=? AND owner=?",
                    ('Kullanıcı tarafından iptal edildi.', timestamp, identifier, owner),
                )
                db.execute(
                    'INSERT INTO events(job_id,created,message) VALUES(?,?,?)',
                    (identifier, timestamp, 'Üretim iptal edildi.'),
                )
            elif row['status'] == 'running':
                db.execute(
                    "UPDATE jobs SET error='__CANCEL_REQUESTED__', updated=? WHERE id=? AND owner=?",
                    (timestamp, identifier, owner),
                )
                db.execute(
                    'INSERT INTO events(job_id,created,message) VALUES(?,?,?)',
                    (identifier, timestamp, 'İptal istendi, işlem durduruluyor…'),
                )
            else:
                raise Conflict('Yalnızca sıradaki veya çalışan üretim iptal edilebilir.')
        return self.job(owner, identifier)

    def is_cancelled(self, identifier):
        with self.connect() as db:
            row = db.execute('SELECT status, error FROM jobs WHERE id=?', (identifier,)).fetchone()
            return row is None or row['error'] == '__CANCEL_REQUESTED__'

    def find_active_job(self, owner, project_id, kind, scene_id=None):
        with self.connect() as db:
            rows = db.execute(
                "SELECT id,snapshot FROM jobs WHERE owner=? AND project_id=? AND kind=? AND status IN ('queued','running') ORDER BY created DESC",
                (owner, project_id, kind),
            ).fetchall()
            for row in rows:
                snap = json.loads(row['snapshot'])
                if snap.get('scene_id') == scene_id:
                    return self.job(owner, row['id'])
        return None

    def running_job(self, owner):
        with self.connect() as db:
            row = db.execute(
                '''SELECT id,project_id,kind,status,snapshot,created,updated,
                          (SELECT message FROM events WHERE job_id=jobs.id ORDER BY id DESC LIMIT 1) AS latest_event
                   FROM jobs WHERE owner=? AND status='running' ORDER BY updated DESC LIMIT 1''',
                (owner,),
            ).fetchone()
            if not row:
                return None
            snap = json.loads(row['snapshot'])
            scene_id = snap.get('scene_id')
            scene_title = ''
            if scene_id and snap.get('project', {}).get('script', {}):
                for idx, item in enumerate(snap['project']['script'].get('scenes', []), 1):
                    if item.get('id') == scene_id:
                        scene_title = f"Sahne {idx}: {item.get('title') or 'Sahne'}"
                        break
            return {
                'id': row['id'],
                'kind': row['kind'],
                'project_id': row['project_id'],
                'project_name': snap.get('project', {}).get('name', ''),
                'scene_id': scene_id,
                'scene_title': scene_title,
                'latest_event': row['latest_event'] or 'Üretiliyor…',
                'created': row['created'],
                'updated': row['updated'],
            }

    def claim(self):
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            row = db.execute("SELECT * FROM jobs WHERE status='queued' ORDER BY created LIMIT 1").fetchone()
            if not row:
                return None
            db.execute("UPDATE jobs SET status='running',updated=? WHERE id=?", (now(), row['id']))
            identifier, owner = row['id'], row['owner']
        return self.job(owner, identifier)

    def finish(self, identifier, status, result=None, error=None):
        with self.connect() as db:
            db.execute('UPDATE jobs SET status=?,result=?,error=?,updated=? WHERE id=?',
                       (status, json.dumps(result, ensure_ascii=False) if result else None, error, now(), identifier))

    def event(self, identifier, message):
        with self.connect() as db:
            db.execute('INSERT INTO events(job_id,created,message) VALUES(?,?,?)',
                       (identifier, now(), str(message)[-2000:]))
            db.execute('UPDATE jobs SET updated=? WHERE id=?', (now(), identifier))
