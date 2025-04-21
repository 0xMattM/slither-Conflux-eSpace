from setuptools import setup, find_namespace_packages

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="slither-conflux",
    description="Slither plugin for analyzing Conflux eSpace smart contracts",
    url="https://github.com/0xMattM/slither-Conflux-eSpace",
    author="0xMattM",
    version="0.1.0",
    packages=find_namespace_packages(include=["slither*"]),
    python_requires=">=3.8",
    install_requires=[
        "slither-analyzer>=0.11.0",
        "web3>=7.10.2, <8",
        "eth-abi>=4.0.0",
        "eth-typing>=3.0.0",
        "eth-utils>=2.1.0",    
        "requests>=2.31.0",
        "solc-select>=1.0.0",
    ],
    extras_require={
        "lint": [
            "black==22.3.0",
            "pylint==3.0.3",
        ],
        "test": [
            "pytest",
            "pytest-cov",
            "pytest-xdist",
            "deepdiff",
            "numpy",
            "coverage[toml]",
            "filelock",
            "pytest-insta",
        ],
        "doc": [
            "pdoc",
        ],
        "dev": [
            "slither-analyzer[lint,test,doc]",
            "openai",
        ],
    },
    license="AGPL-3.0",
    long_description=long_description,
    long_description_content_type="text/markdown",
    entry_points={
        "console_scripts": [
            "slither-conflux = slither.tools.conflux_espace.__main__:main",
            "espace-source = slither.tools.conflux_espace.source_downloader:main",
        ]
    },
)
