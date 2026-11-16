"""MA 1.6/1.8 client compatibility, verified against server 2.10.12/schema 65.

A client method accepting a keyword does not imply the connected server accepts it.
Schema 65 supports user attribution on play_media, but not on metadata/queue settings.
"""
import inspect


def schema(client):
    return getattr(getattr(client, 'server_info', None), 'schema_version', 0)


def supports(method, keyword):
    parameters = inspect.signature(method).parameters
    return keyword in parameters or any(p.kind == inspect.Parameter.VAR_KEYWORD for p in parameters.values())


async def contextual(client, method, *args, user=None):
    options = {'user': user} if schema(client) >= 101 and supports(method, 'user') else {}
    return await method(*args, **options)


async def autoplay_off(client, queue_id, user=None):
    queues = client.player_queues
    # Client 1.8's new wrapper requires schema 101. Server 65 exposes the old alias.
    if schema(client) >= 101 and hasattr(queues, 'autoplay'):
        await contextual(client, queues.autoplay, queue_id, False, user=user)
    else:
        await queues.dont_stop_the_music(queue_id, False)


async def replace_ordered(client, queue_id, tracks, option, user=None):
    if schema(client) >= 101 and supports(client.player_queues.play_media, 'shuffle'):
        await client.player_queues.play_media(
            queue_id, media=tracks, option=option, radio_mode=False, shuffle=False, user=user,
        )
        return
    # Client 1.6 lacks shuffle; client 1.8 gates user attribution on schema 101.
    # Server 2.10.12/schema 65 already supports both fields on this command.
    # Send precisely the same command as the official wrapper, adding shuffle=false.
    # Do not start first and then try to repair a shuffled queue.
    if schema(client) < 65:
        raise ValueError('Music Assistant braucht API-Schema >= 65')
    options = {'user': user} if user else {}
    await client.send_command(
        'player_queues/play_media', queue_id=queue_id, media=tracks,
        option=option, radio_mode=False, shuffle=False, **options,
    )
