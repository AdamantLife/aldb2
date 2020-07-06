import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="aldb2",
    version="2.0.0",
    author="AdamantLife",
    author_email="contact.adamantmedia@gmail.com",
    description="",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/AdamantLife/aldb2",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.8',

    install_requires = [
        "selenium",
        "click",
        "requests",
        "bs4",
        "pillow",
        "numpy",
        "matplotlib",
        "openpyxl",
        "python-Levenshtein",
        ]
)
