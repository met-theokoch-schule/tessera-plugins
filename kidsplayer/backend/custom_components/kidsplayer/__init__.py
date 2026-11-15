"""Kidsplayer companion: YAML, paged browser and exact URI playback for Tessera."""
import asyncio
import hashlib
import io
import logging
from pathlib import Path
from collections import OrderedDict

import voluptuous as vol
from aiohttp import web
from PIL import Image, ImageOps
from homeassistant.components import websocket_api
from homeassistant.components.http import HomeAssistantView
from homeassistant.helpers import config_validation as cv, entity_registry as er
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.components.music_assistant.helpers import get_music_assistant_client

from .library import parse, window, ConfigError, MAX_BYTES
from .playback import Playback

_LOGGER = logging.getLogger(__name__)
DOMAIN = 'kidsplayer'
CONFIG_SCHEMA = vol.Schema({vol.Required(DOMAIN): vol.Schema({
    vol.Optional('libraries_file', default='kidsplayer.yaml'): cv.string,
    vol.Optional('cover_root', default='/media/hoerspielcover'): cv.string,
})}, extra=vol.ALLOW_EXTRA)

class Backend:
    def __init__(self, hass, config):
        self.hass = hass
        self.path = Path(hass.config.path(config['libraries_file']))
        self.root = Path(config['cover_root']).resolve()
        self.libs = {}
        self.digest = ''
        self.covers = OrderedDict()
        self.playback = Playback()
        self.load_lock = asyncio.Lock()

    def read(self):
        with self.path.open('rb') as handle:
            raw = handle.read(MAX_BYTES + 1)
        if len(raw) > MAX_BYTES:
            raise ConfigError('YAML exceeds 512 KiB')
        digest = hashlib.sha256(raw).hexdigest()
        return digest, raw.decode('utf-8')

    async def load(self):
        async with self.load_lock:
            digest, source = await self.hass.async_add_executor_job(self.read)
            if digest != self.digest:
                libs = await self.hass.async_add_executor_job(parse, source)
                self.libs, self.digest = libs, digest
        return self.libs

    def client(self, entity_id):
        entry = er.async_get(self.hass).async_get(entity_id)
        if not entry or entry.platform != 'music_assistant' or not entry.config_entry_id:
            raise ValueError('Einen Player der offiziellen Music-Assistant-Integration waehlen')
        return get_music_assistant_client(self.hass, entry.config_entry_id), entry.unique_id

    async def cover(self, item, lib, client):
        if item.cover == 'auto':
            ep = item.episodes[0] if hasattr(item, 'episodes') else item
            media = await client.music.get_item_by_uri(ep.items[0], user=lib.user or None)
            source = client.get_media_item_image_url(media)
            if not source:
                return ''
        else:
            source = str((self.root / item.cover).resolve())
            if not Path(source).is_relative_to(self.root):
                raise ValueError('Cover ausserhalb cover_root')
        token = hashlib.sha256((self.digest + source).encode()).hexdigest()[:20]
        self.covers[token] = (source, item.cover == 'auto')
        self.covers.move_to_end(token)
        while len(self.covers) > 512:
            self.covers.popitem(last=False)
        return '/api/image/serve/kp_' + token  # 40 bytes: Tessera cuts strings at 48

    async def browse(self, msg):
        libs = await self.load()
        lib = libs[msg['library']]
        client, _ = self.client(msg.get('player') or lib.player)
        index, total, items = window(lib, msg.get('category', ''), msg.get('index', 0))
        result = dict(index=index, total=total, revision=self.digest[:16],
                      show_titles=lib.show_titles, animation=lib.animation)
        for slot, item in zip(('left', 'center', 'right'), items):
            try:
                picture = await self.cover(item, lib, client)
            except Exception:
                picture = ''
                _LOGGER.warning('Cover nicht verfuegbar: %s', item.id)
            result[slot] = dict(id=item.id, title=item.title, cover=picture)
        return result

    async def play(self, msg):
        lib = (await self.load())[msg['library']]
        if msg['revision'] != self.digest[:16]:
            raise ValueError('Bibliothek geaendert; Auswahl neu laden')
        cat = next(c for c in lib.categories if c.id == msg['category'])
        ep = next(e for e in cat.episodes if e.id == msg['episode'])
        client, player_id = self.client(msg.get('player') or lib.player)
        await self.playback.start(client, player_id, ep, lib.user or None)
        return {'status': 'Wiedergabe gestartet'}

class CoverView(HomeAssistantView):
    url = '/api/image/serve/kp_{token}'
    name = 'api:kidsplayer:cover'
    requires_auth = True

    def __init__(self, backend):
        self.backend = backend

    async def get(self, request, token):
        source = self.backend.covers.get(token)
        if not source:
            raise web.HTTPNotFound()
        path, remote = source
        if remote:
            # URL was generated by the installed Music Assistant client, never by display input.
            session = async_get_clientsession(self.backend.hass)
            async with session.get(path, timeout=15, allow_redirects=False) as response:
                response.raise_for_status()
                raw = await response.content.read(2 * 1024 * 1024 + 1)
        else:
            def read():
                resolved = Path(path).resolve()
                if not resolved.is_relative_to(self.backend.root):
                    raise ValueError('Cover ausserhalb cover_root')
                with resolved.open('rb') as handle:
                    return handle.read(2 * 1024 * 1024 + 1)
            raw = await self.backend.hass.async_add_executor_job(read)
        if len(raw) > 2 * 1024 * 1024:
            raise web.HTTPRequestEntityTooLarge(max_size=2097152, actual_size=len(raw))
        def resize():
            with Image.open(io.BytesIO(raw)) as original:
                if original.width * original.height > 16000000:
                    raise ValueError('Cover exceeds 16 megapixels')
                image = ImageOps.exif_transpose(original)
                image.thumbnail((360, 360))
                output = io.BytesIO()
                image.convert('RGB').save(output, 'JPEG', quality=88)
                return output.getvalue()
        data = await self.backend.hass.async_add_executor_job(resize)
        return web.Response(body=data, content_type='image/jpeg')

@websocket_api.websocket_command({
    vol.Required('type'): 'kidsplayer/browse',
    vol.Required('library'): cv.string,
    vol.Optional('player', default=''): cv.string,
    vol.Optional('category', default=''): cv.string,
    vol.Optional('index', default=0): vol.All(vol.Coerce(int), vol.Range(min=-100000, max=100000)),
})
@websocket_api.async_response
async def ws_browse(hass, connection, msg):
    try:
        connection.send_result(msg['id'], await hass.data[DOMAIN].browse(msg))
    except Exception as err:
        _LOGGER.exception('Kidsplayer-Bibliothek konnte nicht geladen werden')
        connection.send_error(msg['id'], 'kidsplayer_error', str(err)[:160])

@websocket_api.websocket_command({
    vol.Required('type'): 'kidsplayer/play',
    vol.Required('library'): cv.string,
    vol.Required('category'): cv.string,
    vol.Required('episode'): cv.string,
    vol.Required('revision'): cv.string,
    vol.Optional('player', default=''): cv.string,
})
@websocket_api.async_response
async def ws_play(hass, connection, msg):
    if not connection.user.is_admin:
        connection.send_error(msg['id'], 'unauthorized', 'Admin connection required')
        return
    try:
        connection.send_result(msg['id'], await hass.data[DOMAIN].play(msg))
    except Exception as err:
        _LOGGER.exception('Kidsplayer-Wiedergabe fehlgeschlagen')
        connection.send_error(msg['id'], 'kidsplayer_error', str(err)[:160])

async def async_setup(hass, config):
    backend = Backend(hass, config[DOMAIN])
    hass.data[DOMAIN] = backend
    hass.http.register_view(CoverView(backend))
    websocket_api.async_register_command(hass, ws_browse)
    websocket_api.async_register_command(hass, ws_play)
    return True
