import os
from pathlib import Path
from typing import Iterable, Iterator
from uuid import uuid4

from app.pkg.logger import get_logger

log = get_logger(__name__)
READ_CHUNK = 64 * 1024


class LocalFileStorage:
    """Stores files as <uuid4>.pdf directly under `root`."""

    def __init__(self, root: str | Path) -> None:
        self._root = Path(root)
        self._root.mkdir(parents=True, exist_ok=True)

    def _path(self, key: str) -> Path:
        # basename only: a key can never escape the storage root
        return self._root / Path(key).name

    def save(self, chunks: Iterable[bytes]) -> tuple[str, int]:
        key = f"{uuid4()}.pdf"
        path = self._path(key)
        size = 0
        try:
            with open(path, "wb") as fh:
                for chunk in chunks:
                    fh.write(chunk)
                    size += len(chunk)
        except BaseException:
            path.unlink(missing_ok=True)
            raise
        return key, size

    def exists(self, key: str) -> bool:
        return self._path(key).is_file()

    def iter_chunks(self, key: str) -> Iterator[bytes]:
        with open(self._path(key), "rb") as fh:
            while chunk := fh.read(READ_CHUNK):
                yield chunk

    def delete(self, key: str) -> None:
        try:
            os.remove(self._path(key))
        except FileNotFoundError:
            pass
        except OSError:
            log.warning("could not delete stored file", extra={"key": key})
