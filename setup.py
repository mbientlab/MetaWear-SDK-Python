import os
import sys
from distutils.dir_util import copy_tree
from shutil import copy2
from subprocess import call, STDOUT
from setuptools import setup
from setuptools.command.install import install

machine = "x64" if sys.maxsize > 2**32 else "x86"

class MetaWearInstall(install):
    def run(self):
        dir = os.path.join(os.path.dirname(os.path.abspath(__file__)))
        status = call(["make", "-C", "MetaWear-SDK-Cpp", "OPT_FLAGS=-Wno-strict-aliasing", "-j"], cwd=dir, stderr=STDOUT)
        if (status != 0):
            raise RuntimeError("Failed to compile C++ SDK")

        copy_tree('MetaWear-SDK-Cpp/dist/release/lib/%s/' % (machine), "mbientlab/metawear")
        copy2('MetaWear-SDK-Cpp/bindings/python/mbientlab/metawear/cbindings.py', "mbientlab/metawear")

        install.run(self)

setup(
    name='metawear',
    packages=['mbientlab.metawear'],
    version='0.1.0',
    description='Python bindings for the MetaWear C++ SDK',
    package_data={'mbientlab.metawear': ['libmetawear.so*']},
    include_package_data=True,
    url='https://github.com/mbientlab/MetaWear-SDK-Python',
    author='MbientLab',
    cmdclass={
        'install': MetaWearInstall,
    }
)
