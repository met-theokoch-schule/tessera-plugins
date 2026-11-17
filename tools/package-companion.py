#!/usr/bin/env python3
"""Package only the HA companion, rooted for extraction into /config."""
import argparse
import json
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

root = Path(__file__).resolve().parents[1]
source = root / 'kidsplayer/backend/custom_components/kidsplayer'
required = ('__init__.py', 'manifest.json', 'library.py', 'playback.py', 'compat.py', 'images.py')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path, help='Destination ZIP file (outside the source tree recommended)')
    output = parser.parse_args().output
    for name in required:
        if not (source / name).is_file():
            raise SystemExit('Missing companion file: ' + name)
    manifest = json.loads((source / 'manifest.json').read_text())
    if manifest['domain'] != 'kidsplayer':
        raise SystemExit('Unexpected companion domain')
    output.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(output, 'w', ZIP_DEFLATED) as archive:
        for name in required:
            archive.write(source / name, 'custom_components/kidsplayer/' + name)
        archive.write(root / 'kidsplayer/LICENSE', 'custom_components/kidsplayer/LICENSE')
    with ZipFile(output) as archive:
        if archive.testzip() is not None:
            raise SystemExit('ZIP verification failed')
        print('Companion ' + manifest['version'] + ': ' + str(output.resolve()))
        for name in archive.namelist():
            print(name)


if __name__ == '__main__':
    main()
