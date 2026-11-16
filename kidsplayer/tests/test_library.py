import asyncio
import ast
import json
import importlib.util
from pathlib import Path
import sys
import types
import unittest
from types import SimpleNamespace as NS
from unittest.mock import AsyncMock
import yaml

ROOT = Path(__file__).resolve().parents[1]
def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'backend/custom_components/kidsplayer' / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module
model = load('library')
Playback = load('playback').Playback
sys.modules['music_assistant_models'] = types.ModuleType('music_assistant_models')
enums = types.ModuleType('music_assistant_models.enums')
enums.QueueOption = NS(REPLACE='replace')
enums.RepeatMode = NS(OFF='off')
sys.modules[enums.__name__] = enums

def config():
    return {'libraries': {'child': {'version': 1, 'player': 'media_player.child', 'categories': [
        {'id': 'robin', 'title': 'Robin', 'episodes': [
            {'id': 'ep1', 'title': 'Episode 1', 'playback': {'items': [{'uri': 'apple_music://track/test1'}]}}
        ]},
        {'id': 'conni', 'title': 'Conni', 'episodes': [
            {'id': 'ep1', 'title': 'Episode 1', 'playback': {'items': [{'uri': 'library://album/1'}]}}
        ]},
    ]}}}

def parse(data):
    return model.parse(yaml.safe_dump(data))

class LibraryTests(unittest.TestCase):
    def test_valid(self):
        self.assertEqual(parse(config())['child'].categories[0].episodes[0].items, ('apple_music://track/test1',))

    def test_invalid_yaml(self):
        with self.assertRaises(model.ConfigError): model.parse('libraries: [')

    def test_duplicate_yaml_key(self):
        with self.assertRaises(model.ConfigError): model.parse('libraries: {}\nlibraries: {}')

    def test_bad_shapes(self):
        for categories in ([], None, {}, 'x'):
            data = config(); data['libraries']['child']['categories'] = categories
            with self.subTest(categories=categories), self.assertRaises(model.ConfigError): parse(data)

    def test_empty_episodes(self):
        data = config(); data['libraries']['child']['categories'][0]['episodes'] = []
        with self.assertRaises(model.ConfigError): parse(data)

    def test_duplicates(self):
        for field in ('categories', 'episodes'):
            data = config(); cats = data['libraries']['child']['categories']
            entries = cats if field == 'categories' else cats[0]['episodes']
            entries.append(entries[0])
            with self.subTest(field=field), self.assertRaises(model.ConfigError): parse(data)

    def test_unknown_field(self):
        data = config(); data['libraries']['child']['typo'] = True
        with self.assertRaises(model.ConfigError): parse(data)

    def test_uri_validation(self):
        for uri in ('', 'Robin Hood', 'https://example.org/file.mp3', 'apple_music://track/PLACEHOLDER_ID', 'apple_music://album/a b'):
            data = config(); data['libraries']['child']['categories'][0]['episodes'][0]['playback']['items'] = [{'uri': uri}]
            with self.subTest(uri=uri), self.assertRaises(model.ConfigError): parse(data)

    def test_cover_traversal(self):
        for value in ('../private.jpg', '/etc/passwd', 'https://example.org/a.jpg'):
            data = config(); data['libraries']['child']['categories'][0]['cover'] = value
            with self.assertRaises(model.ConfigError): parse(data)

    def test_large(self):
        data = config(); ep = data['libraries']['child']['categories'][0]['episodes'][0]
        ep['playback']['items'] = [{'uri': 'filesystem_local://track/test%s.mp3' % i} for i in range(100)]
        self.assertEqual(len(parse(data)['child'].categories[0].episodes[0].items), 100)
        with self.assertRaises(model.ConfigError): model.parse('x' * (model.MAX_BYTES + 1))

    def test_navigation_and_independence(self):
        lib = parse(config())['child']
        a = model.window(lib, '', 1)
        b = model.window(lib, '', 0)
        self.assertEqual(a[2][1].id, 'conni')
        self.assertEqual(b[2][1].id, 'robin')
        self.assertEqual(model.window(lib, 'robin', 7)[2][1].id, 'ep1')
        self.assertEqual(model.window(lib, '', a[0])[2][1].id, 'conni')
        self.assertEqual(model.window(lib, '', -1)[0], 1)
        with self.assertRaises(model.ConfigError): model.window(lib, 'removed', 0)

class PlaybackTests(unittest.IsolatedAsyncioTestCase):
    def client(self):
        q = NS(get_active_queue=AsyncMock(return_value=NS(queue_id='queue')), repeat=AsyncMock(), autoplay=AsyncMock(), play_media=AsyncMock())
        return NS(music=NS(get_item_by_uri=AsyncMock(), get_album_tracks=AsyncMock()), player_queues=q)

    def track(self, uri, disc=1, number=1, available=True):
        return NS(uri=uri, available=available, media_type='track', disc_number=disc, track_number=number)

    async def run_episode(self, uris):
        client = self.client()
        client.music.get_item_by_uri.side_effect = [self.track(uri) for uri in uris]
        await Playback().start(client, 'player', NS(items=uris), 'kind1')
        call = client.player_queues.play_media.call_args.kwargs
        self.assertEqual([t.uri for t in call['media']], uris)
        self.assertEqual(call['option'], 'replace')
        self.assertIs(call['shuffle'], False)
        self.assertIs(call['radio_mode'], False)
        self.assertEqual(call['user'], 'kind1')
        client.player_queues.play_media.assert_awaited_once()
        client.player_queues.repeat.assert_awaited_once_with('queue', 'off', user='kind1')
        client.player_queues.autoplay.assert_awaited_once_with('queue', False, user='kind1')

    async def test_A_album_multidisc(self):
        client = self.client()
        client.music.get_item_by_uri.return_value = NS(media_type='album', available=True, item_id='test', provider='apple_music')
        client.music.get_album_tracks.return_value = [self.track('disc2',2,1), self.track('disc1',1,1)]
        await Playback().start(client, 'player', NS(items=['apple_music://album/test']))
        self.assertEqual([t.uri for t in client.player_queues.play_media.call_args.kwargs['media']], ['disc1', 'disc2'])

    async def test_B_five_local_tracks(self):
        await self.run_episode(['filesystem_local://track/test%s.mp3' % i for i in range(5)])

    async def test_C_four_apple_tracks(self):
        await self.run_episode(['apple_music://track/test%s' % i for i in range(4)])

    async def test_D_three_groups(self):
        for start in (1,5,9):
            await self.run_episode(['apple_music://track/test%s' % i for i in range(start,start+4)])

    async def test_E_mixed_sources(self):
        await self.run_episode(['apple_music://track/test1', 'filesystem_local://track/test2.mp3'])

    async def test_F_replace_and_no_restart(self):
        client = self.client(); client.music.get_item_by_uri.side_effect = [self.track('one'),self.track('two')]
        player = Playback()
        await player.start(client,'player',NS(items=['one']))
        await player.start(client,'player',NS(items=['two']))
        await asyncio.sleep(0)
        self.assertEqual(client.player_queues.play_media.await_count, 2)
        self.assertEqual(client.player_queues.play_media.call_args.kwargs['media'][0].uri, 'two')

    async def test_G_missing_track_leaves_queue(self):
        client = self.client(); client.music.get_item_by_uri.side_effect = [self.track('ok'),self.track('missing', available=False)]
        with self.assertRaises(ValueError): await Playback().start(client,'player',NS(items=['ok','missing']))
        client.player_queues.play_media.assert_not_awaited()
        client.player_queues.repeat.assert_not_awaited()

    async def test_resolution_error_leaves_queue(self):
        client = self.client(); client.music.get_item_by_uri.side_effect = RuntimeError('Provider offline')
        with self.assertRaises(RuntimeError): await Playback().start(client,'player',NS(items=['bad']))
        client.player_queues.play_media.assert_not_awaited()

    async def test_empty_album(self):
        client=self.client(); client.music.get_item_by_uri.return_value=NS(media_type='album',available=True,item_id='a',provider='apple_music')
        client.music.get_album_tracks.return_value=[]
        with self.assertRaises(ValueError): await Playback().start(client,'player',NS(items=['album']))
        client.player_queues.play_media.assert_not_awaited()

class SevenCoverTests(unittest.IsolatedAsyncioTestCase):
    def libraries(self, count):
        data=config()
        template=data['libraries']['child']['categories'][0]
        data['libraries']['child']['categories'] = [dict(template, id='series_%s'%i) for i in range(count)]
        return parse(data)

    async def test_actual_backend_seven_entries_and_wire_budget(self):
        # Execute the actual Backend.browse method without bootstrapping Home Assistant.
        source=ast.parse((ROOT/'backend/custom_components/kidsplayer/__init__.py').read_text())
        backend=next(n for n in source.body if isinstance(n,ast.ClassDef) and n.name=='Backend')
        method=next(n for n in backend.body if isinstance(n,ast.AsyncFunctionDef) and n.name=='browse')
        scope={'window':model.window}
        exec(compile(ast.Module(body=[method],type_ignores=[]), '<Backend.browse>', 'exec'),scope)
        fixture=NS(load=AsyncMock(return_value=self.libraries(9)), client=lambda player: ('client','player'),
                   digest='f'*64,cover=AsyncMock(return_value='/api/image/serve/kp_'+'a'*20))
        result=await scope['browse'](fixture,{'library':'child','index':0})
        keys=('left3','left2','left','center','right','right2','right3')
        self.assertEqual([result[key]['id'] for key in keys],['series_%s'%i for i in (6,7,8,0,1,2,3)])
        self.assertEqual(fixture.cover.await_count,7)
        # Account for Tessera's 48-byte text cap: even max title/ID/cover fits 3200 bytes.
        for key in keys:
            result[key].update(title='x'*48,id='x'*32)
        self.assertLess(len(json.dumps(result).encode()),3200)
        self.assertNotIn('playback',json.dumps(result))
        self.assertNotIn('://track/',json.dumps(result))

    async def test_small_library_resolves_each_cover_once(self):
        source=ast.parse((ROOT/'backend/custom_components/kidsplayer/__init__.py').read_text())
        backend=next(n for n in source.body if isinstance(n,ast.ClassDef) and n.name=='Backend')
        method=next(n for n in backend.body if isinstance(n,ast.AsyncFunctionDef) and n.name=='browse')
        scope={'window':model.window}
        exec(compile(ast.Module(body=[method],type_ignores=[]), '<Backend.browse>', 'exec'),scope)
        for count in (1,2,3):
            fixture=NS(load=AsyncMock(return_value=self.libraries(count)),client=lambda player: ('client','player'),
                       digest='f'*64,cover=AsyncMock(return_value='/cover'))
            await scope['browse'](fixture,{'library':'child'})
            self.assertEqual(fixture.cover.await_count,count)

    def test_reference_frame_algorithm_unchanged(self):
        reference=(ROOT.parent/'examples/new_music/components/new_music/new_music.cpp').read_text()
        actual=(ROOT/'components/kidsplayer/kidsplayer.cpp').read_text()
        # This is deliberately an equality check of the reused reference block.
        start=reference.index('      const int spread =')
        end=reference.index('\n    }\n    frames.push_back',start)
        copied=actual.split('// BEGIN NEW MUSIC IMAGE FRAMES: copied unchanged from the pinned reference.\n',1)[1]
        copied=copied.split('      // END NEW MUSIC IMAGE FRAMES',1)[0].rstrip()
        self.assertEqual(copied,reference[start:end])

if __name__ == '__main__': unittest.main()
