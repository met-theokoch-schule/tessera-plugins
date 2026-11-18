"""The cover reader must not mistake an early network chunk for the whole image."""
import asyncio
import ast
import base64
import importlib.util
import hashlib
import os
from pathlib import Path
from collections import OrderedDict
import tempfile
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
    async def test_local_replacement_changes_actual_backend_url_without_yaml_changes(self):
        source=ast.parse((ROOT/'backend/custom_components/kidsplayer/__init__.py').read_text())
        backend=next(n for n in source.body if isinstance(n,ast.ClassDef) and n.name=='Backend')
        method=next(n for n in backend.body if isinstance(n,ast.AsyncFunctionDef) and n.name=='cover')
        scope={'hashlib':hashlib,'local_cover_source':images.local_cover_source}
        exec(compile(ast.Module(body=[method],type_ignores=[]), '<Backend.cover>', 'exec'),scope)
        async def executor(fn,*args): return fn(*args)
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'cover.jpg';path.write_bytes(b'old-cover')
            saved=path.stat()
            fixture=NS(root=Path(folder),digest='same-yaml-revision',covers=OrderedDict(),
                       hass=NS(async_add_executor_job=executor))
            item=NS(cover='cover.jpg')
            old=await scope['cover'](fixture,item,None,None)
            self.assertEqual(await scope['cover'](fixture,item,None,None),old)
            path.write_bytes(b'new-cover') # same filename and byte length
            os.utime(path,ns=(saved.st_atime_ns,saved.st_mtime_ns)) # copied timestamps too
            new=await scope['cover'](fixture,item,None,None)
            self.assertNotEqual(new,old)
            self.assertLessEqual(len(new.encode()),48)
            self.assertEqual(fixture.covers[new.rsplit('kp_',1)[1]],(str(path.resolve()),False))
            # A HA restart with identical source bytes should not redownload artwork.
            fixture.covers=OrderedDict()
            self.assertEqual(await scope['cover'](fixture,item,None,None),new)

    async def test_local_digest_follows_bytes_not_timestamps(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'cover.jpg';path.write_bytes(PNG)
            source,first=images.local_cover_source(folder,'cover.jpg')
            self.assertEqual(source,str(path.resolve()))
            self.assertEqual(first,hashlib.sha256(PNG).hexdigest())
            os.utime(path,ns=(1,1))
            self.assertEqual(images.local_cover_source(folder,'cover.jpg')[1],first)

    async def test_local_limits_empty_and_missing_file(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'cover.jpg';path.write_bytes(b'')
            with self.assertRaisesRegex(images.CoverError,'Leere Coverdatei'):
                images.local_cover_source(folder,'cover.jpg')
            path.write_bytes(b'a'*(images.MAX_IMAGE_BYTES+1))
            with self.assertRaisesRegex(images.CoverError,'2 MiB'):
                images.local_cover_source(folder,'cover.jpg')
            with self.assertRaises(FileNotFoundError):
                images.local_cover_source(folder,'missing.jpg')

    async def test_local_digest_rejects_paths_and_symlinks_outside_root(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)/'covers';root.mkdir()
            outside=Path(folder)/'private.jpg';outside.write_bytes(b'not-a-cover')
            (root/'link.jpg').symlink_to(outside)
            for name in ('../private.jpg',str(outside),'link.jpg'):
                with self.subTest(name=name), self.assertRaisesRegex(images.CoverError,'ausserhalb'):
                    images.local_cover_source(root,name)

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
