import setuptools
import configparser

with open("README.md", "r") as fh:
    long_description = fh.read()

with open("./src/pyxplora_api/const.py") as f:
    config_string = "[dummy_section]\n" + f.read()
    config = configparser.ConfigParser()
    config.read_string(config_string)
    version = config["dummy_section"]["VERSION"].strip('"')

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
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Intended Audience :: Developers",
        "Topic :: Software Development",
        "Topic :: Utilities",
        "Topic :: Home Automation",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    keywords="api xplora watch",
    install_requires=["python-graphql-client==0.4.3"],
    python_requires=">=3.6",
)
