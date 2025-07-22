from setuptools import setup, find_packages

setup(
    name="olakaisdk",
    version="0.1.0",
    description="Olakai SDK for enable monitoring across apps, tools and AI agents",
    author="Olakai",
    author_email="support@olakai.ai",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "requests",
        # add other dependencies here
    ],
    python_requires=">=3.7",
)
