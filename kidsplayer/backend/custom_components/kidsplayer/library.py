"""Strict, bounded library model; contains no Home Assistant dependencies."""
from dataclasses import dataclass
import re
from typing import Optional
import yaml

MAX_BYTES = 512 * 1024
ID = re.compile(r'^[a-z][a-z0-9_]{0,31}$')
URI = re.compile(r'^[a-zA-Z0-9_\-]+://(track|album)/[^\s]+$')

class ConfigError(ValueError):
    pass

class UniqueLoader(yaml.SafeLoader):
    pass

def mapping(loader, node):
    out = {}
    for key, value in node.value:
        k = loader.construct_object(key)
        if not isinstance(k, str) or k in out:
            raise ConfigError('Duplicate or non-text YAML key')
        out[k] = loader.construct_object(value)
    return out

UniqueLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, mapping)

def fields(obj, allowed, required=()):
    if not isinstance(obj, dict) or set(obj) - set(allowed) or set(required) - set(obj):
        raise ConfigError('Missing or unknown fields: ' + ', '.join(allowed))
    return obj

def text(value, limit=160):
    if not isinstance(value, str) or not value.strip() or len(value.encode()) > limit:
        raise ConfigError('Invalid or oversized text')
    return value

def identity(value):
    if not isinstance(value, str) or not ID.fullmatch(value):
        raise ConfigError('IDs: lowercase letters, digits, underscores; maximum 32')
    return value

def entries(value, most):
    if not isinstance(value, list) or not 1 <= len(value) <= most:
        raise ConfigError('List must contain 1..%s entries' % most)
    return value

def cover(value):
    value = text(value, 240)
    if value != 'auto':
        if value.startswith('/') or '..' in value.split('/') or ':' in value or '\\' in value:
            raise ConfigError('Cover must be relative to cover_root')
    return value

def media_uri(value, album_only=False):
    value = text(value, 1024)
    if not URI.fullmatch(value) or 'PLACEHOLDER' in value or '<' in value:
        raise ConfigError('Use an exact Music Assistant album/track URI; replace placeholders')
    if album_only and value.split('://', 1)[1].split('/', 1)[0] != 'album':
        raise ConfigError('album_uri muss eine Album-URI sein')
    return value

def position(value):
    if type(value) is not int or not 1 <= value <= 9999:
        raise ConfigError('Track- und Discnummern muessen ganze Zahlen von 1 bis 9999 sein')
    return value

@dataclass(frozen=True)
class AlbumSelection:
    uri: str
    numbers: tuple
    disc: Optional[int] = None

def playback_config(value):
    playback = fields(value, ('items', 'album_uri', 'tracks', 'track_range', 'disc'))
    if 'items' in playback:
        if len(playback) != 1:
            raise ConfigError('playback.items nicht mit album_uri oder Trackauswahl mischen')
        uris = []
        for item in entries(playback['items'], 256):
            fields(item, ('uri',), ('uri',))
            uris.append(media_uri(item['uri']))
        return tuple(uris), None
    if 'album_uri' not in playback or ('tracks' in playback) == ('track_range' in playback):
        raise ConfigError('playback braucht items oder album_uri mit genau einer Auswahl: tracks oder track_range')
    uri = media_uri(playback['album_uri'], album_only=True)
    disc = position(playback['disc']) if 'disc' in playback else None
    if 'tracks' in playback:
        numbers = tuple(position(n) for n in entries(playback['tracks'], 256))
        if len(set(numbers)) != len(numbers):
            raise ConfigError('Tracknummern in tracks duerfen nicht doppelt vorkommen')
    else:
        interval = fields(playback['track_range'], ('start', 'end'), ('start', 'end'))
        start, end = position(interval['start']), position(interval['end'])
        if end < start or end - start + 1 > 256:
            raise ConfigError('track_range braucht start <= end und hoechstens 256 Tracks')
        numbers = tuple(range(start, end + 1))
    return (), AlbumSelection(uri, numbers, disc)

@dataclass(frozen=True)
class Episode:
    id: str
    title: str
    cover: str
    items: tuple
    album: Optional[AlbumSelection] = None

    @property
    def first_uri(self):
        return self.album.uri if self.album else self.items[0]

@dataclass(frozen=True)
class Category:
    id: str
    title: str
    cover: str
    episodes: tuple

@dataclass(frozen=True)
class Library:
    player: str
    user: str
    show_titles: bool
    animation: bool
    categories: tuple

def parse(source):
    if len(source.encode()) > MAX_BYTES:
        raise ConfigError('Library file exceeds 512 KiB')
    try:
        raw = yaml.load(source, Loader=UniqueLoader)
    except (yaml.YAMLError, RecursionError, TypeError) as err:
        raise ConfigError('Invalid YAML') from err
    fields(raw, ('libraries',), ('libraries',))
    libraries = raw['libraries']
    if not isinstance(libraries, dict) or not 1 <= len(libraries) <= 32:
        raise ConfigError('Expected 1..32 named libraries')
    result = {}
    for name, lib in libraries.items():
        identity(name)
        fields(lib, ('version', 'player', 'music_assistant_user', 'display', 'categories'), ('version', 'categories'))
        if type(lib['version']) is not int or lib['version'] != 1:
            raise ConfigError('Expected version: 1')
        player = lib.get('player', '')
        if player and not re.fullmatch(r'media_player\.[a-z0-9_]+', player):
            raise ConfigError('Invalid player')
        user = lib.get('music_assistant_user', '')
        if user:
            text(user, 64)
        display = fields(lib.get('display', {}), ('show_titles', 'cover_style', 'animation'))
        for key in ('show_titles', 'animation'):
            if key in display and type(display[key]) is not bool:
                raise ConfigError('Display flags must be boolean')
        if display.get('cover_style', 'contain') != 'contain':
            raise ConfigError('Only contain is supported')
        categories, ids = [], set()
        for cat in entries(lib['categories'], 128):
            fields(cat, ('id', 'title', 'cover', 'episodes'), ('id', 'title', 'episodes'))
            cid = identity(cat['id'])
            if cid in ids:
                raise ConfigError('Duplicate category ID')
            ids.add(cid)
            episodes, eids = [], set()
            for ep in entries(cat['episodes'], 512):
                fields(ep, ('id', 'title', 'cover', 'playback'), ('id', 'title', 'playback'))
                eid = identity(ep['id'])
                if eid in eids:
                    raise ConfigError('Duplicate episode ID')
                eids.add(eid)
                uris, album = playback_config(ep['playback'])
                episodes.append(Episode(eid, text(ep['title']), cover(ep.get('cover', 'auto')), uris, album))
            categories.append(Category(cid, text(cat['title']), cover(cat.get('cover', 'auto')), tuple(episodes)))
        result[name] = Library(player, user, display.get('show_titles', True), display.get('animation', True), tuple(categories))
    return result

def window(lib, category='', index=0, radius=1):
    cat = next((c for c in lib.categories if c.id == category), None)
    if category and cat is None:
        raise ConfigError('Category no longer exists; go back')
    items = cat.episodes if cat else lib.categories
    index %= len(items)
    return index, len(items), [items[(index + delta) % len(items)] for delta in range(-radius, radius + 1)]
