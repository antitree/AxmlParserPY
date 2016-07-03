from setuptools import setup, find_packages

version = "0.0.2"

setup(name="axmlparserpy",
      version=version,
      author="Bryan Bishop",
      author_email="kanzure@gmail.com",
      license="GPL",
      description="Androguard-related tools for reverse engineering Android binary xml files (and others).",
      packages=find_packages())
