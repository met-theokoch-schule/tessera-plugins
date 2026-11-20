"""Playback against strict legacy signatures and the actual 1.6 client source."""
import ast
import os
from pathlib import Path
from types import SimpleNamespace as NS
import unittest
from unittest.mock import AsyncMock, Mock
from test_library import Playback, compat

class LegacyMusic:
    async def get_item_by_uri(self, uri):
        return NS(uri=uri,media_type='track',available=True)

class LegacyQueues:
    def __init__(self):
        self.repeat=AsyncMock(spec=self.set_repeat)
        self.dont_stop_the_music=AsyncMock(spec=self.set_autoplay)

    async def get_active_queue(self, player_id):
        return NS(queue_id='queue')

    async def set_repeat(self, queue_id, repeat_mode): pass
    async def set_autoplay(self, queue_id, enabled): pass
    async def play_media(self, queue_id, media, option=None, radio_mode=False, user=None):
        raise AssertionError('1.6 wrapper cannot pass shuffle=false')

class CompatTests(unittest.IsolatedAsyncioTestCase):
    def client(self):
        return NS(server_info=NS(schema_version=65),music=LegacyMusic(),player_queues=LegacyQueues(),send_command=AsyncMock())

    async def test_legacy_preserves_all_tracks_and_queue_options(self):
        client=self.client()
        items=['apple_music://track/t5','apple_music://track/t6','filesystem_local://track/t7']
        await Playback().start(client,'player',NS(items=items),'kind1')
        client.send_command.assert_awaited_once()
        command=client.send_command.call_args
        self.assertEqual(command.args,('player_queues/play_media',))
        self.assertEqual([t.uri for t in command.kwargs['media']],items)
        self.assertEqual(command.kwargs['option'],'replace')
        self.assertEqual(command.kwargs['user'],'kind1')
        self.assertIs(command.kwargs['shuffle'],False)
        self.assertIs(command.kwargs['radio_mode'],False)
        client.player_queues.repeat.assert_awaited_once_with('queue','off')
        client.player_queues.dont_stop_the_music.assert_awaited_once_with('queue',False)

    async def test_new_client_on_legacy_server_does_not_impersonate_metadata(self):
        client=self.client()
        async def metadata(uri, *, user=None):
            self.assertIsNone(user) # server 65 disallows it here, even if wrapper accepts it
            return 'ok'
        self.assertEqual(await compat.contextual(client,metadata,'uri',user='kind1'),'ok')

    async def test_new_client_on_legacy_server_uses_supported_wire_command(self):
        client=self.client()
        async def modern_play(queue_id,media,option=None,radio_mode=False,shuffle=None,user=None):
            raise AssertionError('New wrapper would reject the schema-65 user argument')
        client.player_queues.play_media=modern_play
        await compat.replace_ordered(client,'queue',[],'replace','kind1')
        self.assertEqual(client.send_command.call_args.kwargs['user'],'kind1')
        self.assertIs(client.send_command.call_args.kwargs['shuffle'],False)

    async def test_underlying_typeerror_is_not_retried(self):
        client=self.client(); method=AsyncMock(side_effect=TypeError('Provider implementation failed'))
        with self.assertRaises(TypeError): await compat.contextual(client,method,'uri')
        method.assert_awaited_once()

    async def test_raw_shuffle_path_refuses_unverified_old_server(self):
        client=self.client();client.server_info.schema_version=34
        with self.assertRaises(ValueError): await compat.replace_ordered(client,'queue',[],'replace')
        client.send_command.assert_not_awaited()

    @unittest.skipUnless(os.getenv('MA_CLIENT_16_SOURCE'),'Set MA_CLIENT_16_SOURCE to an official v1.6.0 checkout')
    async def test_actual_client_16_methods(self):
        root=Path(os.environ['MA_CLIENT_16_SOURCE'])/'music_assistant_client'
        def controller(filename,names):
            source=ast.parse((root/filename).read_text())
            cls=next(n for n in source.body if isinstance(n,ast.ClassDef))
            methods=[n for n in cls.body if isinstance(n,ast.AsyncFunctionDef) and n.name in names]
            self.assertEqual(len(methods),len(names))
            for method in methods:
                method.returns=None
                for argument in (*method.args.posonlyargs,*method.args.args,*method.args.kwonlyargs): argument.annotation=None
            scope={'media_from_dict':lambda obj:NS(**obj),'Track':NS(from_dict=lambda obj:NS(**obj)),
                   'PlayerQueue':NS(from_dict=lambda obj:NS(**obj))}
            exec(compile(ast.Module(body=methods,type_ignores=[]),str(root/filename),'exec'),scope)
            return type('ActualClientController',(),{name:scope[name] for name in names})()
        client=self.client()
        client.music=controller('music.py',('get_item_by_uri','get_album_tracks'))
        client.player_queues=controller('player_queues.py',('get_active_queue','repeat','dont_stop_the_music','play_media'))
        client.music.client=client;client.player_queues.client=client
        calls=[]
        async def send(command,**kwargs):
            calls.append((command,kwargs))
            if command=='music/item_by_uri':
                if '/album/' in kwargs['uri']:
                    return dict(uri=kwargs['uri'],media_type='album',available=True,
                                item_id='test_album',provider='apple_music--test')
                return dict(uri=kwargs['uri'],media_type='track',available=True)
            if command=='music/albums/album_tracks':
                return [dict(uri='apple_music--test://track/t%s'%n,media_type='track',available=True,
                             disc_number=1,track_number=n) for n in range(12,0,-1)]
            if command=='player_queues/get_active_queue': return {'queue_id':'queue'}
        client.send_command=send
        await Playback().start(client,'player',NS(items=['apple_music://track/t5','apple_music://track/t6']),'kind1')
        self.assertEqual([c for c,_ in calls],['music/item_by_uri','music/item_by_uri','player_queues/get_active_queue',
            'player_queues/repeat','player_queues/dont_stop_the_music','player_queues/play_media'])
        self.assertTrue(all('user' not in data for _,data in calls[:-1]))
        self.assertEqual(calls[-1][1]['user'],'kind1')
        self.assertIs(calls[-1][1]['shuffle'],False)
        # The new number range uses the same actual 1.6 metadata wrappers and
        # sends exactly the selected tracks in one schema-65 replacement.
        calls.clear()
        selection=NS(uri='apple_music--test://album/test_album',numbers=(5,6,7,8),disc=None)
        await Playback().start(client,'player',NS(items=(),album=selection),'kind1')
        self.assertEqual([c for c,_ in calls],['music/item_by_uri','music/albums/album_tracks',
            'player_queues/get_active_queue','player_queues/repeat',
            'player_queues/dont_stop_the_music','player_queues/play_media'])
        self.assertEqual(calls[1][1],dict(item_id='test_album',
            provider_instance_id_or_domain='apple_music--test',in_library_only=False))
        self.assertTrue(all('user' not in data for _,data in calls[:-1]))
        self.assertEqual([t.uri for t in calls[-1][1]['media']],
            ['apple_music--test://track/t%s'%n for n in (5,6,7,8)])
        self.assertEqual(calls[-1][1]['option'],'replace')
        self.assertEqual(calls[-1][1]['user'],'kind1')
        self.assertIs(calls[-1][1]['shuffle'],False)

class ErrorTransportTests(unittest.IsolatedAsyncioTestCase):
    def scope(self):
        root=Path(__file__).resolve().parents[1]/'backend/custom_components/kidsplayer/__init__.py'
        source=ast.parse(root.read_text())
        methods=[node for node in source.body if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)) and node.name in ('send_failure','ws_play','ws_browse')]
        for node in methods: node.decorator_list=[]
        scope={'DOMAIN':'kidsplayer','_LOGGER':Mock()}
        exec(compile(ast.Module(body=methods,type_ignores=[]),str(root),'exec'),scope)
        return scope

    async def test_error_detail_survives_for_new_firmware(self):
        scope=self.scope(); backend=NS(play=AsyncMock(side_effect=TypeError('Bad MA parameter')))
        connection=NS(user=NS(is_admin=True),send_result=Mock(),send_error=Mock())
        await scope['ws_play'](NS(data={'kidsplayer':backend}),connection,{'id':7,'protocol':1})
        connection.send_error.assert_not_called()
        result=connection.send_result.call_args.args[1]
        self.assertIs(result['ok'],False)
        self.assertEqual(result['message'],'Bad MA parameter')

    async def test_legacy_error_never_reports_false_success(self):
        scope=self.scope(); backend=NS(play=AsyncMock(side_effect=ValueError('Missing track')))
        connection=NS(user=NS(is_admin=True),send_result=Mock(),send_error=Mock())
        await scope['ws_play'](NS(data={'kidsplayer':backend}),connection,{'id':7})
        connection.send_result.assert_not_called();connection.send_error.assert_called_once()

    async def test_admin_requirement_is_preserved(self):
        scope=self.scope();backend=NS(play=AsyncMock())
        connection=NS(user=NS(is_admin=False),send_result=Mock(),send_error=Mock())
        await scope['ws_play'](NS(data={'kidsplayer':backend}),connection,{'id':7,'protocol':1})
        backend.play.assert_not_awaited()
        self.assertEqual(connection.send_result.call_args.args[1]['error'],'unauthorized')
