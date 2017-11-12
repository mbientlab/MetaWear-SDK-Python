from distutils.dir_util import copy_tree
from multiprocessing import cpu_count
from shutil import copy2
from subprocess import call, STDOUT
from setuptools import setup
from setuptools.command.build_py import build_py

import os
import platform
import sys

machine = "arm" if "arm" in platform.machine() else ("x64" if sys.maxsize > 2**32 else "x86")

class MetaWearBuild(build_py):
    def run(self):
        root = os.path.dirname(os.path.abspath(__file__))

        if os.path.exists(os.path.join(root, '.git')):
            status = call(["git", "submodule", "update", "--init"], cwd=root, stderr=STDOUT)
            if (status != 0):
                raise RuntimeError("Could not init git submodule")

        status = call(["make", "-C", "MetaWear-SDK-Cpp", "OPT_FLAGS=-Wno-strict-aliasing", "-j%d" % (cpu_count())], cwd=root, stderr=STDOUT)
        if (status != 0):
            raise RuntimeError("Failed to compile C++ SDK")

        copy_tree('MetaWear-SDK-Cpp/dist/release/lib/%s/' % (machine), "mbientlab/metawear")
        copy2('MetaWear-SDK-Cpp/bindings/python/mbientlab/metawear/cbindings.py', "mbientlab/metawear")

        build_py.run(self)

setup(
    name='metawear',
    packages=['mbientlab', 'mbientlab.metawear'],
    version='0.3.0',
    description='Python bindings for the MetaWear C++ SDK by MbientLab',
    long_description=open(os.path.join(os.path.dirname(__file__), "README.rst")).read(),
    package_data={'mbientlab.metawear': ['libmetawear.so*']},
    include_package_data=True,
    url='https://github.com/mbientlab/MetaWear-SDK-Python',
    author='MbientLab',
    author_email="hello@mbientlab.com",
    install_requires=[
        'gattlib==0.20171002',
        'requests'
    ],
    cmdclass={
        'build_py': MetaWearBuild,
    },
    dependency_links=[
        'git+https://github.com/mbientlab/pygattlib.git/@master#egg=gattlib-0.20171002',
        'git+https://github.com/mbientlab/pygattlib.git@master#egg=gattlib-0.20171002'
    ],
    keywords = ['sensors', 'mbientlab', 'metawear', 'bluetooth le', 'native'],
    python_requires='>=2.7',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
    ]
)
