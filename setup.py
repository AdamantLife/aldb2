import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="AL Anime Database 2",
    version="1.0.0",
    author="AdamantLife",
    author_email="contact.adamantmedia@gmail.com",
    description="V2 of the AnimeDatabase",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/AdamantLife/aldb2",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.8',

    install_requires = [
        "selenium",
"click",
"requests",
#git+https://github.com/AdamantLife/alcustoms.git
"bs4",
"pillow",
"numpy",
"matplotlib",
"openpyxl",
"python-Levenshtein"
        ]
)
