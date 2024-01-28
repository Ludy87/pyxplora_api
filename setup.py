"""setup."""

import configparser

import setuptools

with open("README.md", encoding="utf8") as fh:
    long_description = fh.read()

with open("./src/pyxplora_api/const_version.py", encoding="utf8") as f:
    config_string = "[dummy_section]\n" + f.read()
    config = configparser.ConfigParser()
    config.read_string(config_string)
    version = config["dummy_section"]["VERSION"].strip('"')

requirements_array = []
with open("requirements.txt", encoding="utf8") as my_file:
    for line in my_file:
        requirements_array.append(line.replace("\n", ""))

setuptools.setup(
    name="pyxplora_api",
    version=version,
    author="Ludy87",
    author_email="android@astra-g.org",
    description="Python Xplora® Api",
    license="MIT",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Ludy87/pyxplora_api",
    project_urls={
        "Bug Tracker": "https://github.com/Ludy87/pyxplora_api/issues",
    },
    package_dir={"": "src"},
    packages=setuptools.find_packages(where="src"),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Intended Audience :: Developers",
        "Topic :: Software Development",
        "Topic :: Utilities",
        "Topic :: Home Automation",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    keywords="api xplora watch",
    install_requires=requirements_array,
    python_requires=">=3.9",
)
