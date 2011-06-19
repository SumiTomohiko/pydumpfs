#! python
# -*- coding: utf-8 -*-

from os import chmod, lchown, listdir, lstat, makedirs, mkfifo, readlink, remove, stat, walk
from os.path import abspath, dirname, exists, isdir, isfile, islink, join, lexists, samefile
from shutil import rmtree
from stat import S_IRUSR, S_IRWXG, S_IRWXO, S_IRWXU, S_ISLNK, S_ISREG
from unittest import TestCase, main

from sys import path
path.insert(0, "src")

from pydumpfs import Pydumpfs, PydumpfsError

class TestPydumpfs(TestCase):

    def setUp(self):
        import tempfile
        self.dest_dir = tempfile.mkdtemp(prefix="pydumpfs")

    def tearDown(self):
        rmtree(self.dest_dir)

    def test_copy_dir(self):
        self._do_test("copy_dir")

    def _do_test_twice(self, name):
        for _ in range(2):
            self._do_test(name)

    def test_copy_dir_twice(self):
        self._do_test_twice("copy_dir_twice")

    def test_copy_file(self):
        self._do_test("copy_file")

    def test_copy_symlink_dir(self):
        self._do_test("copy_symlink_dir")

    def test_copy_symlink_file(self):
        self._do_test("copy_symlink_file")

    def test_hard_link(self):
        name = "hard_link"
        src_dir = self._get_source_directory(name)

        obj = Pydumpfs(**self._get_pydumpfs_options())
        backup_dir1 = obj.do(self.dest_dir, src_dir)
        backup_dir2 = obj.do(self.dest_dir, src_dir)

        foo_src_path = join(src_dir, "foo")
        path1 = backup_dir1 + foo_src_path
        path2 = backup_dir2 + foo_src_path
        self.assert_(samefile(path1, path2),
            "%(path1)r's i-node and %(path2)r's one are not same."
                % dict(path1=path1, path2=path2))

    def test_new_file(self):
        name = "new_file"
        src_dir = self._get_source_directory(name)
        file_path = join(src_dir, "foo")
        if isfile(file_path):
            remove(file_path)
        elif isdir(file_path):
            rmtree(file_path)

        obj = Pydumpfs()
        obj.do(self.dest_dir, src_dir)

        self._make_sample_file(file_path)

        self._do_test(name)

    def test_remove_file(self):
        name = "remove_file"
        src_dir = self._get_source_directory(name)
        file_path = join(src_dir, "foo")

        self._make_sample_file(file_path)

        obj = Pydumpfs()
        obj.do(self.dest_dir, src_dir)

        remove(file_path)

        self._do_test(name)

    def test_update_file(self):
        name = "update_file"
        src_dir = self._get_source_directory(name)
        file_path = join(src_dir, "foo")

        self._make_sample_file(file_path)

        obj = Pydumpfs()
        obj.do(self.dest_dir, src_dir)

        file = open(file_path, "a")
        try:
            print >> file, "bar"
        finally:
            file.close()

        self._do_test(name)

    def test_change_uid(self):
        name = "change_uid"
        src_dir = self._get_source_directory(name)
        file_path = join(src_dir, "foo")

        self._change_uid(file_path, 1000)

        obj = Pydumpfs(**self._get_pydumpfs_options())
        backup_dir1 = obj.do(self.dest_dir, src_dir)

        self._change_uid(file_path, 0)

        backup_dir2 = obj.do(self.dest_dir, src_dir)

        path1 = backup_dir1 + file_path
        path2 = backup_dir2 + file_path
        self.failIf(samefile(path1, path2))

    def test_change_gid(self):
        name = "change_gid"
        src_dir = self._get_source_directory(name)
        file_path = join(src_dir, "foo")

        self._change_gid(file_path, 1000)

        obj = Pydumpfs(**self._get_pydumpfs_options())
        backup_dir1 = obj.do(self.dest_dir, src_dir)

        self._change_gid(file_path, 0)

        backup_dir2 = obj.do(self.dest_dir, src_dir)

        path1 = backup_dir1 + file_path
        path2 = backup_dir2 + file_path
        self.failIf(samefile(path1, path2))

    def test_mode(self):
        name = "mode"
        src_dir = self._get_source_directory(name)
        file_path = join(src_dir, "foo")

        chmod(file_path, S_IRWXU | S_IRWXG | S_IRWXO)

        self._do_test(name)

    def test_change_mode(self):
        name = "change_mode"
        src_dir = self._get_source_directory(name)
        file_path = join(src_dir, "foo")

        chmod(file_path, S_IRWXU | S_IRWXG | S_IRWXO)

        obj = Pydumpfs(**self._get_pydumpfs_options())
        backup_dir1 = obj.do(self.dest_dir, src_dir)

        chmod(file_path, S_IRUSR)

        backup_dir2 = obj.do(self.dest_dir, src_dir)

        path1 = backup_dir1 + file_path
        path2 = backup_dir2 + file_path
        self.failIf(samefile(path1, path2))

    def test_copy_symlink_dir_twice(self):
        self._do_test_twice("copy_symlink_dir_twice")

    def test_copy_symlink_file_twice(self):
        self._do_test_twice("copy_symlink_file_twice")

    def test_different_uid_symlink_file(self):
        name = "different_uid_symlink_file"
        src_dir = self._get_source_directory(name)
        foo_path = join(src_dir, "foo")
        bar_path = join(src_dir, "bar")

        self._change_uid(foo_path, 1000)
        self._change_uid(bar_path, 0)

        self._do_test(name)

    def test_different_gid_symlink_file(self):
        name = "different_gid_symlink_file"
        src_dir = self._get_source_directory(name)
        foo_path = join(src_dir, "foo")
        bar_path = join(src_dir, "bar")

        self._change_gid(foo_path, 1000)
        self._change_gid(bar_path, 0)

        self._do_test(name)

    def test_copy_dead_link(self):
        name = "copy_dead_link"
        src_dir = self._get_source_directory(name)
        foo_path = join(src_dir, "foo")
        remove(foo_path)
        try:
            self._do_test("copy_dead_link")
        finally:
            self._make_sample_file(foo_path)

    def test_new_file_after_copy(self):
        name = "new_file_after_copy"
        src_dir = self._get_source_directory(name)

        foo_path = join(src_dir, "foo")
        if exists(foo_path):
            remove(foo_path)

        obj = Pydumpfs(**self._get_pydumpfs_options())
        makedirs(self.dest_dir + src_dir)
        obj._copy_recursively(self.dest_dir, src_dir)

        self._make_sample_file(foo_path)

        obj._change_meta_data(self.dest_dir, src_dir)

    def test_fifo(self):
        name = "fifo"
        src_dir = self._get_source_directory(name)
        foo_path = join(src_dir, "foo")
        mkfifo(foo_path)
        try:
            self._do_test(name)
        finally:
            remove(foo_path)

    def test_fifo_twice(self):
        name = "fifo_twice"
        src_dir = self._get_source_directory(name)
        foo_path = join(src_dir, "foo")
        mkfifo(foo_path)
        try:
            self._do_test_twice(name)
        finally:
            remove(foo_path)

    def test_same_name_dir(self):
        name = "same_name_dir"
        src_dir = self._get_source_directory(name)
        filename = "foo"
        prev_dir = join(self.dest_dir, "2008", "01", "06", "000000.000000")
        illegal_dir = join(prev_dir + src_dir, filename)
        makedirs(illegal_dir)

        self._do_test(name)

    def _change_uid(self, path, uid):
        st = stat(path)
        lchown(path, uid, st.st_gid)

    def _change_gid(self, path, gid):
        st = stat(path)
        lchown(path, st.st_uid, gid)

    def _get_source_directory(self, name):
        return abspath(join(dirname(__file__), name))

    def _make_sample_file(self, path):
        file = open(path, "w")
        try:
            print >> file, "foo"
        finally:
            file.close()

    def _compare_file(self, path1, path2):
        import filecmp
        self.assert_(filecmp.cmp(path1, path2),
            "%(path1)r and %(path2)r are not same."
                % dict(path1=path1, path2=path2))

    def _compare_stat_attribute(self, path1, path2, name):
        st1 = lstat(path1)
        st2 = lstat(path2)
        value1 = st1.__getattribute__(name)
        value2 = st2.__getattribute__(name)

        self.assert_(value1 == value2,
            "%(name)r of %(path1)r and that of %(path2)r are not same."
                % dict(path1=path1, path2=path2, name=name))

    def _compare_stat(self, path1, path2):
        self._compare_stat_attribute(path1, path2, "st_uid")
        self._compare_stat_attribute(path1, path2, "st_gid")
        if (not islink(path1)) and (not islink(path2)):
            self._compare_stat_attribute(path1, path2, "st_mode")
            self._compare_stat_attribute(path1, path2, "st_mtime")

    def _compare_link(self, path1, path2):
        if islink(path1):
            self.assert_(islink(path2),
                "%(path1)r is a symbolic link, but %(path2)r is not."
                    % dict(path1=path1, path2=path2))

            link1 = readlink(path1)
            link2 = readlink(path2)
            self.assert_(link1 == link2,
                "The symbolic link %(path1)r and %(path2)r doesn't link to a sa"
                "me file/directory." % dict(path1=path1, path2=path2))
        else:
            self.assert_(not islink(path2),
                "%(path1)r is not a symbolic link, but %(path2)r is."
                    % dict(path1=path1, path2=path2))

    def _compare_file_node(self, backup_dir, dirpath, name, is_func):
        src_path = join(dirpath, name)
        backup_path = backup_dir + src_path
        if not islink(backup_path):
            self.assert_(is_func(backup_path),
                "%(path)r is not a file/directory." % dict(path=backup_path))

        self._compare_link(backup_path, src_path)
        self._compare_stat(backup_path, src_path)

    def _compare_dir_recursively(self, backup_dir, src_dir):
        src_dir = abspath(src_dir)

        dir = dirname(src_dir)
        while dir != "/":
            self.assert_(isdir(dir),
                "%(dir)r is not a directory." % dict(dir=dir))
            self._compare_stat(backup_dir + dir, dir)
            dir = dirname(dir)

        for dirpath, dirnames, filenames in walk(src_dir):
            dirpath = abspath(dirpath)

            for name in dirnames:
                self._compare_file_node(backup_dir, dirpath, name, isdir)

            for filename in filenames:
                path = join(dirpath, filename)
                backup_path = backup_dir + path
                st = lstat(path)
                if S_ISREG(st.st_mode) or S_ISLNK(st.st_mode):
                    self._compare_file_node(
                        backup_dir, dirpath, filename, isfile)
                    path = join(dirpath, filename)
                    if not islink(path):
                        self._compare_file(backup_path, path)
                else:
                    self.failIf(lexists(backup_path),
                        "%(src)r isn't a file nor a link. But %(dest)r exists."
                            % dict(src=path, dest=backup_path))

            for name in listdir(backup_dir + dirpath):
                self.assert_((name in dirnames) or (name in filenames),
                    "%(path)r is not in a source."
                        % dict(path=backup_dir + join(dirpath, name)))

    def _do_test(self, name):
        src_dir = self._get_source_directory(name)

        obj = Pydumpfs(**self._get_pydumpfs_options())
        backup_dir = obj.do(self.dest_dir, src_dir)

        self._compare_dir_recursively(backup_dir, src_dir)

    def test_no_dest_dir(self):
        dest_dir = join(self.dest_dir, "test_no_dest_dir")
        obj = Pydumpfs(**self._get_pydumpfs_options())
        try:
            backup_dir \
                    = obj.do(dest_dir, self._get_source_directory("new_file"))
        except PydumpfsError:
            pass
        else:
            self.assert_(False, "Can backup to directory which doesn't exist.")

    def _get_pydumpfs_options(self):
        #return dict(verbose=True)
        return {}

if __name__ == "__main__":
    main()

# vim: tabstop=4 shiftwidth=4 expandtab softtabstop=4
