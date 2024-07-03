import setuptools
import platform

# Dấu __ đánh dấu biến này k nên đc gọi ở đâu khác
with open("requirement.txt") as file:
    # List các package cần có từ file requirement
    ## filter(None) để loại bỏ các giá trị bị null, rỗng
    __requires = list(filter(None, file.read().splitlines()))

# Check loại implemetation của Python trên máy đó
if platform.python_implementation() == "PyPy":
    # Nếu implementation là PyPy, cần dùng các package của Gevent dành riêng cho PyPy
    __requires.append("git+git://github.com/schmir/gevent@pypy-hacks")
    __requires.append("git+git://github.com/gevent-on-pypy/pypycore ")
else:
    # Bản Gevent general với các loại Python khác
    __requires.append("gevent>=1")

setuptools.setup(
    name="aj",
    version="2.2.10",
    python_requires=">=3",
    install_requires=__requires,
    description="Web UI base toolkit",
    author="Eugene Pankov",
    author_email="e@ajenti.org",
    url="https://ajenti.org/",
    packages=setuptools.find_packages(),
    include_package_data=True,
    package_data={
        "aj": [
            "aj/static/images/*",
        ],
    },
)
