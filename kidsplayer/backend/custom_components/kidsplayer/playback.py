"""Preflight every item before touching the queue. No title search, no polling restart."""
import asyncio
from .compat import contextual, autoplay_off, replace_ordered

def album_positions(tracks):
    """Validate positions before sorting or selecting; never infer list offsets."""
    if not tracks:
        raise ValueError('Album hat keine Tracks')
    if len(tracks) > 2048:
        raise ValueError('Album hat mehr als 2048 Tracks')
    result = []
    for track in tracks:
        disc = getattr(track, 'disc_number', None)
        disc = 1 if disc is None or (type(disc) is int and disc == 0) else disc
        number = getattr(track, 'track_number', None)
        if type(disc) is not int or disc < 1 or type(number) is not int or number < 1:
            raise ValueError('Album-Reihenfolge unklar; explizite Track-URIs verwenden')
        result.append((disc, number, track))
    return result

def select_album_tracks(tracks, selection):
    positions = album_positions(tracks)
    discs = {disc for disc, _, _ in positions}
    if selection.disc is None and len(discs) > 1:
        raise ValueError('Album hat mehrere Discs; playback.disc angeben')
    chosen_disc = selection.disc if selection.disc is not None else next(iter(discs))
    if chosen_disc not in discs:
        raise ValueError('Disc %s fehlt im Album' % chosen_disc)
    by_number = {}
    for disc, number, track in positions:
        if disc != chosen_disc:
            continue
        if number in by_number:
            raise ValueError('Tracknummer %s auf Disc %s ist mehrdeutig' % (number, disc))
        by_number[number] = track
    missing = [number for number in selection.numbers if number not in by_number]
    if missing:
        raise ValueError('Track %s fehlt auf Disc %s' % (missing[0], chosen_disc))
    # An explicit number list preserves YAML order, even [8, 2, 5].
    return [by_number[number] for number in selection.numbers]

async def resolve_album_selection(client, selection, user=None):
    album = await contextual(client, client.music.get_item_by_uri, selection.uri, user=user)
    if str(album.media_type) != 'album':
        raise ValueError('album_uri verweist nicht auf ein Album')
    if not getattr(album, 'available', False):
        raise ValueError('Album nicht verfuegbar: ' + selection.uri)
    tracks = await contextual(client, client.music.get_album_tracks, album.item_id, album.provider, user=user)
    return select_album_tracks(tracks, selection)

class Playback:
    def __init__(self):
        self.locks = {}

    async def start(self, client, player_id, episode, user=None):
        # Serialize all tiles targeting the same MA server/player.
        key = (id(client), player_id)
        async with self.locks.setdefault(key, asyncio.Lock()):
            selection = getattr(episode, 'album', None)
            tracks = await resolve_album_selection(client, selection, user) if selection else []
            for uri in episode.items:
                item = await contextual(client, client.music.get_item_by_uri, uri, user=user)
                if not getattr(item, 'available', False):
                    raise ValueError('Medium nicht verfuegbar: ' + uri)
                if str(item.media_type) == 'album':
                    album = await contextual(client, client.music.get_album_tracks, item.item_id, item.provider, user=user)
                    if not album:
                        raise ValueError('Album hat keine Tracks: ' + uri)
                    # Never let a server preference reorder a multi-disc album.
                    positions = album_positions(album)
                    if len({(disc, number) for disc, number, _ in positions}) != len(positions):
                        raise ValueError('Album-Reihenfolge unklar; explizite Track-URIs verwenden')
                    tracks.extend(track for _, _, track in sorted(positions, key=lambda entry: entry[:2]))
                elif str(item.media_type) == 'track':
                    tracks.append(item)
                else:
                    raise ValueError('Nur Album und Track werden unterstuetzt')
            if not tracks:
                raise ValueError('Folge hat keine Tracks')
            if len(tracks) > 2048:
                raise ValueError('Folge hat mehr als 2048 Tracks')
            for track in tracks:
                if not getattr(track, 'uri', ''):
                    raise ValueError('Track-URI fehlt; Auswahl nicht gestartet')
                if not getattr(track, 'available', False):
                    raise ValueError('Track nicht verfuegbar: ' + track.uri)
            # Start a new episode on the selected player's own queue. Its active
            # source can be external AirPlay (no MA queue) or another player's
            # queue; following that source would fail or redirect playback.
            queue = client.player_queues.get(player_id)
            if queue is None or queue.queue_id != player_id:
                raise ValueError('Music-Assistant-Queue fuer den gewaehlten Player fehlt')
            # Import only at runtime, so the sequencing logic is testable without HA.
            from music_assistant_models.enums import QueueOption, RepeatMode
            await contextual(client, client.player_queues.repeat, queue.queue_id, RepeatMode.OFF, user=user)
            await autoplay_off(client, queue.queue_id, user=user)
            await replace_ordered(client, queue.queue_id, tracks, QueueOption.REPLACE, user=user)
