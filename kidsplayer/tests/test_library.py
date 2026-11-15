import asyncio
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

if __name__ == '__main__': unittest.main()
