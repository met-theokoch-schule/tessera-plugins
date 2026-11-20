"""Numbered selections must resolve completely before changing the MA queue."""
import ast
import hashlib
from pathlib import Path
from types import SimpleNamespace as NS
import unittest
from unittest.mock import AsyncMock

from test_library import Playback, model, parse, config, compat

ALBUM = 'apple_music--test://album/test_album'


def episode(playback):
    data = config()
    data['libraries']['child']['categories'][0]['episodes'][0]['playback'] = playback
    return parse(data)['child'].categories[0].episodes[0]


class AlbumConfigTests(unittest.TestCase):
    def test_inclusive_range(self):
        ep = episode({'album_uri': ALBUM, 'track_range': {'start': 5, 'end': 8}})
        self.assertEqual(ep.items, ())
        self.assertEqual(ep.album.numbers, (5, 6, 7, 8))
        self.assertEqual(ep.first_uri, ALBUM)

    def test_list_order_and_explicit_disc(self):
        ep = episode({'album_uri': ALBUM, 'tracks': [8, 2, 5], 'disc': 2})
        self.assertEqual(ep.album.numbers, (8, 2, 5))
        self.assertEqual(ep.album.disc, 2)

    def test_range_of_one_track(self):
        ep = episode({'album_uri': 'library://album/test', 'track_range': {'start': 8, 'end': 8}})
        self.assertEqual(ep.album.numbers, (8,))

    def test_reject_invalid_or_ambiguous_configuration(self):
        invalid = [
            {}, {'album_uri': ALBUM}, {'tracks': [1]},
            {'album_uri': ALBUM, 'tracks': [1], 'track_range': {'start': 1, 'end': 2}},
            {'items': [{'uri': ALBUM}], 'album_uri': ALBUM, 'tracks': [1]},
            {'items': {'album_uri': ALBUM, 'start': 1, 'end': 8}},
            {'album_uri': ALBUM, 'start': 1, 'end': 8},
            {'album_uri': ALBUM, 'tracks': []}, {'album_uri': ALBUM, 'tracks': [1, 1]},
            {'album_uri': ALBUM, 'tracks': list(range(1, 258))},
            {'album_uri': ALBUM, 'track_range': {'start': 1}},
            {'album_uri': ALBUM, 'track_range': {'start': 8, 'end': 1}},
            {'album_uri': ALBUM, 'track_range': {'start': 1, 'end': 257}},
            {'album_uri': ALBUM, 'track_range': {'start': 1, 'end': 8, 'typo': 0}},
            {'album_uri': 'apple_music://track/test', 'tracks': [1]},
            {'album_uri': 'apple_music://album/PLACEHOLDER', 'tracks': [1]},
        ]
        for value in (0, -1, True, 1.5, '1', 10000, None):
            invalid.extend([
                {'album_uri': ALBUM, 'tracks': [value]},
                {'album_uri': ALBUM, 'track_range': {'start': value, 'end': 8}},
                {'album_uri': ALBUM, 'tracks': [1], 'disc': value},
            ])
        for data in invalid:
            with self.subTest(data=data), self.assertRaises(model.ConfigError):
                episode(data)


class AlbumPlaybackTests(unittest.IsolatedAsyncioTestCase):
    def track(self, number, disc=1, available=True):
        return NS(uri='apple_music--test://track/disc%s_track%s' % (disc, number),
                  disc_number=disc, track_number=number, available=available, media_type='track')

    def client(self, tracks):
        return NS(server_info=NS(schema_version=101), music=NS(
            get_item_by_uri=AsyncMock(return_value=NS(media_type='album', available=True,
                                                    item_id='test_album', provider='apple_music--test')),
            get_album_tracks=AsyncMock(return_value=tracks)),
            player_queues=NS(get_active_queue=AsyncMock(return_value=NS(queue_id='queue')),
                            repeat=AsyncMock(), autoplay=AsyncMock(), play_media=AsyncMock()))

    async def start(self, playback, tracks):
        client = self.client(tracks)
        await Playback().start(client, 'player', episode(playback), 'kind1')
        client.player_queues.play_media.assert_awaited_once()
        call = client.player_queues.play_media.call_args.kwargs
        self.assertEqual(call['option'], 'replace')
        self.assertIs(call['shuffle'], False)
        self.assertIs(call['radio_mode'], False)
        return client, call['media']

    async def test_three_episodes_from_one_twelve_track_album(self):
        tracks = [self.track(n) for n in range(12, 0, -1)] # provider response out of order
        for start in (1, 5, 9):
            with self.subTest(start=start):
                client, selected = await self.start(
                    {'album_uri': ALBUM, 'track_range': {'start': start, 'end': start+3}}, tracks)
                self.assertEqual([t.track_number for t in selected], list(range(start, start+4)))
                client.music.get_item_by_uri.assert_awaited_once_with(ALBUM, user='kind1')

    async def test_noncontiguous_numbers_keep_yaml_order(self):
        _, selected = await self.start({'album_uri': ALBUM, 'tracks': [8, 2, 5]},
                                       [self.track(n) for n in range(1, 13)])
        self.assertEqual([t.track_number for t in selected], [8, 2, 5])

    async def test_disc_selection_is_exact(self):
        tracks = [self.track(n, disc) for disc in (2, 1) for n in (3, 1, 2)]
        _, selected = await self.start({'album_uri': ALBUM, 'disc': 2, 'tracks': [2, 1]}, tracks)
        self.assertEqual([(t.disc_number, t.track_number) for t in selected], [(2, 2), (2, 1)])

    async def test_unselected_unavailable_track_does_not_block_episode(self):
        _, selected = await self.start({'album_uri': ALBUM, 'tracks': [1]},
                                       [self.track(1), self.track(2, available=False)])
        self.assertEqual([t.track_number for t in selected], [1])

    async def test_missing_ambiguous_or_unavailable_tracks_leave_queue_untouched(self):
        missing_uri = self.track(1)
        missing_uri.uri = ''
        cases = [
            ([self.track(1)], {'tracks': [1, 2]}, 'Track 2 fehlt'),
            ([self.track(1, 1), self.track(1, 2)], {'tracks': [1]}, 'mehrere Discs'),
            ([self.track(1), self.track(1)], {'tracks': [1]}, 'mehrdeutig'),
            ([self.track(1)], {'tracks': [1], 'disc': 2}, 'Disc 2 fehlt'),
            ([self.track(0)], {'tracks': [1]}, 'Reihenfolge unklar'),
            ([self.track(True)], {'tracks': [1]}, 'Reihenfolge unklar'),
            ([missing_uri], {'tracks': [1]}, 'Track-URI fehlt'),
            ([self.track(1, available=False)], {'tracks': [1]}, 'nicht verfuegbar'),
            ([], {'tracks': [1]}, 'keine Tracks'),
            ([self.track(n) for n in range(1, 2050)], {'tracks': [1]}, 'mehr als 2048'),
        ]
        for tracks, selection, error in cases:
            with self.subTest(selection=selection, error=error):
                client = self.client(tracks)
                with self.assertRaisesRegex(ValueError, error):
                    await Playback().start(client, 'player', episode(dict(album_uri=ALBUM, **selection)))
                client.player_queues.get_active_queue.assert_not_awaited()
                client.player_queues.repeat.assert_not_awaited()
                client.player_queues.autoplay.assert_not_awaited()
                client.player_queues.play_media.assert_not_awaited()

    async def test_album_type_and_provider_error_leave_queue_untouched(self):
        for wrong in ('track', 'unavailable', 'offline'):
            client = self.client([self.track(1)])
            if wrong == 'track': client.music.get_item_by_uri.return_value.media_type = 'track'
            elif wrong == 'unavailable': client.music.get_item_by_uri.return_value.available = False
            else: client.music.get_album_tracks.side_effect = RuntimeError('Provider offline')
            with self.subTest(wrong=wrong), self.assertRaises((ValueError, RuntimeError)):
                await Playback().start(client, 'player', episode({'album_uri': ALBUM, 'tracks': [1]}))
            client.player_queues.repeat.assert_not_awaited()
            client.player_queues.play_media.assert_not_awaited()

    async def test_metadata_is_resolved_fresh_at_each_start(self):
        client = self.client([self.track(1), self.track(2)])
        ep = episode({'album_uri': ALBUM, 'track_range': {'start': 1, 'end': 2}})
        playback = Playback()
        await playback.start(client, 'player', ep)
        client.music.get_album_tracks.return_value = [self.track(1)]
        with self.assertRaisesRegex(ValueError, 'Track 2 fehlt'):
            await playback.start(client, 'player', ep)
        self.assertEqual(client.player_queues.play_media.await_count, 1)

    async def test_auto_cover_uses_album_uri_for_episode_and_category(self):
        source = ast.parse((Path(__file__).resolve().parents[1] / 'backend/custom_components/kidsplayer/__init__.py').read_text())
        cls = next(n for n in source.body if isinstance(n, ast.ClassDef) and n.name == 'Backend')
        method = next(n for n in cls.body if isinstance(n, ast.AsyncFunctionDef) and n.name == 'cover')
        scope = {'contextual': compat.contextual, 'hashlib': hashlib}
        exec(compile(ast.Module(body=[method], type_ignores=[]), '<Backend.cover>', 'exec'), scope)
        from collections import OrderedDict
        client = self.client([])
        client.get_media_item_image_url = lambda item: 'https://example.invalid/cover'
        fixture = NS(digest='same-yaml', covers=OrderedDict())
        ep = episode({'album_uri': ALBUM, 'tracks': [1]})
        cat = model.Category('test', 'Test', 'auto', (ep,))
        for item in (ep, cat):
            await scope['cover'](fixture, item, NS(user='kind1'), client)
        self.assertEqual(client.music.get_item_by_uri.await_args_list[0].args, (ALBUM,))
        self.assertEqual(client.music.get_item_by_uri.await_args_list[1].args, (ALBUM,))
