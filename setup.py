from distutils.command.clean import clean
from multiprocessing import cpu_count
from shutil import copy2, move
from subprocess import call, STDOUT
from setuptools import setup
from setuptools.command.build_py import build_py

import os
import platform
import sys

machine = os.environ['MACHINE'] if 'MACHINE' in os.environ else ("arm" if ("arm" in platform.machine()) or ("aarch64" in platform.machine()) else ("x64" if sys.maxsize > 2**32 else "x86"))
root = os.path.dirname(os.path.abspath(__file__))
dest = os.path.join("mbientlab", "metawear")

class MetaWearClean(clean):
    def run(self):
        bindings = os.path.join(dest, "cbindings.py")
        if os.path.isfile(bindings):
            os.remove(bindings)

        if (platform.system() == 'Windows'):
            dll = os.path.join(dest, "MetaWear.Win32.dll")
            if os.path.isfile(dll):
                os.remove(dll)
        elif (platform.system() == 'Linux'):
            for f in os.listdir(dest):
                if (f.startswith("libmetawear.so")):
                    os.remove(os.path.join(dest, f))

class MetaWearBuild(build_py):
    @staticmethod
    def _move(src, dest, basename):
        for f in os.listdir(src):
            if (f.startswith(basename)):
                move(os.path.join(src, f), dest)

    def run(self):        
        cpp_sdk = os.path.join(root, 'MetaWear-SDK-Cpp')
        system = platform.system()
        dist_dir = os.path.join(cpp_sdk, 'dist', 'release', 'lib', "Win32" if machine == "x86" and system == "Windows" else machine)

        if os.path.exists(os.path.join(root, '.git')):
            status = call(["git", "submodule", "update", "--init"], cwd=root, stderr=STDOUT)
            if (status != 0):
                raise RuntimeError("Could not init git submodule")

        if (system == 'Windows'):
            if not os.path.exists(os.path.join(dist_dir, "MetaWear.Win32.dll")):
                if (call(["MSBuild.exe", "MetaWear.Win32.vcxproj", "/p:Platform=%s" % machine, "/p:Configuration=Release"], cwd=cpp_sdk, stderr=STDOUT) != 0):
                    raise RuntimeError("Failed to compile MetaWear.dll")

            copy2(os.path.join(dist_dir, "MetaWear.Win32.dll"), dest)
        elif (system == 'Linux'):
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
    version='1.0.6',
    description='Python bindings for the MetaWear C++ SDK by MbientLab',
    long_description=open(os.path.join(os.path.dirname(__file__), "README.rst")).read(),
    package_data={'mbientlab.metawear': so_pkg_data},
    include_package_data=True,
    url='https://github.com/mbientlab/MetaWear-SDK-Python',
    author='MbientLab',
    author_email="hello@mbientlab.com",
    install_requires=[
        'warble >= 1.2.8, < 2.0',
        'requests',
        'pyserial'
    ],
    cmdclass={
        'build_py': MetaWearBuild,
        'clean': MetaWearClean
    },
    keywords = ['sensors', 'mbientlab', 'metawear', 'bluetooth le', 'native'],
    python_requires='>=3.4',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Operating System :: POSIX :: Linux',
        'Operating System :: Microsoft :: Windows :: Windows 10',
        'Programming Language :: Python :: 3',
    ]
)
