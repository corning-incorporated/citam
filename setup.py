#  Copyright 2021. Corning Incorporated. All rights reserved.
#
#  This software may only be used in accordance with the identified license(s).
#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
#  CORNING BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
#  ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
#  CONNECTION WITH THE SOFTWARE OR THE USE OF THE SOFTWARE.
#  ==========================================================================
import setuptools

from build_tasks import NodeJSBuild

setuptools.setup(
    name="CITAM",
    # Version number format defined by https://www.python.org/dev/peps/pep-0440
    use_scm_version=True,
    author="Corning Inc",
    description="The COVID Indoor Transmission Agent-based Modeling Platform",
    packages=setuptools.find_packages(exclude=["*.tests.*"],),
    entry_points={"console_scripts": ["citam=citam.cli:main"]},
    cmdclass={"build_js": NodeJSBuild},
    include_package_data=True,
    zip_safe=True,
    install_requires=[
        "svgpathtools",
        "numpy",
        "scipy",
        "networkx",
        "docutils==0.15",  # Required for boto3
        "progressbar2",
        "matplotlib",
        "boto3",
        "falcon",
        "appdirs",
        "rich[jupyter]",
    ],
    setup_requires=["setuptools_scm"],
    # For a list of classifiers, see https://pypi.org/classifiers/
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
    ],
)
