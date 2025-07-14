from setuptools import setup, find_packages

setup(
    name="olakai_sdk",
    version="0.1.0",
    description="Olakai SDK",
    author="Olakai",
    author_email="support@olakai.com",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "requests",
        # add other dependencies here
    ],
    python_requires=">=3.7",
)
