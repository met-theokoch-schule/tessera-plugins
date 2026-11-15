"""Preflight every item before touching the queue. No title search, no polling restart."""
import asyncio

class Playback:
    def __init__(self):
        self.locks = {}

    async def start(self, client, player_id, episode, user=None):
        # Serialize all tiles targeting the same MA server/player.
        key = (id(client), player_id)
        async with self.locks.setdefault(key, asyncio.Lock()):
            tracks = []
            for uri in episode.items:
                item = await client.music.get_item_by_uri(uri, user=user)
                if not getattr(item, 'available', False):
                    raise ValueError('Medium nicht verfuegbar: ' + uri)
                if str(item.media_type) == 'album':
                    album = await client.music.get_album_tracks(item.item_id, item.provider, user=user)
                    if not album:
                        raise ValueError('Album hat keine Tracks: ' + uri)
                    # Never let a server preference reorder a multi-disc album.
                    album = sorted(album, key=lambda t: (t.disc_number or 1, t.track_number or 0))
                    positions = [(t.disc_number or 1, t.track_number) for t in album]
                    if any(not n for _, n in positions) or len(set(positions)) != len(positions):
                        raise ValueError('Album-Reihenfolge unklar; explizite Track-URIs verwenden')
                    tracks.extend(album)
                elif str(item.media_type) == 'track':
                    tracks.append(item)
                else:
                    raise ValueError('Nur Album und Track werden unterstuetzt')
            if len(tracks) > 2048:
                raise ValueError('Folge hat mehr als 2048 Tracks')
            for track in tracks:
                if not track.available:
                    raise ValueError('Track nicht verfuegbar: ' + track.uri)
            queue = await client.player_queues.get_active_queue(player_id, user=user)
            if queue is None:
                raise ValueError('Keine aktive Music-Assistant-Queue')
            # Import only at runtime, so the sequencing logic is testable without HA.
            from music_assistant_models.enums import QueueOption, RepeatMode
            await client.player_queues.repeat(queue.queue_id, RepeatMode.OFF, user=user)
            await client.player_queues.autoplay(queue.queue_id, False, user=user)
            await client.player_queues.play_media(
                queue.queue_id, media=tracks, option=QueueOption.REPLACE,
                radio_mode=False, shuffle=False, user=user,
            )
