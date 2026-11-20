"""A new episode must use the selected speaker, independent of its active source."""
import ast
from pathlib import Path
from types import SimpleNamespace as NS
import unittest
from unittest.mock import AsyncMock, Mock

from test_library import Playback, parse, config


class PlaybackTargetTests(unittest.IsolatedAsyncioTestCase):
    def client(self, active):
        return NS(server_info=NS(schema_version=101), music=NS(
            get_item_by_uri=AsyncMock(return_value=NS(
                uri='apple_music--test://track/one', media_type='track', available=True))),
            player_queues=NS(get=Mock(return_value=NS(queue_id='selected-speaker')),
                            get_active_queue=AsyncMock(return_value=active),
                            repeat=AsyncMock(), autoplay=AsyncMock(), play_media=AsyncMock()))

    async def start(self, client):
        await Playback().start(client, 'selected-speaker',
                               NS(items=['apple_music--test://track/one']), 'child')

    async def assert_selected_target(self, active):
        client = self.client(active)
        await self.start(client)
        queues = client.player_queues
        queues.get.assert_called_once_with('selected-speaker')
        queues.get_active_queue.assert_not_awaited()
        queues.repeat.assert_awaited_once_with('selected-speaker', 'off', user='child')
        queues.autoplay.assert_awaited_once_with('selected-speaker', False, user='child')
        queues.play_media.assert_awaited_once()
        self.assertEqual(queues.play_media.call_args.args, ('selected-speaker',))
        self.assertEqual(queues.play_media.call_args.kwargs['option'], 'replace')

    async def test_external_airplay_with_no_active_ma_queue(self):
        await self.assert_selected_target(None)

    async def test_another_players_active_queue_is_not_used(self):
        await self.assert_selected_target(NS(queue_id='another-room'))

    async def test_missing_or_wrong_own_queue_leaves_other_room_untouched(self):
        for own in (None, NS(queue_id='another-room')):
            with self.subTest(own=own):
                client = self.client(NS(queue_id='another-room'))
                client.player_queues.get.return_value = own
                with self.assertRaisesRegex(ValueError, 'gewaehlten Player'):
                    await self.start(client)
                client.player_queues.get_active_queue.assert_not_awaited()
                client.player_queues.repeat.assert_not_awaited()
                client.player_queues.autoplay.assert_not_awaited()
                client.player_queues.play_media.assert_not_awaited()


class BackendTargetTests(unittest.IsolatedAsyncioTestCase):
    async def test_inspector_overrides_yaml_and_entity_mapping_is_resolved_each_start(self):
        path = Path(__file__).resolve().parents[1] / 'backend/custom_components/kidsplayer/__init__.py'
        source = ast.parse(path.read_text())
        cls = next(n for n in source.body if isinstance(n, ast.ClassDef) and n.name == 'Backend')
        method = next(n for n in cls.body if isinstance(n, ast.AsyncFunctionDef) and n.name == 'play')
        scope = {}
        exec(compile(ast.Module(body=[method], type_ignores=[]), str(path), 'exec'), scope)
        libs = parse(config())
        fixture = NS(load=AsyncMock(return_value=libs), digest='r'*64,
                     client=Mock(side_effect=[('client', 'speaker-before-rename'),
                                              ('client', 'speaker-after-rename'),
                                              ('client', 'yaml-speaker')]),
                     playback=NS(start=AsyncMock()))
        msg = dict(library='child', category='robin', episode='ep1', revision='r'*16,
                   player='media_player.selected')
        for _ in range(2):
            await scope['play'](fixture, msg)
        await scope['play'](fixture, dict(msg, player=''))
        self.assertEqual([call.args[0] for call in fixture.client.call_args_list],
                         ['media_player.selected', 'media_player.selected', 'media_player.child'])
        self.assertEqual([call.args[1] for call in fixture.playback.start.call_args_list],
                         ['speaker-before-rename', 'speaker-after-rename', 'yaml-speaker'])
