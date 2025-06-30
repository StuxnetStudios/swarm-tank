#!/usr/bin/env python
"""Setup script for the Swarm Tank Simulation."""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="swarm-tank-simulation",
    version="1.0.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="A sophisticated swarm intelligence simulation with autonomous bots and emergent behaviors",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/swarm-tank-simulation",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Education",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Games/Entertainment :: Simulation",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Education",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "black",
            "flake8",
            "mypy",
            "pytest",
        ],
    },
    entry_points={
        "console_scripts": [
            "swarm-tank=swarm_tank:main",
        ],
    },
    keywords="swarm intelligence, simulation, pygame, artificial intelligence, emergent behavior",
    project_urls={
        "Bug Reports": "https://github.com/yourusername/swarm-tank-simulation/issues",
        "Source": "https://github.com/yourusername/swarm-tank-simulation",
        "Documentation": "https://github.com/yourusername/swarm-tank-simulation/blob/main/README.md",
    },
)
