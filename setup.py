#! python
# -*- coding: utf-8 -*-

import ez_setup
ez_setup.use_setuptools()

from setuptools import setup, find_packages

setup(name="pydumpfs", version="0.3", packages=find_packages("src"), 
    package_dir={"": "src"}, test_suite="pydumpfs.tests", scripts=["pydumpfs"], 

    author="Sumi Tomohiko", author_email="tom@nekomimists.ddo.jp", 
    description="pdumpfs-like backup tool", license="MIT", 
    url="http://d.hatena.ne.jp/SumiTomohiko/")

# vim: tabstop=4 shiftwidth=4 expandtab softtabstop=4
