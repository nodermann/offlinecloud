import asyncio
import contextlib
import enum
import os
import shutil

from typing import Callable
from typing import Final
from typing import List
from typing import Tuple
from os.path import commonpath as C

import aiohttp


LockCheck = Callable[[str], bool]


def startswith(s: str, prefix: str) -> bool:
    return s[:len(prefix)] == prefix


def remove_prefix(s: str, prefix: str) -> str:
    if startswith(s, prefix):
        s = s[len(prefix):]

    return s


async def save_multipart_stream(
        reader: aiohttp.BodyPartReader, real_path: str, chunk_size: int = 256 * 1024):
    with open(real_path, "wb") as f:
        chunk = await reader.read_chunk(chunk_size)

        while chunk:
            f.write(chunk)
            chunk = await reader.read_chunk(chunk_size)


class StorageError(Exception):
    path: str

    def __init__(self, path: str) -> None:
        super().__init__(path)

        self.path = path


class SameSrcDest(Exception):
    src: str
    dest: str

    def __init__(self, src: str, dest: str) -> None:
        super().__init__(src, dest)

        self.src = src
        self.dest = dest
    

class BusyPath(StorageError): pass
class DangerousPath(StorageError): pass
class NotFound(StorageError): pass
class AlreadyExists(StorageError): pass
class NotAFile(StorageError): pass
class NotADir(StorageError): pass



#TODO: maybe dataclass?
class RWListPair:
    def __init__(self) -> None:
        self.read: List[str] = []
        self.write: List[str] = []


class StorageMutex:
    def __init__(self) -> None:
        self.files = RWListPair()
        self.dirs = RWListPair()

    def can_rlock_file(self, file: str) -> bool:
        # if file is WLocked file, itself writes, we can't RLock file
        # if C(file, wld) is WLocked dir, parent writes, we can't RLock file

        return not (
            file in self.files.write or
            any(C([file, wld]) in self.dirs.write for wld in self.dirs.write)
        )

    def can_wlock_file(self, file: str) -> bool:
        # if file is RLocked file, itself reads, we can't WLock file
        # if C(file, rld) is RLocked dir, parent reads, we can't WLock file
        # if C(file, wld) is WLocked dir, parent writes, we can't WLock file

        return not (
            file in self.files.read or
            any(C([file, rld]) in self.dirs.read for rld in self.dirs.read) or
            any(C([file, wld]) in self.dirs.write for wld in self.dirs.write)
        )

    def can_rlock_dir(self, dir: str) -> bool:
        # if C(dir, wlf) is dir, child file writes, we can't RLock dir
        # if C(dir, wld) is dir, itself/child dir writes, we can't RLock dir
        # if C(dir, wld) is WLocked dir, parent dir writes, we can't RLock dir

        return not (
            any([C([dir, wlf]) == dir for wlf in self.files.write]) or
            any([C([dir, wld]) == dir for wld in self.dirs.write]) or
            any([C([dir, wld]) in self.dirs.write for wld in self.dirs.write])
        )

    def can_wlock_dir(self, dir: str) -> bool:
        # if not can_rlock_dir(dir), child/parent/itself writes, we can't WLock dir
        # if C(dir, rlf) is dir, child file reads, we can't WLock dir
        # if C(dir, rld) is dir, child dir reads, we can't WLock dir
        # if C(dir, rld) is RLocked dir, parent/itself reads, we can't WLock dir

        return not (
            not self.can_rlock_dir(dir) or
            any(C([dir, rlf]) == dir for rlf in self.files.read) or
            any(C([dir, rld]) == dir for rld in self.dirs.read) or
            any(C([dir, rld]) in self.dirs.read for rld in self.dirs.read)
        )

    @contextlib.contextmanager
    def lock(self, collection: List[str], check: 'LockCheck', path: str):
        if not check(path):
            raise BusyPath(path)

        collection.append(path)

        try:
            yield
        finally:
            collection.remove(path)

    @contextlib.contextmanager
    def rlock_file(self, file: str):
        with self.lock(self.files.read, self.can_rlock_file, file):
            yield


    @contextlib.contextmanager
    def wlock_file(self, file: str):
        with self.lock(self.files.write, self.can_wlock_file, file):
            yield

    @contextlib.contextmanager
    def rlock_dir(self, dir: str):
        with self.lock(self.dirs.read, self.can_rlock_dir, dir):
            yield

    @contextlib.contextmanager
    def wlock_dir(self, dir: str):
        with self.lock(self.dirs.write, self.can_wlock_dir, dir):
            yield



class Storage:
    def __init__(self, root: str) -> None:
        self.root: Final = root
        self.mutex = StorageMutex()

    def trim_root(self, path: str) -> str:
        return remove_prefix(path, self.root)

    @contextlib.contextmanager
    def acquire_rlocked_file(self, file: str):
        with self.mutex.rlock_file(file):
            yield

    @contextlib.contextmanager
    def acquire_wlocked_file(self, file: str):
        with self.mutex.wlock_file(file):
            yield

    @contextlib.contextmanager
    def acquire_rlocked_dir(self, dir: str):
        with self.mutex.rlock_dir(dir):
            yield

    @contextlib.contextmanager
    def acquire_wlocked_dir(self, dir: str):
        with self.mutex.wlock_dir(dir):
            yield

    def resolve_nonexistent_root(self, path: str) -> str:
        parent: str = os.path.dirname(path)

        while not os.path.exists(parent):
            if len(path) <= len(self.root):
                raise DangerousPath(path)

            path = parent
            parent = os.path.dirname(path)

        return path


    def join_path(self, path: str) -> str:
        return os.path.normpath(os.path.join(self.root, path))

    def check_safe_path(self, path: str) -> bool:
        return C([self.root, path]) == self.root

    def resolve(self, path: str) -> str:
        # a/b/c   -> /storage_root/a/b/c
        # removes any leading and trailing slashes
        # /a/b/c  -> /storage_root/a/b/c
        # not resolves paths outside of storage root
        # ../boot -> raise DangerousPath

        # using this variable to raise the exception with
        # proper argument

        original_path: Final = path
        real_path = self.join_path(path.strip("/"))

        if not self.check_safe_path(real_path):
            raise DangerousPath(original_path)

        return real_path


    async def new_file(self, path: str) -> None:
        real_path = self.resolve(path)
        parent = os.path.dirname(real_path)

        with self.mutex.rlock_file(real_path):
            root = self.resolve_nonexistent_root(parent)

        with contextlib.ExitStack() as s:
            if os.path.exists(root):
                s.enter_context(self.mutex.wlock_file(real_path))
            else:
                s.enter_context(self.mutex.wlock_dir(root))

            if os.path.exists(real_path):
                raise AlreadyExists(path)

            os.makedirs(parent, exist_ok=True)
            os.mknod(real_path)


    async def new_dir(self, path: str) -> None:
        real_path = self.resolve(path)
        parent = os.path.dirname(real_path)

        with self.mutex.rlock_dir(real_path):
            root = self.resolve_nonexistent_root(parent)

        with contextlib.ExitStack() as s:
            if os.path.exists(root):
                s.enter_context(self.mutex.wlock_dir(real_path))
            else:
                s.enter_context(self.mutex.wlock_dir(root))

            if os.path.exists(real_path):
                raise AlreadyExists(path)

            os.makedirs(real_path, exist_ok=True)


    async def copy_file(self, src: str, dest: str) -> None:
        real_src  = self.resolve(src)
        real_dest = self.resolve(dest)

        if real_src == real_dest:
            raise SameSrcDest(src, dest)

        dest_parent = os.path.dirname(real_dest)

        with contextlib.ExitStack() as s:
            s.enter_context(self.mutex.rlock_file(real_src))
            s.enter_context(self.mutex.rlock_file(real_dest))

            root = self.resolve_nonexistent_root(dest_parent)

        with contextlib.ExitStack() as s:
            s.enter_context(self.mutex.rlock_file(real_src))

            if os.path.exists(root):
                s.enter_context(self.mutex.wlock_file(real_dest))
            else:
                s.enter_context(self.mutex.wlock_dir(root))

            if not os.path.exists(real_src):
                raise NotFound(src)
            if not os.path.isfile(real_src):
                raise NotAFile(src)
            if os.path.exists(real_dest):
                raise AlreadyExists(dest)
                
            os.makedirs(dest_parent, exist_ok=True)
            shutil.copyfile(real_src, real_dest)

    async def copy_dir(self, src: str, dest: str) -> None:
        real_src  = self.resolve(src)
        real_dest = self.resolve(dest)

        if real_src == real_dest:
            raise SameSrcDest(src, dest)

        dest_parent = os.path.dirname(real_dest)

        with contextlib.ExitStack() as s:
            s.enter_context(self.mutex.rlock_dir(real_src))
            s.enter_context(self.mutex.rlock_dir(real_dest))

            root = self.resolve_nonexistent_root(dest_parent)

        with contextlib.ExitStack() as s:
            s.enter_context(self.mutex.wlock_dir(real_src))

            if os.path.exists(root):
                s.enter_context(self.mutex.wlock_dir(real_dest))
            else:
                s.enter_context(self.mutex.wlock_dir(root))
                
            if not os.path.exists(real_src): raise NotFound(src)
            if not os.path.isdir(real_src): raise NotADir(src)
            if os.path.exists(real_dest): raise AlreadyExists(dest)
                
            os.makedirs(dest_parent, exist_ok=True)
            shutil.copytree(real_src, real_dest)


    async def move_file(self, src: str, dest: str) -> None:
        real_src  = self.resolve(src)
        real_dest = self.resolve(dest)

        if real_src == real_dest:
            raise SameSrcDest(src, dest)

        dest_parent = os.path.dirname(real_dest)

        with contextlib.ExitStack() as s:
            s.enter_context(self.mutex.rlock_file(real_src))
            s.enter_context(self.mutex.rlock_file(real_dest))

            root = self.resolve_nonexistent_root(dest_parent)

        with contextlib.ExitStack() as s:
            if os.path.exists(root):
                s.enter_context(self.mutex.wlock_file(real_src))
                s.enter_context(self.mutex.wlock_file(real_dest))
            else:
                s.enter_context(self.mutex.wlock_file(real_src))
                s.enter_context(self.mutex.wlock_dir(root))

            if not os.path.exists(real_src): raise NotFound(src)
            if not os.path.isfile(real_src): raise NotAFile(src)
            if os.path.exists(real_dest): raise AlreadyExists(dest)
                
            os.makedirs(dest_parent, exist_ok=True)
            os.replace(real_src, real_dest)


    async def move_dir(self, src: str, dest: str) -> None:
        real_src  = self.resolve(src)
        real_dest = self.resolve(dest)

        if real_src == real_dest:
            raise SameSrcDest(src, dest)

        dest_parent = os.path.dirname(real_dest)

        with contextlib.ExitStack() as s:
            s.enter_context(self.mutex.rlock_dir(real_src))
            s.enter_context(self.mutex.rlock_dir(real_dest))

            root = self.resolve_nonexistent_root(dest_parent)

        with contextlib.ExitStack() as s:
            s.enter_context(self.mutex.wlock_dir(real_src))

            if os.path.exists(root):
                s.enter_context(self.mutex.wlock_dir(real_dest))
            else:
                s.enter_context(self.mutex.wlock_dir(root))
                
            if not os.path.exists(real_src): raise NotFound(src)
            if not os.path.isdir(real_src): raise NotADir(src)
            if os.path.exists(real_dest): raise AlreadyExists(dest)
                
            os.makedirs(dest_parent, exist_ok=True)
            shutil.move(real_src, real_dest)

    async def save_multipart_file(self, reader: aiohttp.BodyPartReader, path: str) -> None:
        real_path = self.resolve(path)
        parent = os.path.dirname(real_path)

        with self.mutex.rlock_file(real_path):
            root = self.resolve_nonexistent_root(parent)

        with contextlib.ExitStack() as s:
            if os.path.exists(root):
                s.enter_context(self.mutex.wlock_file(real_path))
            else:
                s.enter_context(self.mutex.wlock_dir(root))

            if os.path.exists(real_path):
                raise AlreadyExists(path)

            os.makedirs(parent, exist_ok=True)

            try:
                await save_multipart_stream(reader, real_path)

            except Exception:
                os.remove(real_path)

                raise
    
    async def remove_file(self, path: str) -> None:
        real_path = self.resolve(path)

        with self.mutex.wlock_file(real_path):
            if not os.path.exists(real_path): raise NotFound(path)
            if not os.path.isfile(real_path): raise NotAFile(path)

            os.remove(real_path)

    async def remove_dir(self, path: str) -> None:
        real_path = self.resolve(path)

        with self.mutex.wlock_dir(real_path):
            if not os.path.exists(real_path): raise NotFound(path)
            if not os.path.isdir(real_path): raise NotADir(path)

            shutil.rmtree(real_path)
