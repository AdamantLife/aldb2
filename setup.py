import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(

    name="AL Anime Database 2",
    version="1.1.0",
    author="AdamantLife",
    author_email="contact.adamantmedia@gmail.com",
    description="V2 of the AnimeDatabase",
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
        "alcustoms @ git+https://github.com/AdamantLife/alcustoms",
        "al-excel @ git+https://github.com/AdamantLife/AL_Excel",
        "al-decorators @ git+https://github.com/AdamantLife/AL_Decorators",
        "al-web @ git+https://github.com/AdamantLife/AL_Web",
        ],
        entry_points={
          "console_scripts": ["gammut=aldb2.SeasonCharts.cli:cli"]
      }
)
