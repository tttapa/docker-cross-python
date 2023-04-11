import sys
from platform_config import (
    PlatformConfig,
    conan_arch,
)

cross_config_contents = """\
[settings]
arch={arch}
build_type=Release
compiler=gcc
compiler.cppstd=gnu17
compiler.libcxx=libstdc++11
compiler.version=12
os=Linux

[conf]
tools.cmake.cmaketoolchain:user_toolchain=["/opt/{triple}/cmake/{triple}.toolchain.cmake"]
"""


def get_py_build_cmake_cross_config(cfg: PlatformConfig):
    subs = {
        "arch": conan_arch(cfg),
        "triple": str(cfg),
    }
    return cross_config_contents.format(**subs)


if __name__ == "__main__":
    triple = sys.argv[1]
    outfile = sys.argv[2]
    cfg = PlatformConfig.from_string(triple)
    with open(outfile, "w") as f:
        f.write(get_py_build_cmake_cross_config(cfg))
