import setuptools
import platform

# Dấu __ đánh dấu biến này k nên đc gọi ở đâu khác
with open("requirement.txt") as file:
    # List các package cần có từ file requirement
    ## filter(None) để loại bỏ các giá trị bị null, rỗng
    __requires = list(filter(None, file.read().splitlines()))

if platform.python_implementation() == "PyPy"