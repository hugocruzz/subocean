from setuptools import setup, find_packages

setup(
    name="subocean",
    version="0.1",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "pandas>=2.0.0",
        "numpy>=1.22.0",
        "pytest>=7.0.0",
    ],
    python_requires=">=3.8",
    author="SENSE Unit",
    description="SubOcean data processing tools",
)