from setuptools import setup, find_packages

setup(
    name='YesMan-PS3',
    version='0.1',
    packages=find_packages(),
    install_requires=[
        "fire",
        "numpy",
        "aioftp",
        "aiohttp",
        "fastapi",
        "uvicorn",
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
        "Programming Language :: Python :: 3",
        "Natural Language :: English",
        "Operating System :: Unix" #Intended for debian bookworm slim docker image
    ],
    include_package_data=True,
)

