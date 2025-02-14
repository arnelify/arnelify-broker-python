from setuptools import setup, find_packages, Extension

ffi = Extension(
  'arnelify-broker-ffi',
  sources=['arnelify_broker/cpp/ffi.cpp'],
  language='c++',
  extra_compile_args=['-std=c++2b', '-w'],
  include_dirs=['arnelify_broker/cpp/include', '/usr/include', '/usr/include/jsoncpp/json'],
  extra_link_args=['-ljsoncpp', '-lz']
)

setup(
    name="arnelify-broker",
    version="0.7.1",
    author="Arnelify",
    description="Minimalistic dynamic library which is a message broker written in C and C++.",
    url='https://github.com/arnelify/arnelify-broker-python',
    keywords="arnelify arnelify-broker-python arnelify-broker",
    packages=find_packages(),
    license="MIT",
    install_requires=["cffi", "setuptools", "wheel"],
    long_description=open("README.md", "r", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
    ],
    ext_modules=[ffi],
)