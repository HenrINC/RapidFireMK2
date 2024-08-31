from setuptools import setup, find_packages

setup(
    name='YesMan-PS3',
    version='0.1',
    packages=[
        'yesman',
        'yesman.parsers',
        "yesman.parsers.xmb",
        'yesman.file_transfer',
        'yesman.wrappers',
    ],
    install_requires=[
        "fire",
        "numpy",
        "aioftp",
        "aiohttp",
        "aiofiles",
        "pydantic",
        "requests",
        "opencv-python",
        "beautifulsoup4",
    ],
    entry_points={
    },
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3.11",
        "Natural Language :: English",
        "Operating System :: Unix" #Intended for debian bookworm slim docker image
    ],
    include_package_data=True,
)

