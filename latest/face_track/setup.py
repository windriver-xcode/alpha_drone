#!/usr/bin/env python
####
# face_track Python Package:
#
# The face_track python package represents the core Tello control to track human face.
# To install this package, run the following commands:
#
# User Install / Upgrade:
# ```
# pip install --upgrade .
# ```
#
# Developer and Dynamic Installation:
# ```
# pip install -e .
# ```
###

from setuptools import find_packages, setup

# Setup a python package using setup-tools. This is a newer (and more recommended) technology
# then distutils.
setup(
    ####
    # Package Description:
    #
    # Basic package information. Describes the package and the data contained inside. This
    # information should match the F prime description information.
    ####
    name="face_track",
    version="0.0.2",
    license="MIT License",
    description="Tello control to track human face",
    long_description="""
This package contains the tello control to track human face. After running, the Tello drone first hovers to
1.7 meters high, then starts to recognize and track the closest human face. PID control is applied to stablize
the drone. Durin the flight, if any key is pressed, then program exits and the drone lands immediately. When
face track python script is running, it automatically record video (640*480) to its working directory in the name
vid-YYYYMMDD-hhmmss.avi.
    """,
    url="https://github.com/shijq23/alpha_drone",
    keywords=["tello", "embedded", "opencv", "AI", "drone", "PID"],
    project_urls={"Issue Tracker": "https://github.com/shijq23/alpha_drone/issues"},
    author="shijq23",
    author_email="N/A",
    ####
    # Included Packages:
    #
    # Will search for and included all python packages under the "src" directory.  The root package
    # is set to 'src' to avoid package names of the form src.face_track.
    ####
    packages=find_packages("src"),
    package_dir={"": "src"},
    ####
    # Classifiers:
    #
    # Standard Python classifiers used to describe this package.
    ####
    classifiers=[
        # complete classifier list: http://pypi.python.org/pypi?%3Aaction=list_classifiers
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Topic :: Software Development :: Embedded Systems",
    ],
    # Requires Python 3.6+
    python_requires=">=3.6",
    install_requires=[
        'opencv-python;python_version >="4.5"',
        'djitellopy2;python_version >="2.3"',
        'numpy;python_version >="1.20"',
    ],
    extras_require={"dev": ["black", "pytest", "pylint", "pre-commit"]},
    # Setup and test requirements, not needed by normal install
    setup_requires=["pytest-runner"],
    tests_require=["pytest"],
    # Create a set of executable entry-points for running directly from the package
    entry_points={
        "console_scripts": ["face_track = face_track.__main__:main"],
        "gui_scripts": ["face_track = face_track.__main__:main"],
    },
)