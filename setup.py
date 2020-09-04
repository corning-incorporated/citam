#  Copyright 2020. Corning Incorporated. All rights reserved.
#
#  This software may only be used in accordance with the licenses granted by
#  Corning Incorporated. All other uses as well as any copying, modification
#  or reverse engineering of the software is strictly prohibited.
#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
#  CORNING BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
#  ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
#  CONNECTION WITH THE SOFTWARE OR THE USE OF THE SOFTWARE.
#  ==========================================================================

import setuptools

from setuptools.command.sdist import sdist
from distutils.command.build import build
from build_tasks import NodeJSBuild


class sdist_custom(sdist):
    """Custom sdist command which includes the build_js subcommand"""
    sub_commands = [('build_js', None)] + sdist.sub_commands


class build_custom(build):
    """Custom build command which includes the build_js subcommand"""
    sub_commands = [('build_js', None)] + build.sub_commands


setuptools.setup(
    name="CITAM",
    # Version number format defined by https://www.python.org/dev/peps/pep-0440
    version="0.9.0",
    author="Corning Inc",
    description="The COVID Indoor Transmission Agent-based Modeling Platform",
    packages=setuptools.find_packages(
        exclude=['*.tests.*', '*.test.*'],
    ),
    entry_points={
        'console_scripts': ['citam=citam.cli:main']
    },
    cmdclass={
        'build_js': NodeJSBuild,
        'sdist': sdist_custom,
        'build': build_custom,
    },
    include_package_data=True,
    zip_safe=True,
    install_requires=[
        'svgpathtools',
        'numpy',
        'scipy',
        'networkx',
        'docutils==0.15',  # Required for boto3
        'progressbar2',
        'matplotlib',
        'boto3',
        'falcon',
    ],

    # For a list of classifiers, see https://pypi.org/classifiers/
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)"
    ],
)
