"""Persistence, owner isolation, revision conflicts, standalone app and reproducible scene reuse."""
from concurrent.futures import ThreadPoolExecutor

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from studio.app import create_app
from studio.pipeline import build_character_prompt, cached_stage, resolve_prompt
from studio.routes import router
from studio.schema import Project
from studio.store import Conflict, Store


def test_revisions_and_immutable_snapshot_survive_reopen(tmp_path):
    store = Store(tmp_path)
    row = store.save('alice', 'project', {'name': 'First'})
    job = store.submit('alice', 'render', row['data'], row['id'])
    store.save('alice', 'project', {'name': 'Second'}, row['id'], 1)
    reopened = Store(tmp_path)
    assert reopened.job('alice', job['id'])['snapshot'] == {'name': 'First'}
    assert [r['data']['name'] for r in reopened.history('alice', row['id'])] == ['Second', 'First']
    with pytest.raises(Conflict):
        reopened.save('alice', 'project', {'name': 'Stale'}, row['id'], 1)
    assert reopened.get('bob', row['id']) is None
    assert reopened.job('bob', job['id']) is None


def test_only_one_worker_claims_a_job(tmp_path):
    store = Store(tmp_path)
    job = store.submit('alice', 'script', {})
    with ThreadPoolExecutor(4) as pool:
        claimed = list(pool.map(lambda _: Store(tmp_path).claim(), range(4)))
    assert [row['id'] for row in claimed if row] == [job['id']]
    assert store.job('alice', job['id'])['status'] == 'running'


def test_cached_scene_reused_only_for_same_owner_and_inputs(tmp_path):
    store = Store(tmp_path / 'state')
    job = store.submit('alice', 'render', {})
    target = tmp_path / 'take.png'
    calls = []

    def generate():
        calls.append(True)
        target.write_bytes(b'generated')

    cached_stage(store, job, target, {'seed': 1}, generate)
    target.unlink()
    cached_stage(store, job, target, {'seed': 1}, generate)
    assert len(calls) == 1
    target.unlink()
    cached_stage(store, job, target, {'seed': 2}, generate)
    assert len(calls) == 2
    target.unlink()
    other = store.submit('bob', 'render', {})
    cached_stage(store, other, target, {'seed': 1}, generate)
    assert len(calls) == 3


@pytest.fixture
def client(tmp_path, monkeypatch):
    async def owner(request):
        return request.headers.get('x-test-owner', 'alice')

    import studio.routes as routes
    monkeypatch.setattr(routes, 'start', lambda _: None)
    monkeypatch.setattr(routes, 'validate', lambda _, **kwargs: None)
    monkeypatch.setattr(routes, 'catalog', lambda: [])
    api, store = router(tmp_path, owner)
    app = FastAPI()
    app.include_router(api)
    return TestClient(app), store


def test_api_rejects_foreign_references_and_stale_writes(client):
    client, store = client
    other = store.save('bob', 'asset', {'name': 'private'})
    response = client.post('/api/studio/documents/character', json={'data': {'name': 'Hero', 'references': [other['id']]}})
    assert response.status_code == 404
    row = client.post('/api/studio/documents/project', json={'data': {'name': 'Story'}}).json()
    assert client.put(f'/api/studio/documents/{row["id"]}', json={'data': {'name': 'v2'}, 'revision': 1}).status_code == 200
    assert client.put(f'/api/studio/documents/{row["id"]}', json={'data': {'name': 'stale'}, 'revision': 1}).status_code == 409
    assert client.get(f'/api/studio/documents/{row["id"]}/revisions', headers={'x-test-owner': 'bob'}).status_code == 404


def test_scene_cast_and_job_input_are_validated(client):
    client, _ = client
    hero = client.post('/api/studio/documents/character', json={'data': {'name': 'Hero'}}).json()
    project = Project(name='Story').model_dump()
    project['script'] = {'title': 'Short', 'scenes': [{'id': '1', 'character_ids': [hero['id']]}]}
    assert client.post('/api/studio/documents/project', json={'data': project}).status_code == 422
    project['character_ids'] = [hero['id']]
    created = client.post('/api/studio/documents/project', json={'data': project})
    assert created.status_code == 200
    row = created.json()
    job = client.post(f'/api/studio/projects/{row["id"]}/jobs', json={'kind': 'script'}).json()
    assert job['snapshot']['characters'][0]['id'] == hero['id']


def test_resolve_prompt_supports_turkish_and_english_placeholders():
    project = Project(name='Test', brief='Yer çekimi', duration=10).model_dump()
    project['prompt_template'] = '{konu} | {duration} | {words}'
    assert resolve_prompt(project, []) == 'Yer çekimi | 10 | 18'


def test_standalone_app_health_and_library(tmp_path):
    app = create_app(tmp_path, start_background_worker=False)
    with TestClient(app) as client:
        health = client.get('/api/health')
        assert health.status_code == 200
        assert health.json()['status'] == 'ok'
        library = client.get('/api/studio/library')
        assert library.status_code == 200
        assert library.json() == {'series': [], 'project': [], 'character': [], 'template': []}


def test_build_character_prompt_translates_via_llm_and_falls_back(monkeypatch):
    import studio.pipeline as pipeline

    monkeypatch.setattr(pipeline.providers, 'release_script_model', lambda _m: None)
    monkeypatch.setattr(
        pipeline.llm,
        'generate_json',
        lambda prompt, schema, model=None: (
            {'visual_prompt': 'completely bald man with smooth hairless head', 'negative_prompt': 'hair, wig'},
            {},
        ),
    )
    prompt, negative = build_character_prompt(
        {'description': 'Kel adam', 'negative_prompt': 'hat', 'style': 'animation_2d'},
        model_id='qwen3-vl:8b-instruct',
    )
    assert 'completely bald man with smooth hairless head' in prompt
    assert 'hair' in negative and 'hat' in negative

    def fail(*_args, **_kwargs):
        raise RuntimeError('offline')

    monkeypatch.setattr(pipeline.llm, 'generate_json', fail)
    fallback_prompt, fallback_negative = build_character_prompt(
        {'description': 'Bald traveler', 'negative_prompt': '', 'style': 'animation_2d'},
        model_id='qwen3-vl:8b-instruct',
    )
    assert 'Bald traveler' in fallback_prompt
    assert 'multiple characters' in fallback_negative


def test_delete_character_detaches_from_project_and_deletes_jobs(client):
    client, store = client
    hero = client.post('/api/studio/documents/character', json={'data': {'name': 'Hero'}}).json()
    project = Project(name='Story', character_ids=[hero['id']]).model_dump()
    project['script'] = {
        'title': 'Short',
        'scenes': [{'id': '1', 'character_ids': [hero['id']], 'speaker_id': hero['id']}],
    }
    saved_project = client.post('/api/studio/documents/project', json={'data': project}).json()
    assert client.delete(f'/api/studio/documents/{hero["id"]}', headers={'x-test-owner': 'bob'}).status_code == 404
    deleted = client.delete(f'/api/studio/documents/{hero["id"]}')
    assert deleted.status_code == 200
    assert deleted.json()['kind'] == 'character'
    library = client.get('/api/studio/library').json()
    assert library['character'] == []
    updated_project = next(p for p in library['project'] if p['id'] == saved_project['id'])
    assert updated_project['data']['character_ids'] == []
    assert updated_project['data']['script']['scenes'][0]['character_ids'] == []
    assert updated_project['data']['script']['scenes'][0]['speaker_id'] == ''

    job = client.post(f'/api/studio/projects/{saved_project["id"]}/jobs', json={'kind': 'script'}).json()
    job_dir = store.root / 'jobs' / job['id']
    job_dir.mkdir(parents=True, exist_ok=True)
    (job_dir / 'dummy.txt').write_text('ok', encoding='utf-8')
    assert client.delete(f'/api/studio/jobs/{job["id"]}').status_code == 200
    assert not job_dir.exists()
    assert client.get(f'/api/studio/jobs/{job["id"]}').status_code == 404

    running_job = store.submit('alice', 'script', {}, saved_project['id'])
    store.claim()
    assert client.delete(f'/api/studio/jobs/{running_job["id"]}').status_code == 409


def test_staged_scene_production_and_full_mode(client, monkeypatch):
    client, store = client
    import studio.pipeline as pipeline

    project = Project(
        name='Staged Story',
        brief='A small clock floats in a room.',
        production_mode='staged',
        scene_count=2,
        episode_count=2,
        script={
            'title': 'Staged Story',
            'scenes': [
                {
                    'id': 's1',
                    'title': 'Opening',
                    'duration': 4,
                    'narration': 'Hello world.',
                    'visual_prompt': 'Orange clock in teal room',
                    'end_prompt': 'Clock moves right',
                    'shot_size': 'wide',
                    'camera_move': 'push',
                }
            ],
        },
    ).model_dump()
    saved = client.post('/api/studio/documents/project', json={'data': project}).json()

    # Validate scene stage checks
    assert client.post(f'/api/studio/projects/{saved["id"]}/jobs', json={'kind': 'scene_first'}).status_code == 422
    job_first = client.post(
        f'/api/studio/projects/{saved["id"]}/jobs',
        json={'kind': 'scene_first', 'scene_id': 's1'},
    )
    assert job_first.status_code == 200
    job_data = job_first.json()
    # Duplicate active request returns the existing queued job instead of duplicating
    dup_first = client.post(
        f'/api/studio/projects/{saved["id"]}/jobs',
        json={'kind': 'scene_first', 'scene_id': 's1'},
    )
    assert dup_first.status_code == 200
    assert dup_first.json()['id'] == job_data['id']

    monkeypatch.setattr(
        pipeline.providers,
        'generate_image',
        lambda prompt, neg, out, settings, refs=(), **_kw: out.write_bytes(b'\x89PNG\r\n\x1a\nfake'),
    )
    claimed = store.claim()
    result = pipeline.execute(store, claimed)
    store.finish(claimed['id'], 'completed', result)
    assert result['scene_id'] == 's1'
    assert result['first_asset']

    # Generated asset is attached to project scene and served as PNG
    refreshed = client.get('/api/studio/library').json()['project'][0]
    assert refreshed['data']['script']['scenes'][0]['first_asset'] == result['first_asset']
    asset_resp = client.get(f'/api/studio/assets/{result["first_asset"]}')
    assert asset_resp.status_code == 200
    assert asset_resp.headers['content-type'].startswith('image/png')

    # Full mode endpoint validation & prompt resolution with scene_count/episode_count
    resolved = resolve_prompt(saved['data'], [])
    assert 'Write exactly 2 scenes.' in resolved
    assert 'Total planned episodes: 2' in resolved

    # Script job excludes stale project script from snapshot and normalizes scene IDs + saves to project
    monkeypatch.setattr(pipeline.providers, 'release_script_model', lambda _m: None)
    monkeypatch.setattr(
        pipeline.llm,
        'generate_json',
        lambda prompt, schema, model=None, on_progress=None: (
            {
                'title': 'Arılar',
                'logline': 'Arılar olmasaydı doğa dururdu.',
                'recommended_duration': 10,
                'scenes': [
                    {
                        'title': 'Kovan',
                        'duration': 5,
                        'narration': 'Arılar uçar.',
                        'caption': 'Arılar uçar.',
                        'visual_prompt': 'Golden meadow with bees flying around blossoms',
                        'end_prompt': 'Bees vanish leaving silent still blossoms',
                        'motion_prompt': 'Slow pan across the meadow as bees fly away',
                    },
                    {
                        'title': 'Sessizlik',
                        'duration': 5,
                        'narration': 'Çiçekler solar.',
                        'caption': 'Sessiz tarla.',
                        'visual_prompt': 'Empty sunlit field without any bees',
                        'end_prompt': 'Wilted flowers under pale afternoon light',
                        'motion_prompt': 'Slow push-in toward a drooping flower',
                    },
                ],
            },
            {},
        ),
    )
    script_job = client.post(f'/api/studio/projects/{saved["id"]}/jobs', json={'kind': 'script'})
    assert script_job.status_code == 200
    assert script_job.json()['snapshot']['project']['script'] is None
    claimed_script = store.claim()
    script_res = pipeline.execute(store, claimed_script)
    store.finish(claimed_script['id'], 'completed', script_res)
    assert [s['id'] for s in script_res['script']['scenes']] == ['scene-01', 'scene-02']
    assert all(s['seed'] is None for s in script_res['script']['scenes'])
    latest_proj = client.get('/api/studio/library').json()['project'][0]
    assert latest_proj['data']['script']['title'] == 'Arılar'

    full_job = client.post(
        f'/api/studio/projects/{saved["id"]}/jobs',
        json={'kind': 'full', 'regenerate_script': True},
    )
    assert full_job.status_code == 200
    assert full_job.json()['snapshot']['regenerate_script'] is True
    assert full_job.json()['snapshot']['project']['script'] is None
    monkeypatch.setattr(pipeline, 'render', lambda *_args, **_kw: {'video': 'jobs/x/final.mp4', 'duration': 10.0, 'scenes': []})
    claimed_full = store.claim()
    full_res = pipeline.execute(store, claimed_full)
    assert full_res['script']['title'] == 'Arılar'
    assert full_res['video'] == 'jobs/x/final.mp4'


def test_wait_comfy_emits_node_phase_and_step_percentage(monkeypatch):
    import json
    import studio.providers as providers

    messages = [
        json.dumps({'type': 'executing', 'data': {'prompt_id': 'p1', 'node': '4'}}),
        json.dumps({'type': 'executing', 'data': {'prompt_id': 'p1', 'node': '10'}}),
        json.dumps({'type': 'progress', 'data': {'prompt_id': 'p1', 'value': 4, 'max': 8}}),
        json.dumps({'type': 'executing', 'data': {'prompt_id': 'p1', 'node': None}}),
    ]

    class FakeWS:
        def recv(self, timeout=None):
            return messages.pop(0)

    monkeypatch.setattr(
        providers,
        'comfy',
        lambda path, body=None: {'p1': {'status': {'status_str': 'success'}, 'outputs': {}}},
    )
    events = []
    graph = {
        '4': {'class_type': 'TextEncodeQwenImage21'},
        '10': {'class_type': 'SamplerCustomAdvanced'},
    }
    res = providers._wait_comfy('p1', graph, 'cid', FakeWS(), events.append)
    assert res['status']['status_str'] == 'success'
    assert any('Prompt ve referans kodlanıyor (CUDA)' in msg for msg in events)
    assert any('adım 4/8 (%50)' in msg for msg in events)


def test_styles_voices_cancel_and_scene_rewrite(client, monkeypatch):
    client, store = client
    import studio.pipeline as pipeline
    import studio.providers as providers

    styles_resp = client.get('/api/studio/styles')
    assert styles_resp.status_code == 200
    styles = styles_resp.json()['styles']
    assert len(styles) >= 8
    assert any(s['id'] == 'anime_cel' and s['sample_url'] for s in styles)

    voices_resp = client.get('/api/studio/voices/catalog')
    assert voices_resp.status_code == 200
    voices = voices_resp.json()['voices']
    assert any(v['id'] == 'tr_TR-fahrettin-medium' for v in voices)

    assert providers._parse_freevideo_line('{"event": "encoding_start"}')
    assert 'tahmini' in providers._parse_freevideo_line('│ Estimate  Engine 01:15–04:46 · sampling 00:52').lower()
    assert '%50' in providers._parse_freevideo_line('{"event": "step", "step": 4, "total_steps": 8}')

    project = Project(
        name='Rewrite Test',
        brief='Arılar yok olursa',
        style='anime_cel',
        script={
            'title': 'Arılar',
            'scenes': [
                {'id': 'scene-01', 'title': 'Kovan', 'duration': 5, 'narration': 'Arılar uçar.'},
                {'id': 'scene-02', 'title': 'Tekrar', 'duration': 5, 'narration': 'Aynı sahne.'},
            ],
        },
    ).model_dump()
    saved = client.post('/api/studio/documents/project', json={'data': project}).json()

    queued = client.post(
        f'/api/studio/projects/{saved["id"]}/jobs',
        json={'kind': 'scene_rewrite', 'scene_id': 'scene-02'},
    ).json()
    cancelled = client.post(f'/api/studio/jobs/{queued["id"]}/cancel')
    assert cancelled.status_code == 200
    assert cancelled.json()['status'] == 'failed'

    # Now run scene_rewrite cleanly
    monkeypatch.setattr(pipeline.providers, 'release_script_model', lambda _m: None)
    monkeypatch.setattr(
        pipeline.llm,
        'generate_json',
        lambda prompt, schema, model=None, on_progress=None: (
            {
                'title': 'Sessiz Bahçe',
                'duration': 5,
                'narration': 'Çiçekler arısız solmaya başlar.',
                'caption': 'Sessiz bahçe.',
                'visual_prompt': 'Quiet orchard with drooping apple blossoms in soft light',
                'end_prompt': 'Petals fall gently onto dry soil beneath still branches',
                'motion_prompt': 'Slow pull-back revealing the silent empty orchard',
            },
            {},
        ),
    )
    rewrite_job = client.post(
        f'/api/studio/projects/{saved["id"]}/jobs',
        json={'kind': 'scene_rewrite', 'scene_id': 'scene-02'},
    )
    assert rewrite_job.status_code == 200
    claimed = store.claim()
    res = pipeline.execute(store, claimed)
    assert res['title'] == 'Sessiz Bahçe'
    updated_proj = client.get('/api/studio/library').json()['project'][0]
    assert updated_proj['data']['script']['scenes'][0]['title'] == 'Kovan'
    assert updated_proj['data']['script']['scenes'][1]['title'] == 'Sessiz Bahçe'


def test_ingredients_bgm_aspect_ratios_and_export_zip(tmp_path):
    import zipfile
    import io
    import studio.pipeline as pipeline

    async def owner(_request):
        return 'alice'

    app = FastAPI()
    api, store = router(tmp_path, owner)
    app.include_router(api)
    client = TestClient(app)

    # 3. Ingredients: location & prop prompts + persistence
    loc = client.post(
        '/api/studio/documents/character',
        json={'data': {'name': 'Arı Kovanı', 'ingredient_type': 'location', 'description': 'Güneşli ahşap kovan', 'style': 'animation_2d'}},
    )
    assert loc.status_code == 200
    assert loc.json()['data']['ingredient_type'] == 'location'
    loc_prompt, _ = pipeline.build_character_prompt(loc.json()['data'])
    assert 'Environment location reference sheet' in loc_prompt

    prop = client.post(
        '/api/studio/documents/character',
        json={'data': {'name': 'Masa Saati', 'ingredient_type': 'prop', 'description': 'Turuncu vintage saat', 'style': 'science_2d'}},
    )
    assert prop.status_code == 200
    prop_prompt, _ = pipeline.build_character_prompt(prop.json()['data'])
    assert 'hero object and prop reference sheet' in prop_prompt

    # 5. BGM catalog + preview synthesis + audio/edit settings
    bgm_res = client.get('/api/studio/bgm')
    assert bgm_res.status_code == 200
    assert len(bgm_res.json()['tracks']) == 3
    preview = client.get('/api/studio/bgm/calm_ambient/preview')
    assert preview.status_code == 200
    assert preview.content[:4] == b'RIFF'

    # 6. Aspect ratio delivery dimensions + export.zip bundle
    assert pipeline._delivery_size({'aspect_ratio': '16:9'}) == (1920, 1080)
    assert pipeline._delivery_size({'aspect_ratio': '16:9-480p'}) == (854, 480)
    assert pipeline._delivery_size({'aspect_ratio': '1:1'}) == (1080, 1080)
    assert pipeline._delivery_size({'aspect_ratio': '9:16'}) == (1080, 1920)

    job = store.submit('alice', 'render', {'project': {'name': 'Export Test'}})
    jdir = store.root / 'jobs' / job['id']
    (jdir / 'assets').mkdir(parents=True, exist_ok=True)
    (jdir / 'final.mp4').write_bytes(b'fake-mp4')
    (jdir / 'captions.srt').write_text('1\n00:00:00,000 --> 00:00:03,000\nMerhaba\n', encoding='utf-8')
    (jdir / 'assets' / 'scene-01.mp4').write_bytes(b'fake-clip')

    zres = client.get(f'/api/studio/jobs/{job["id"]}/export.zip')
    assert zres.status_code == 200
    with zipfile.ZipFile(io.BytesIO(zres.content)) as zf:
        names = set(zf.namelist())
        assert 'final.mp4' in names
        assert 'captions.srt' in names
        assert 'scenes/scene-01.mp4' in names

    # 10 style 20s example projects (including realistic_35mm & documentary_4k)
    styles_res = client.get('/api/studio/styles').json()['styles']
    assert len(styles_res) == 10
    style_ids = {item['id'] for item in styles_res}
    assert 'realistic_35mm' in style_ids and 'documentary_4k' in style_ids
    for item in styles_res:
        ex = item['example']
        assert ex is not None
        assert ex['duration'] == 20
        assert len(ex['script']['scenes']) == 4
        assert sum(s['duration'] for s in ex['script']['scenes']) == 20
    created_ex = client.post('/api/studio/styles/noir_comic/example-project?language=en')
    assert created_ex.status_code == 200
    assert created_ex.json()['data']['style'] == 'noir_comic'
    assert created_ex.json()['data']['settings']['language'] == 'en'
    assert len(created_ex.json()['data']['script']['scenes']) == 4


def test_translate_scene_prompts_translates_turkish_and_skips_english(monkeypatch):
    import studio.pipeline as pipeline

    calls = []
    monkeypatch.setattr(pipeline.providers, 'release_script_model', lambda _m: None)

    def fake_llm(prompt, schema, model=None):
        calls.append(prompt)
        return (
            {
                'visual_prompt': 'Inside a sunlit wooden beehive with golden honeycombs',
                'end_prompt': 'Bees flying out from the hive entrance into the morning sun',
                'motion_prompt': 'Slow upward camera tilt as bees exit the hive',
                'negative_prompt': 'blurry, text',
            },
            {},
        )

    monkeypatch.setattr(pipeline.llm, 'generate_json', fake_llm)
    pipeline._PROMPT_TRANSLATION_CACHE.clear()

    # English scene skips LLM completely (0 calls)
    en_scene = {
        'visual_prompt': 'A cozy sunlit hilltop workshop with brass lanterns',
        'end_prompt': 'Lanterns glowing warmly at dusk',
        'motion_prompt': 'Slow smooth push-in',
        'negative_prompt': 'blurry, watermark',
    }
    assert pipeline.translate_scene_prompts(en_scene, 'qwen3-vl:8b-instruct') == en_scene
    assert len(calls) == 0

    # Turkish scene translates via LLM once, then hits cache on repeat
    tr_scene = {
        'visual_prompt': 'Güneşli ahşap arı kovanının içi, altın petekler',
        'end_prompt': 'Arılar sabah güneşine doğru kovandan çıkıyor',
        'motion_prompt': 'Kamera yavaşça yukarıya doğru hareket eder',
        'negative_prompt': 'bulanık, yazı',
    }
    out1 = pipeline.translate_scene_prompts(tr_scene, 'qwen3-vl:8b-instruct')
    assert out1['visual_prompt'] == 'Inside a sunlit wooden beehive with golden honeycombs'
    assert out1['motion_prompt'] == 'Slow upward camera tilt as bees exit the hive'
    assert len(calls) == 1

    # Second call uses cache (still 1 LLM call)
    out2 = pipeline.translate_scene_prompts(tr_scene, 'qwen3-vl:8b-instruct')
    assert out2 == out1
    assert len(calls) == 1


def test_series_migration_inheritance_queue_reorder_and_system_status(tmp_path):
    async def owner(_request):
        return 'alice'

    app = FastAPI()
    api, store = router(tmp_path, owner)
    app.include_router(api)
    client = TestClient(app)

    # Create legacy character & 2 projects sharing the same series name string (no series_id)
    char = client.post(
        '/api/studio/documents/character',
        json={'data': {'name': 'Barnaby', 'ingredient_type': 'character', 'description': 'Clay baker', 'style': 'clay_stopmotion'}},
    ).json()
    for ep in (1, 2):
        proj = Project(
            name=f'The Clockwork Bakery · Ep {ep:02d}',
            series='The Clockwork Bakery',
            episode=ep,
            duration=35,
            style='clay_stopmotion',
            character_ids=[char['id']],
        ).model_dump()
        assert client.post('/api/studio/documents/project', json={'data': proj}).status_code == 200

    # Calling /library auto-migrates legacy series string into a real Series document
    lib = client.get('/api/studio/library').json()
    assert len(lib['series']) == 1
    series = lib['series'][0]
    assert series['data']['name'] == 'The Clockwork Bakery'
    assert all(p['data']['series_id'] == series['id'] for p in lib['project'])
    assert series['id'] in lib['character'][0]['data']['series_ids']

    # Idempotent: calling /library again does NOT create duplicate series
    assert len(client.get('/api/studio/library').json()['series']) == 1

    # Creating a new episode via /series/{id}/episodes inherits style, duration, cast, and increments episode #
    ep3 = client.post(f'/api/studio/series/{series["id"]}/episodes', json={'name': 'Ep 03', 'brief': 'Flour storm'})
    assert ep3.status_code == 200
    assert ep3.json()['data']['episode'] == 3
    assert ep3.json()['data']['style'] == 'clay_stopmotion'
    assert ep3.json()['data']['character_ids'] == [char['id']]

    # Queue prioritization & estimation
    j1 = store.submit('alice', 'render', {'project': {'name': 'Ep 1', 'settings': {'image': 'flux2-klein-4b', 'video': 'freevideo-h3'}}})
    j2 = store.submit('alice', 'render', {'project': {'name': 'Ep 2', 'settings': {'image': 'flux2-klein-4b', 'video': 'freevideo-h3'}}})
    prio = client.post(f'/api/studio/queue/prioritize/{j2["id"]}')
    assert prio.status_code == 200
    claimed = store.claim()
    assert claimed['id'] == j2['id']

    est = client.get('/api/studio/estimate?episodes=5&scenes=6&image=flux2-klein-4b&video=freevideo-h3')
    assert est.status_code == 200
    assert est.json()['total_seconds'] > 0

    sys_st = client.get('/api/studio/system/status')
    assert sys_st.status_code == 200
    assert 'services' in sys_st.json() and 'hardware' in sys_st.json()


def test_longform_480p_hybrid_engine_estimate_and_lipsync_fallback(client, monkeypatch, tmp_path):
    client, store = client
    import studio.pipeline as pipeline
    import studio.providers as providers

    # Long-form 40-min 480p realistic project schema validation
    project = Project(
        name='Gece Nöbeti · Bölüm 01',
        style='realistic_35mm',
        duration=2400,
        scene_count=400,
        settings={
            'aspect_ratio': '16:9-480p',
            'width': 832,
            'height': 480,
            'video': 'ltxv-distilled',
        },
        script={
            'title': 'Gece Nöbeti',
            'scenes': [
                {'id': 's1', 'title': 'Giriş', 'scene_group': 'Sahne 1 · Hastane', 'shot_mode': 'camera', 'duration': 5, 'camera_move': 'push'},
                {'id': 's2', 'title': 'Soru', 'scene_group': 'Sahne 1 · Hastane', 'shot_mode': 'dialogue', 'duration': 5},
                {'id': 's3', 'title': 'Koşu', 'scene_group': 'Sahne 1 · Hastane', 'shot_mode': 'action', 'duration': 5},
                {'id': 's4', 'title': 'Final', 'scene_group': 'Sahne 1 · Hastane', 'shot_mode': 'hero', 'duration': 5},
                {'id': 's5', 'title': 'Otomatik', 'scene_group': 'Sahne 1 · Hastane', 'shot_mode': 'auto', 'duration': 5},
            ],
        },
    ).model_dump()
    saved = client.post('/api/studio/documents/project', json={'data': project})
    assert saved.status_code == 200
    scenes = saved.json()['data']['script']['scenes']
    assert scenes[0]['scene_group'] == 'Sahne 1 · Hastane'
    assert [s['shot_mode'] for s in scenes] == ['camera', 'dialogue', 'action', 'hero', 'auto']

    # Hybrid per-shot engine resolver
    snapshot = {
        'models': [
            {'id': 'ltxv-distilled', 'kind': 'video', 'ready': True},
            {'id': 'freevideo-h3', 'kind': 'video', 'ready': True},
        ]
    }
    settings = saved.json()['data']['settings']
    assert pipeline._resolve_shot_engine(scenes[0], settings, snapshot) == 'still-motion'
    assert pipeline._resolve_shot_engine(scenes[1], settings, snapshot) == 'lipsync'
    assert pipeline._resolve_shot_engine(scenes[2], settings, snapshot) == 'ltxv-distilled'
    assert pipeline._resolve_shot_engine(scenes[3], settings, snapshot) == 'freevideo-h3'
    assert pipeline._resolve_shot_engine(scenes[4], settings, snapshot) == 'ltxv-distilled'

    # Hybrid 480p ETA is dramatically faster than full non-hybrid 1080p FreeVideo
    est_hybrid = client.get('/api/studio/estimate?episodes=1&scenes=360&image=flux2-klein-4b&video=ltxv-distilled&aspect_ratio=16:9-480p&hybrid=true')
    est_full = client.get('/api/studio/estimate?episodes=1&scenes=360&image=flux2-klein-4b&video=freevideo-h3&aspect_ratio=16:9&hybrid=false')
    assert est_hybrid.status_code == 200 and est_full.status_code == 200
    assert est_hybrid.json()['total_seconds'] < est_full.json()['total_seconds'] / 4

    # Store job estimator recognizes hybrid per-shot mix
    job_sec = store.estimate_job_seconds('render', {'project': saved.json()['data']})
    assert job_sec > 0

    # Lip-sync falls back gracefully to camera_motion_video when STUDIO_LIPSYNC_CMD is unset
    monkeypatch.delenv('STUDIO_LIPSYNC_CMD', raising=False)
    assert providers.lipsync_configured() is False
    called = {}

    def fake_camera_motion(image, duration, out, settings, *, camera_move='static', log_path=None, cancel_check=None):
        called['camera_move'] = camera_move
        called['duration'] = duration
        out.write_bytes(b'fake-mp4')

    monkeypatch.setattr(providers, 'camera_motion_video', fake_camera_motion)
    out_mp4 = tmp_path / 'dialog.mp4'
    providers.lipsync_video(tmp_path / 'first.png', None, 5.0, out_mp4, settings)
    assert out_mp4.is_file()
    assert called['camera_move'] == 'static'
    assert called['duration'] == 5.0


def test_expand_scene_block_appends_shots_and_validates_limit(client, monkeypatch):
    client, _ = client
    import studio.routes as routes

    char = client.post(
        '/api/studio/documents/character',
        json={'data': {'name': 'Komiser Selim', 'ingredient_type': 'character', 'description': 'Weathered detective in trench coat', 'style': 'realistic_35mm'}},
    ).json()
    proj = Project(
        name='Karanlık Liman · Bölüm 01',
        style='realistic_35mm',
        duration=20,
        character_ids=[char['id']],
        settings={'aspect_ratio': '16:9-480p', 'width': 832, 'height': 480, 'language': 'tr'},
    ).model_dump()
    saved = client.post('/api/studio/documents/project', json={'data': proj}).json()

    monkeypatch.setattr(routes.providers, 'release_script_model', lambda _m: None)
    monkeypatch.setattr(
        routes.llm,
        'generate_json',
        lambda prompt, schema, model=None: (
            {
                'scene_group': 'Sahne 1 · Yağmurlu İskele',
                'shots': [
                    {
                        'title': 'İskele Genel',
                        'shot_mode': 'camera',
                        'duration': 5,
                        'narration': 'Yağmur limanın taşlarını yıkıyordu.',
                        'caption': 'Limanda yağmur.',
                        'shot_size': 'establishing',
                        'camera_move': 'pan_right',
                        'visual_prompt': 'Rainy misty harbor pier at dusk, 35mm cinema still',
                        'end_prompt': 'Pier lamps reflected in wet cobblestones',
                        'motion_prompt': 'Slow pan across foggy pier',
                        'character_ids': [char['id'], 'unknown-id'],
                        'speaker_id': 'unknown-id',
                    },
                    {
                        'title': 'Selim Yakın Plan',
                        'shot_mode': 'dialogue',
                        'duration': 5,
                        'narration': 'Bu dosyayı bu gece kapatıyoruz.',
                        'caption': 'Bu gece bitiyor.',
                        'shot_size': 'closeup',
                        'camera_move': 'static',
                        'visual_prompt': 'Close-up of Detective Selim under rain, shallow depth of field',
                        'end_prompt': 'Detective narrows eyes looking off-camera',
                        'motion_prompt': 'Subtle head turn and speech',
                        'character_ids': [char['id']],
                        'speaker_id': char['id'],
                    },
                    {
                        'title': 'Depo Kapısı',
                        'shot_mode': 'action',
                        'duration': 5,
                        'narration': 'Ağır demir kapı gıcırtıyla açıldı.',
                        'caption': 'Kapı açılıyor.',
                        'shot_size': 'medium',
                        'camera_move': 'tracking',
                        'visual_prompt': 'Detective pushing open rusty warehouse door',
                        'end_prompt': 'Door swings wide revealing dim warehouse interior',
                        'motion_prompt': 'Tracking shot following detective stepping inside',
                        'character_ids': [char['id']],
                        'speaker_id': '',
                    },
                    {
                        'title': 'Karanlık Koridor',
                        'shot_mode': 'hero',
                        'duration': 5,
                        'narration': 'İçeride sadece tek bir lamba yanıyordu.',
                        'caption': 'Tek bir ışık.',
                        'shot_size': 'wide',
                        'camera_move': 'push',
                        'visual_prompt': 'Long warehouse corridor lit by swinging tungsten bulb',
                        'end_prompt': 'Silhouette steps into the pool of light',
                        'motion_prompt': 'Slow push-in down atmospheric corridor',
                        'character_ids': [char['id']],
                        'speaker_id': '',
                    },
                ],
            },
            {},
        ),
    )

    resp = client.post(
        f'/api/studio/projects/{saved["id"]}/expand-block',
        json={
            'scene_group': 'Sahne 1 · Yağmurlu İskele',
            'summary': 'Komiser Selim yağmurlu iskelede depoya girer.',
            'duration': 20,
            'shot_count': 4,
            'hybrid': True,
        },
    )
    assert resp.status_code == 200
    payload = resp.json()
    assert len(payload['added_shots']) == 4
    assert payload['project']['revision'] == saved['revision'] + 1
    shots = payload['project']['data']['script']['scenes']
    assert len(shots) == 4
    assert all(s['scene_group'] == 'Sahne 1 · Yağmurlu İskele' for s in shots)
    assert [s['shot_mode'] for s in shots] == ['camera', 'dialogue', 'action', 'hero']
    # Foreign/unknown character_ids and speaker_id are stripped cleanly
    assert shots[0]['character_ids'] == [char['id']]
    assert shots[0]['speaker_id'] == ''
    assert shots[1]['speaker_id'] == char['id']
