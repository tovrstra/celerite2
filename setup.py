#!/usr/bin/env python

# Inspired by:
# https://hynek.me/articles/sharing-your-labor-of-love-pypi-quick-and-dirty/
import codecs
import os
import re

from pybind11.setup_helpers import Pybind11Extension, build_ext
from setuptools import find_packages, setup

# PROJECT SPECIFIC

NAME = "celerite2"
PACKAGES = find_packages(where="python")
META_PATH = os.path.join("python", "celerite2", "__init__.py")
CLASSIFIERS = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: Developers",
    "Intended Audience :: Science/Research",
    "License :: OSI Approved :: MIT License",
    "Operating System :: OS Independent",
    "Programming Language :: Python",
    "Programming Language :: Python :: 3",
]
INSTALL_REQUIRES = ["numpy>=1.13.0"]
SETUP_REQUIRES = INSTALL_REQUIRES + [
    "pybind11>=2.4",
    "setuptools>=40.6.0",
    "setuptools_scm",
    "wheel",
]
EXTRA_REQUIRE = {
    "style": ["isort", "black", "black_nbconvert"],
    "test": [
        "coverage[toml]",
        "pytest",
        "pytest-cov",
        "scipy",
        "celerite>=0.3.1",
    ],
    "pymc3": ["pymc3>=3.9", "numpy<1.22"],
    "pymc4": ["pymc>=4,<5"],
    "jax": ["jax", "jaxlib"],
    "docs": [
        "sphinx",
        "sphinx-material",
        "sphinx_copybutton",
        "breathe",
        "myst-nb",
    ],
    "tutorials": [
        "matplotlib",
        "scipy",
        "emcee",
        "pymc>=4,<5",
        "tqdm",
        "numpyro",
    ],
}
EXTRA_REQUIRE["docs"] += EXTRA_REQUIRE["tutorials"]
EXTRA_REQUIRE["theano"] = EXTRA_REQUIRE["pymc3"]
EXTRA_REQUIRE["dev"] = (
    EXTRA_REQUIRE["style"]
    + EXTRA_REQUIRE["test"]
    + ["pre-commit", "nbstripout", "flake8"]
)

include_dirs = [
    "c++/include",
    "c++/vendor/eigen",
    "python/celerite2",
]
ext_modules = [
    Pybind11Extension(
        "celerite2.driver",
        ["python/celerite2/driver.cpp"],
        include_dirs=include_dirs,
        language="c++",
    ),
    Pybind11Extension(
        "celerite2.backprop",
        ["python/celerite2/backprop.cpp"],
        include_dirs=include_dirs,
        language="c++",
    ),
    Pybind11Extension(
        "celerite2.jax.xla_ops",
        ["python/celerite2/jax/xla_ops.cpp"],
        include_dirs=include_dirs,
        language="c++",
    ),
]

# END PROJECT SPECIFIC


HERE = os.path.dirname(os.path.realpath(__file__))


def read(*parts):
    with codecs.open(os.path.join(HERE, *parts), "rb", "utf-8") as f:
        return f.read()


def find_meta(meta, meta_file=read(META_PATH)):
    meta_match = re.search(
        r"^__{meta}__ = ['\"]([^'\"]*)['\"]".format(meta=meta), meta_file, re.M
    )
    if meta_match:
        return meta_match.group(1)
    raise RuntimeError("Unable to find __{meta}__ string.".format(meta=meta))


if __name__ == "__main__":
    setup(
        name=NAME,
        use_scm_version={
            "write_to": os.path.join(
                "python", NAME, "{0}_version.py".format(NAME)
            ),
            "write_to_template": '__version__ = "{version}"\n',
        },
        author=find_meta("author"),
        author_email=find_meta("email"),
        maintainer=find_meta("author"),
        maintainer_email=find_meta("email"),
        url=find_meta("uri"),
        license=find_meta("license"),
        description=find_meta("description"),
        long_description=read("README.md"),
        long_description_content_type="text/markdown",
        packages=PACKAGES,
        package_dir={"": "python"},
        include_package_data=True,
        python_requires=">=3.6",
        install_requires=INSTALL_REQUIRES,
        setup_requires=SETUP_REQUIRES,
        extras_require=EXTRA_REQUIRE,
        classifiers=CLASSIFIERS,
        zip_safe=False,
        ext_modules=ext_modules,
        cmdclass={"build_ext": build_ext},
    )
