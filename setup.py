# -*- coding: utf-8 -*-

# DO NOT EDIT THIS FILE!
# This file has been autogenerated by dephell <3
# https://github.com/dephell/dephell

try:
    from setuptools import setup
except:
    from distutils.core import setup

readme = ""

setup(
    long_description=readme,
    name="fairtorch",
    version="0.1.1",
    python_requires="==3.*,>=3.6.5",
    author="Masashi Sode",
    author_email="masashi.sode@gmail.com",
    maintainer="Akihiko Fukuchi",
    maintainer_email="fukuchi@cl.rcast.u-tokyo.ac.jp",
    license="MIT",
    packages=["fairtorch"],
    package_dir={"": "."},
    package_data={},
    install_requires=["torch==1.*,>=1.6.0"],
    extras_require={
        "dev": [
            "autopep8==1.*,>=1.5.2",
            "black==19.*,>=19.10.0.b0",
            "flake8==3.*,>=3.8.2",
            "isort==4.*,>=4.3.21",
            "mypy==0.*,>=0.782.0",
            "pytest==6.*,>=6.0.1",
        ]
    },
)
