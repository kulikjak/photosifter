import pathlib
from setuptools import setup

HERE = pathlib.Path(__file__).parent
README = (HERE / "README.md").read_text()

setup(
    name="photosifter",
    version="0.1.1",
    description="Photo sifter is a simple application, written in Python, for smooth photo sifting and comparison.",
    long_description=README,
    long_description_content_type="text/markdown",
    url="https://github.com/kulikjak/photosifter",
    author="Jakub Kulik",
    author_email="kulikjak@gmail.com",
    license="MIT",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Operating System :: MacOS",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: POSIX",
        "Operating System :: Unix",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Topic :: Artistic Software",
        "Topic :: Multimedia :: Graphics",
    ],
    packages=["photosifter", "gphotos_deleter"],
    include_package_data=True,
    install_requires=[
        "google-api-python-client>=1.7.0",
        "numpy",
        "opencv-python",
        "oauth2client>=4.1.3"],
    extras_require={
        'gphotos_deleter': [
            "selenium",
        ],
    },
    python_requires=">=3.6",
    entry_points={
        "console_scripts": [
            "photosifter=photosifter.__main__:main",
            "gphotos_deleter=gphotos_deleter.gphotos_deleter:main",
        ]
    },
)
