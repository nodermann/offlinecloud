import pytest

import contextlib

from api.storage import StorageMutex
from api.storage import BusyPath


@pytest.fixture
def mutex():
    return StorageMutex()


@contextlib.contextmanager
def ES():
    with contextlib.ExitStack() as stack:
        stack.ec = stack.enter_context

        yield stack


def test_storage_mutex_reads_only(mutex):
    with ES() as s:
        s.ec(mutex.rlock_file("/a/b/1"))
        s.ec(mutex.rlock_dir("/a/b"))
        s.ec(mutex.rlock_dir("/a/b"))
        s.ec(mutex.rlock_dir("/a"))
        s.ec(mutex.rlock_dir("/a/b/c"))


def test_storage_mutex_writes_only(mutex):
    with ES() as s:
        s.ec(mutex.wlock_dir("/a"))

        with pytest.raises(BusyPath, match="/a/1"):
            s.ec(mutex.wlock_file("/a/1"))

        with pytest.raises(BusyPath, match="/a/2"):
            s.ec(mutex.wlock_file("/a/2"))

        with pytest.raises(BusyPath, match="/"):
            s.ec(mutex.wlock_dir("/"))

        s.ec(mutex.wlock_dir("/b"))

        with pytest.raises(BusyPath, match="/x/y"):
            s.ec(mutex.wlock_dir("/x"))
            s.ec(mutex.wlock_dir("/x/y"))

        with pytest.raises(BusyPath, match="/c/d/10"):
            s.ec(mutex.wlock_dir("/c/d"))
            s.ec(mutex.wlock_file("/c/d/10"))


def test_storage_mutex_files_mixed(mutex):
    with ES() as s:
        with ES() as subs:
            subs.ec(mutex.rlock_file("/a/1"))

            with pytest.raises(BusyPath, match="/a/1"):
                s.ec(mutex.wlock_file("/a/1"))

        s.ec(mutex.wlock_file("/a/1"))


def test_storage_mutex_dirs_mixed(mutex):
    with ES() as s:
        with ES() as subs:
            subs.ec(mutex.rlock_dir("/a/b"))
            subs.ec(mutex.rlock_dir("/a/b/c"))

            with pytest.raises(BusyPath, match="/a"):
                s.ec(mutex.wlock_dir("/a"))

        with ES() as subs:
            subs.ec(mutex.wlock_dir("/a"))

            with pytest.raises(BusyPath, match="/a"):
                s.ec(mutex.rlock_dir("/a"))

        s.ec(mutex.rlock_dir("/a"))


def test_storage_mutex_mixed(mutex):
    with ES() as s:
        with ES() as subs:
            subs.ec(mutex.wlock_dir("/a"))

            with pytest.raises(BusyPath, match="/a/b"):
                subs.ec(mutex.wlock_dir("/a/b"))

        with ES() as subs:
            subs.ec(mutex.rlock_dir("/a"))
            subs.ec(mutex.rlock_dir("/a/b"))

            with pytest.raises(BusyPath, match="/a/1"):
                s.ec(mutex.wlock_file("/a/1"))

            with pytest.raises(BusyPath, match="/a/2"):
                s.ec(mutex.wlock_file("/a/2"))

        with ES() as subs:
            subs.ec(mutex.wlock_file("/a/1"))
            subs.ec(mutex.wlock_file("/a/2"))
            subs.ec(mutex.wlock_file("/a/3"))

            with pytest.raises(BusyPath, match="/a"):
                subs.ec(mutex.wlock_dir("/a"))

        s.ec(mutex.wlock_dir("/a"))
        s.ec(mutex.wlock_dir("/b"))
        s.ec(mutex.wlock_dir("/c"))

        s.ec(mutex.rlock_dir("/d"))
        s.ec(mutex.rlock_dir("/e"))
        s.ec(mutex.rlock_dir("/f"))

        s.ec(mutex.rlock_file("/x/1"))
        s.ec(mutex.rlock_file("/y/1"))
        s.ec(mutex.rlock_file("/z/1"))
