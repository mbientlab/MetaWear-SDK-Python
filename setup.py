from multiprocessing import cpu_count
from shutil import copy2, move
from subprocess import call, STDOUT
from setuptools import setup
from setuptools.command.build_py import build_py

import os
import platform
import sys

machine = "arm" if "arm" in platform.machine() else ("x64" if sys.maxsize > 2**32 else "x86")

class MetaWearBuild(build_py):
    @staticmethod
    def _move(src, dest, basename):
        for f in os.listdir(src):
            if (f.startswith(basename)):
                move(os.path.join(src, f), dest)

    def run(self):
        root = os.path.dirname(os.path.abspath(__file__))
        dest = os.path.join("mbientlab", "metawear")
        cpp_sdk = os.path.join(root, 'MetaWear-SDK-Cpp')
        dist_dir = os.path.join(cpp_sdk, 'dist', 'release', 'lib', machine)

        if os.path.exists(os.path.join(root, '.git')):
            status = call(["git", "submodule", "update", "--init"], cwd=root, stderr=STDOUT)
            if (status != 0):
                raise RuntimeError("Could not init git submodule")

        if (platform.system() == 'Windows'):
            if (call(["MSBuild.exe", "MetaWear.Win32.vcxproj", "/p:Platform=%s" % machine, "/p:Configuration=Release"], cwd=cpp_sdk, stderr=STDOUT) != 0):
                raise RuntimeError("Failed to compile MetaWear.dll")

            move(os.path.join(dist_dir, "MetaWear.Win32.dll"), dest)
        elif (platform.system() == 'Linux'):
            status = call(["make", "-C", "MetaWear-SDK-Cpp", "OPT_FLAGS=-Wno-strict-aliasing", "-j%d" % (cpu_count())], cwd=root, stderr=STDOUT)
            if (status != 0):
                raise RuntimeError("Failed to compile C++ SDK")

            MetaWearBuild._move(dist_dir, dest, 'libmetawear.so')
        else:
            raise RuntimeError("MetaWear Python SDK not supported for '%s'" % platform.system())

        copy2(os.path.join(cpp_sdk, 'bindings', 'python', 'mbientlab', 'metawear', 'cbindings.py'), dest)
        build_py.run(self)

so_pkg_data = ['libmetawear.so'] if platform.system() == 'Linux' else ['MetaWear.Win32.dll']
setup(
    name='metawear',
    packages=['mbientlab', 'mbientlab.metawear'],
    version='0.4.0',
    description='Python bindings for the MetaWear C++ SDK by MbientLab',
    long_description=open(os.path.join(os.path.dirname(__file__), "README.rst")).read(),
    package_data={'mbientlab.metawear': so_pkg_data},
    include_package_data=True,
    url='https://github.com/mbientlab/MetaWear-SDK-Python',
    author='MbientLab',
    author_email="hello@mbientlab.com",
    install_requires=[
        'warble >= 1.0, < 2.0',
        'requests'
    ],
    cmdclass={
        'build_py': MetaWearBuild,
    },
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
