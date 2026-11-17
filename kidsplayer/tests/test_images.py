"""The cover reader must not mistake an early network chunk for the whole image."""
import asyncio
import ast
import base64
import importlib.util
from pathlib import Path
from types import SimpleNamespace as NS
import unittest
from unittest.mock import Mock

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('cover_images', ROOT/'backend/custom_components/kidsplayer/images.py')
images = importlib.util.module_from_spec(spec)
spec.loader.exec_module(images)
PNG = base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+j4nsAAAAASUVORK5CYII=')

class Chunked:
    def __init__(self, chunks): self.chunks=chunks; self.received=0
    async def read(self, n): return self.chunks[0] # realistic first-buffer semantics of read(n)
    async def iter_chunked(self, size):
        for chunk in self.chunks:
            await asyncio.sleep(0)
            self.received += 1
            yield chunk

class ImageTests(unittest.IsolatedAsyncioTestCase):
    async def test_complete_image_from_partial_network_buffers(self):
        stream=Chunked([PNG[:8],PNG[8:30],PNG[30:]])
        self.assertNotEqual(await stream.read(images.MAX_IMAGE_BYTES+1),PNG) # old code truncates
        result=await images.read_image_response(NS(status=200,content_length=None,content=stream))
        self.assertEqual(result,PNG)
        self.assertEqual(stream.received,3)

    async def test_size_limit_is_checked_incrementally(self):
        stream=Chunked([b'a'*4,b'b'*4,b'c'*4])
        with self.assertRaises(images.CoverError):
            await images.read_image_response(NS(status=200,content_length=None,content=stream),limit=7)
        self.assertEqual(stream.received,2) # do not consume the rest of an oversized body

    async def test_advertised_oversize_is_rejected_before_download(self):
        stream=Chunked([b'data'])
        with self.assertRaises(images.CoverError):
            await images.read_image_response(NS(status=200,content_length=8,content=stream),limit=7)
        self.assertEqual(stream.received,0)

    async def test_exact_limit_is_allowed(self):
        result=await images.read_image_response(NS(status=200,content_length=7,content=Chunked([b'123',b'4567'])),limit=7)
        self.assertEqual(result,b'1234567')

    async def test_http_errors_redirect_and_empty_body_are_explicit(self):
        for status in (301,302,401,403,404,500):
            with self.subTest(status=status), self.assertRaisesRegex(images.CoverError,'HTTP %s'%status):
                await images.read_image_response(NS(status=status,content_length=None,content=Chunked([])))
        with self.assertRaisesRegex(images.CoverError,'Leere Coverantwort'):
            await images.read_image_response(NS(status=200,content_length=0,content=Chunked([])))

    async def test_broken_stream_propagates(self):
        class Broken(Chunked):
            async def iter_chunked(self,size):
                yield PNG[:8]
                raise ConnectionError('Disconnected')
        with self.assertRaises(ConnectionError):
            await images.read_image_response(NS(status=200,content_length=None,content=Broken([])))

    async def test_authenticated_view_consumes_complete_body(self):
        # Run the actual CoverView._serve method; only image codec and HA HTTP/session are doubles.
        source=ast.parse((ROOT/'backend/custom_components/kidsplayer/__init__.py').read_text())
        cls=next(n for n in source.body if isinstance(n,ast.ClassDef) and n.name=='CoverView')
        method=next(n for n in cls.body if isinstance(n,ast.AsyncFunctionDef) and n.name=='_serve')
        class Response:
            status=200; content_length=None; content=Chunked([PNG[:8],PNG[8:]])
            async def __aenter__(self): return self
            async def __aexit__(self,*args): pass
        session=NS(get=Mock(return_value=Response()))
        class Decoded:
            width=1; height=1
            def __enter__(self): return self
            def __exit__(self,*args): pass
            def thumbnail(self,size): pass
            def convert(self,mode): return self
            def save(self,output,*args,**kwargs): output.write(b'jpeg-output')
        def decode(raw):
            self.assertEqual(raw.getvalue(),PNG) # the codec must receive every byte
            return Decoded()
        async def executor(fn): return fn()
        import io
        scope={'io':io,'Image':NS(open=decode),'ImageOps':NS(exif_transpose=lambda image:image),
               'MAX_IMAGE_BYTES':images.MAX_IMAGE_BYTES,'read_image_response':images.read_image_response,
               'async_get_clientsession':lambda hass:session,
               'web':NS(Response=lambda **kwargs:kwargs)}
        exec(compile(ast.Module(body=[method],type_ignores=[]), '<CoverView._serve>', 'exec'),scope)
        fixture=NS(backend=NS(covers={'test':('https://example.invalid/art.jpg',True)},hass=NS(async_add_executor_job=executor)))
        result=await scope['_serve'](fixture,None,'test')
        self.assertEqual(result['body'],b'jpeg-output')
        self.assertFalse(session.get.call_args.kwargs['allow_redirects'])

if __name__=='__main__': unittest.main()
