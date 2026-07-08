"""Nooht Framework Setup"""

from setuptools import setup, find_packages

setup(
    name="nooht",
    version="0.1.3",
    description="Model-agnostic code intelligence memory engine",
    author="Nooht Team",
    packages=find_packages(),
    install_requires=[
        "numpy>=1.24.0",
        "duckdb>=0.9.0",
    ],
    extras_require={
        "transformers": ["transformers>=4.30.0", "torch>=2.0.0"],
        "faiss": ["faiss-cpu>=1.7.0"],
        "all": ["transformers>=4.30.0", "torch>=2.0.0", "faiss-cpu>=1.7.0"],
    },
    python_requires=">=3.8",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Software Development :: Libraries",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
)
