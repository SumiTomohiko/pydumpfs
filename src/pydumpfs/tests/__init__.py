#! python
# -*- coding: utf-8 -*-

from os import makedirs
from os.path import join
import os
import os.path
import shutil
import stat
import unittest

from sys import path
path.insert(0, "src")

from pydumpfs import Pydumpfs, PydumpfsError

class TestPydumpfs(unittest.TestCase):

    def setUp(self):
        import tempfile
        self.dest_dir = tempfile.mkdtemp(prefix="pydumpfs")

    def tearDown(self):
        shutil.rmtree(self.dest_dir)

    def test_copy_dir(self):
        self._do_test("copy_dir")

    def test_copy_dir_twice(self):
        dirname = "copy_dir_twice"
        self._do_test(dirname)
        self._do_test(dirname)

    def test_copy_file(self):
        self._do_test("copy_file")

    def test_copy_symlink_dir(self):
        self._do_test("copy_symlink_dir")

    def test_copy_symlink_file(self):
        self._do_test("copy_symlink_file")

    def test_hard_link(self):
        dirname = "hard_link"
        src_dir = self._get_source_directory(dirname)

        obj = Pydumpfs(**self._get_pydumpfs_options())
        backup_dir1 = obj.do(self.dest_dir, src_dir)
        backup_dir2 = obj.do(self.dest_dir, src_dir)

        foo_src_path = os.path.join(src_dir, "foo")
        path1 = backup_dir1 + foo_src_path
        path2 = backup_dir2 + foo_src_path
        self.assert_(os.path.samefile(path1, path2), 
            "%(path1)r's i-node and %(path2)r's one are not same." 
                % dict(path1=path1, path2=path2))

    def test_new_file(self):
        dirname = "new_file"
        src_dir = self._get_source_directory(dirname)
        file_path = os.path.join(src_dir, "foo")
        if os.path.isfile(file_path):
            os.remove(file_path)
        elif os.path.isdir(file_path):
            shutil.rmtree(file_path)

        obj = Pydumpfs()
        obj.do(self.dest_dir, src_dir)

        self._make_sample_file(file_path)

        self._do_test(dirname)

    def test_remove_file(self):
        dirname = "remove_file"
        src_dir = self._get_source_directory(dirname)
        file_path = os.path.join(src_dir, "foo")

        self._make_sample_file(file_path)

        obj = Pydumpfs()
        obj.do(self.dest_dir, src_dir)

        os.remove(file_path)

        self._do_test(dirname)

    def test_update_file(self):
        dirname = "update_file"
        src_dir = self._get_source_directory(dirname)
        file_path = os.path.join(src_dir, "foo")

        self._make_sample_file(file_path)

        obj = Pydumpfs()
        obj.do(self.dest_dir, src_dir)

        file = open(file_path, "a")
        try:
            print >> file, "bar"
        finally:
            file.close()

        self._do_test(dirname)

    def test_change_uid(self):
        dirname = "change_uid"
        src_dir = self._get_source_directory(dirname)
        file_path = os.path.join(src_dir, "foo")

        self._change_uid(file_path, 1000)

        obj = Pydumpfs(**self._get_pydumpfs_options())
        backup_dir1 = obj.do(self.dest_dir, src_dir)

        self._change_uid(file_path, 0)

        backup_dir2 = obj.do(self.dest_dir, src_dir)

        path1 = backup_dir1 + file_path
        path2 = backup_dir2 + file_path
        self.failIf(os.path.samefile(path1, path2))

    def test_change_gid(self):
        dirname = "change_gid"
        src_dir = self._get_source_directory(dirname)
        file_path = os.path.join(src_dir, "foo")

        self._change_gid(file_path, 1000)

        obj = Pydumpfs(**self._get_pydumpfs_options())
        backup_dir1 = obj.do(self.dest_dir, src_dir)

        self._change_gid(file_path, 0)

        backup_dir2 = obj.do(self.dest_dir, src_dir)

        path1 = backup_dir1 + file_path
        path2 = backup_dir2 + file_path
        self.failIf(os.path.samefile(path1, path2))

    def test_mode(self):
        dirname = "mode"
        src_dir = self._get_source_directory(dirname)
        file_path = os.path.join(src_dir, "foo")

        os.chmod(file_path, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)

        self._do_test(dirname)

    def test_change_mode(self):
        dirname = "change_mode"
        src_dir = self._get_source_directory(dirname)
        file_path = os.path.join(src_dir, "foo")

        os.chmod(file_path, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)

        obj = Pydumpfs(**self._get_pydumpfs_options())
        backup_dir1 = obj.do(self.dest_dir, src_dir)

        os.chmod(file_path, stat.S_IRUSR)

        backup_dir2 = obj.do(self.dest_dir, src_dir)

        path1 = backup_dir1 + file_path
        path2 = backup_dir2 + file_path
        self.failIf(os.path.samefile(path1, path2))

    def test_copy_symlink_dir_twice(self):
        dirname = "copy_symlink_dir_twice"
        self._do_test(dirname)
        self._do_test(dirname)

    def test_copy_symlink_file_twice(self):
        dirname = "copy_symlink_file_twice"
        self._do_test(dirname)
        self._do_test(dirname)

    def test_different_uid_symlink_file(self):
        dirname = "different_uid_symlink_file"
        src_dir = self._get_source_directory(dirname)
        foo_path = os.path.join(src_dir, "foo")
        bar_path = os.path.join(src_dir, "bar")

        self._change_uid(foo_path, 1000)
        self._change_uid(bar_path, 0)

        self._do_test(dirname)

    def test_different_gid_symlink_file(self):
        dirname = "different_gid_symlink_file"
        src_dir = self._get_source_directory(dirname)
        foo_path = os.path.join(src_dir, "foo")
        bar_path = os.path.join(src_dir, "bar")

        self._change_gid(foo_path, 1000)
        self._change_gid(bar_path, 0)

        self._do_test(dirname)

    def test_copy_dead_link(self):
        dirname = "copy_dead_link"
        src_dir = self._get_source_directory(dirname)
        foo_path = os.path.join(src_dir, "foo")
        os.remove(foo_path)
        try:
            self._do_test("copy_dead_link")
        finally:
            self._make_sample_file(foo_path)

    def test_new_file_after_copy(self):
        dirname = "new_file_after_copy"
        src_dir = self._get_source_directory(dirname)

        foo_path = os.path.join(src_dir, "foo")
        if os.path.exists(foo_path):
            os.remove(foo_path)

        obj = Pydumpfs(**self._get_pydumpfs_options())
        os.makedirs(self.dest_dir + src_dir)
        obj._copy_recursively(self.dest_dir, src_dir)

        self._make_sample_file(foo_path)

        obj._change_meta_data(self.dest_dir, src_dir)

    def test_fifo(self):
        dirname = "fifo"
        src_dir = self._get_source_directory(dirname)
        foo_path = os.path.join(src_dir, "foo")
        os.mkfifo(foo_path)
        try:
            self._do_test(dirname)
        finally:
            os.remove(foo_path)

    def test_fifo_twice(self):
        dirname = "fifo_twice"
        src_dir = self._get_source_directory(dirname)
        foo_path = os.path.join(src_dir, "foo")
        os.mkfifo(foo_path)
        try:
            self._do_test(dirname)
            self._do_test(dirname)
        finally:
            os.remove(foo_path)

    def test_same_name_dir(self):
        dirname = "same_name_dir"
        src_dir = self._get_source_directory(dirname)
        filename = "foo"
        prev_dir = join(self.dest_dir, "2008", "01", "06", "000000.000000")
        illegal_dir = join(prev_dir + src_dir, filename)
        makedirs(illegal_dir)

        self._do_test(dirname)

    def _change_uid(self, path, uid):
        st = os.stat(path)
        os.lchown(path, uid, st.st_gid)

    def _change_gid(self, path, gid):
        st = os.stat(path)
        os.lchown(path, st.st_uid, gid)

    def _get_source_directory(self, dirname):
        return os.path.abspath(os.path.join(os.path.dirname(__file__), dirname))

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
        st1 = os.lstat(path1)
        st2 = os.lstat(path2)
        value1 = st1.__getattribute__(name)
        value2 = st2.__getattribute__(name)

        self.assert_(value1 == value2, 
            "%(name)r of %(path1)r and that of %(path2)r are not same." 
                % dict(path1=path1, path2=path2, name=name))

    def _compare_stat(self, path1, path2):
        self._compare_stat_attribute(path1, path2, "st_uid")
        self._compare_stat_attribute(path1, path2, "st_gid")
        if (not os.path.islink(path1)) and (not os.path.islink(path2)):
            self._compare_stat_attribute(path1, path2, "st_mode")
            self._compare_stat_attribute(path1, path2, "st_mtime")

    def _compare_link(self, path1, path2):
        if os.path.islink(path1):
            self.assert_(os.path.islink(path2), 
                "%(path1)r is a symbolic link, but %(path2)r is not." 
                    % dict(path1=path1, path2=path2))

            link1 = os.readlink(path1)
            link2 = os.readlink(path2)
            self.assert_(link1 == link2, 
                "The symbolic link %(path1)r and %(path2)r doesn't link to a sa"
                "me file/directory." % dict(path1=path1, path2=path2))
        else:
            self.assert_(not os.path.islink(path2), 
                "%(path1)r is not a symbolic link, but %(path2)r is." 
                    % dict(path1=path1, path2=path2))

    def _compare_file_node(self, backup_dir, dirpath, name, is_func):
        src_path = os.path.join(dirpath, name)
        backup_path = backup_dir + src_path
        if not os.path.islink(backup_path):
            self.assert_(is_func(backup_path), 
                "%(path)r is not a file/directory." % dict(path=backup_path))

        self._compare_link(backup_path, src_path)
        self._compare_stat(backup_path, src_path)

    def _compare_dir_recursively(self, backup_dir, src_dir):
        src_dir = os.path.abspath(src_dir)

        dir = os.path.dirname(src_dir)
        while dir != "/":
            self.assert_(os.path.isdir(dir), 
                "%(dir)r is not a directory." % dict(dir=dir))
            self._compare_stat(backup_dir + dir, dir)

            dir = os.path.dirname(dir)

        for dirpath, dirnames, filenames in os.walk(src_dir):
            dirpath = os.path.abspath(dirpath)

            for dirname in dirnames:
                self._compare_file_node(
                    backup_dir, dirpath, dirname, os.path.isdir)

            for filename in filenames:
                path = os.path.join(dirpath, filename)
                backup_path = backup_dir + path
                st = os.lstat(path)
                if stat.S_ISREG(st.st_mode) or stat.S_ISLNK(st.st_mode):
                    self._compare_file_node(
                        backup_dir, dirpath, filename, os.path.isfile)
                    path = os.path.join(dirpath, filename)
                    if not os.path.islink(path):
                        self._compare_file(backup_path, path)
                else:
                    self.failIf(os.path.lexists(backup_path), 
                        "%(src)r isn't a file nor a link. But %(dest)r exists."
                            % dict(src=path, dest=backup_path))

            for name in os.listdir(backup_dir + dirpath):
                self.assert_((name in dirnames) or (name in filenames), 
                    "%(path)r is not in a source." 
                        % dict(path=backup_dir + os.path.join(dirpath, name)))

    def _do_test(self, dirname):
        src_dir = self._get_source_directory(dirname)

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
    unittest.main()

# vim: tabstop=4 shiftwidth=4 expandtab softtabstop=4
