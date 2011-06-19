# -*- coding: utf-8 -*-

from datetime import datetime
from glob import glob
from os import makedirs, stat_float_times
from os.path import abspath, dirname, exists, isdir, islink, join, lexists
import os
import shutil
import stat
import sys

class PydumpfsError(Exception):
    pass

class Pydumpfs(object):

    def __init__(self, verbose=False):
        self.verbose = verbose

    def decide_backup_dir(self, dest):
        now = datetime.now()
        milli = now.microsecond // 1000
        fmt = "%Y-%m-%d_%H:%M:%S.{milli:03d}".format(**locals())
        return join(dest, now.strftime(fmt))

    def do(self, dest, *src):
        if not exists(dest):
            raise PydumpfsError("%(dest)s doesn't exist." % { "dest": dest })

        stat_float_times(False)
        prev_dir = self._get_prev_dir(dest)
        backup_dir = self.decide_backup_dir(dest)
        makedirs(backup_dir)

        for d in src:
            self._do(prev_dir, backup_dir, d)

        self._print_debug(
            "done. The backup directory is %(path)r." % dict(path=backup_dir))
        return backup_dir

    def _print_debug(self, s):
        if not self.verbose:
            return

        print s

    def _get_prev_dir(self, dest):
        digit = "[0-9][0-9]*"
        date_pattern = "{digit}-{digit}-{digit}".format(**locals())
        time_pattern = "{digit}:{digit}:{digit}".format(**locals())
        pattern = "{date_pattern}_{time_pattern}".format(**locals())
        try:
            return sorted(glob(join(dest, pattern)))[-1]
        except IndexError:
            return None

    def _is_same_file(self, path1, path2):
        if isdir(path1) and (not islink(path1)):
            raise "%(path)r must be a file." % dict(path=path1)
        if isdir(path2) and (not islink(path2)):
            return False

        if (not lexists(path1)) or (not lexists(path2)):
            return False

        stat1 = os.lstat(path1)
        stat2 = os.lstat(path2)
        if stat1.st_mode != stat2.st_mode:
            return False
        if stat1.st_uid != stat2.st_uid:
            return False
        if stat1.st_gid != stat2.st_gid:
            return False
        if stat1.st_size != stat2.st_size:
            return False

        import filecmp
        return filecmp.cmp(path1, path2)

    def _copy_owner(self, dest, src):
        st = os.lstat(src)
        self._print_debug(
            "lchown: path=%(path)s, uid=%(uid)d, gid=%(gid)d" 
                % dict(path=dest, uid=st.st_uid, gid=st.st_gid))
        os.lchown(dest, st.st_uid, st.st_gid)

    def _change_owner_stat(self, dest, src_dir, src_name):
        src_path = join(src_dir, src_name)
        dest_path = dest + src_path
        if not lexists(dest_path):
            return

        self._copy_owner(dest_path, src_path)
        if not islink(src_path):
            self._copystat(dest_path, src_path)

    def _copystat(self, dest, src):
        self._print_debug(
            "copystat: src=%(src)s, dest=%(dest)s" % dict(src=src, dest=dest))
        shutil.copystat(src, dest)

    def _copy(self, dest, src):
        self._print_debug(
            "copy: src=%(src)s, dest=%(dest)s" % dict(src=src, dest=dest))
        try:
            shutil.copy(src, dest)
        except IOError, e:
            print >> sys.stderr, \
                    "error: Can't copy %(src)s to %(dest)s (%(error)s)." \
                    % { "src": src, "dest": dest, "error": e.strerror }

    def _link(self, dest, src):
        self._print_debug(
            "hard link: src=%(src)s, dest=%(dest)s" % dict(src=src, dest=dest))
        os.link(src, dest)

    def _mkdir(self, path):
        self._print_debug("mkdir: path=%(path)s" % dict(path=path))
        os.mkdir(path)

    def _symlink(self, dest, src):
        self._print_debug(
            "symlink: src=%(src)s, dest=%(dest)s" % dict(src=src, dest=dest))
        os.symlink(src, dest)

    def _change_meta_data(self, dest, src):
        for dirpath, dirnames, filenames in os.walk(src, topdown=False):
            for dirname in dirnames:
                try:
                    self._change_owner_stat(dest, dirpath, dirname)
                except OSError, e:
                    path = dest + join(dirpath, dirname)
                    print >> sys.stderr, "error: Can't change status of the di"\
                        "rectory %(path)r (%(desc)s)." \
                            % dict(path=path, desc=e.strerror)

            for filename in filenames:
                try:
                    path = join(dirpath, filename)
                    st = os.lstat(path)
                    if stat.S_ISREG(st.st_mode) or islink(path):
                        self._change_owner_stat(dest, dirpath, filename)
                except OSError, e:
                    print >> sys.stderr, "error: Can't change status of the fi"\
                        "le %(path)r (%(desc)s)." \
                            % dict(path=dest+path, desc=e.strerror)

    def _make_link(self, dest, src):
        to = os.readlink(src)
        self._symlink(dest, to)

    def _walk_to_copy(self, prev, dest, src, file_func):
        for dirpath, dirnames, filenames in os.walk(src):
            for dirname in dirnames:
                src_dir = join(dirpath, dirname)
                dest_dir = dest + src_dir
                try:
                    if islink(src_dir):
                        self._make_link(dest_dir, src_dir)
                    else:
                        self._mkdir(dest_dir)
                except OSError, e:
                    print >> sys.stderr, "error: Can't make the directory %(pa"\
                        "th)r (%(desc)s)." \
                            % dict(path=dest_dir, desc=e.strerror)

            for filename in filenames:
                src_file = join(dirpath, filename)
                if prev is not None:
                    prev_file = prev + src_file
                else:
                    prev_file = None
                dest_file = dest + src_file
                try:
                    file_func(prev_file, dest_file, src_file)
                except OSError, e:
                    print >> sys.stderr, "error: Can't copy the file %(path)r "\
                        "(%(desc)s)." % dict(path=src_file, desc=e.strerror)

        self._change_meta_data(dest, src)

    def _copy_recursively(self, dest, src):
        def _file_func(prev, dest, src):
            st = os.lstat(src)
            if stat.S_ISREG(st.st_mode):
                self._copy(dest, src)
            elif islink(src):
                self._make_link(dest, src)

        self._walk_to_copy(None, dest, src, _file_func)

    def _copy_incrementally(self, prev, dest, src):
        def _file_func(prev, dest, src):
            st = os.lstat(src)
            if stat.S_ISREG(st.st_mode):
                if self._is_same_file(src, prev):
                    self._link(dest, prev)
                else:
                    self._copy(dest, src)
            elif islink(src):
                self._make_link(dest, src)

        self._walk_to_copy(prev, dest, src, _file_func)

    def _do(self, prev_dir, backup_dir, src):
        self._print_debug(
            "backup from %(src)s to %(dest)s." % dict(src=src, dest=backup_dir))
        src = abspath(src)

        dest_dir = backup_dir + src
        self._print_debug("makedirs: %(dir)s" % dict(dir=dest_dir))
        makedirs(dest_dir)

        dir = src
        while dir != "/":
            path = backup_dir + dir
            self._copy_owner(path, dir)
            self._copystat(path, dir)
            dir = dirname(dir)

        if prev_dir is None:
            self._copy_recursively(backup_dir, src)
        else:
            self._copy_incrementally(prev_dir, backup_dir, src)

# vim: tabstop=4 shiftwidth=4 expandtab softtabstop=4
