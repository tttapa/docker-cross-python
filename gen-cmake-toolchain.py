import sys
from platform_config import (
    PlatformConfig,
    arch_flags,
    cmake_system_name,
    cmake_system_processor,
    cpack_debian_architecture,
    multiarch_lib_dir,
)

toolchain_contents = """\
# For more information, see 
# https://cmake.org/cmake/help/latest/manual/cmake-toolchains.7.html,
# https://cmake.org/cmake/help/book/mastering-cmake/chapter/Cross%20Compiling%20With%20CMake.html, and
# https://tttapa.github.io/Pages/Raspberry-Pi/C++-Development-RPiOS/index.html.

include(CMakeDependentOption)

# System information
set(CMAKE_SYSTEM_NAME "{CMAKE_SYSTEM_NAME}")
set(CMAKE_SYSTEM_PROCESSOR "{CMAKE_SYSTEM_PROCESSOR}")
set(CROSS_GNU_TRIPLE "{CROSS_GNU_TRIPLE}"
    CACHE STRING "The GNU triple of the toolchain to use")
set(CMAKE_LIBRARY_ARCHITECTURE {CMAKE_LIBRARY_ARCHITECTURE})

# Compiler flags
set(CMAKE_C_FLAGS_INIT       "{ARCH_FLAGS}")
set(CMAKE_CXX_FLAGS_INIT     "{ARCH_FLAGS}")
set(CMAKE_Fortran_FLAGS_INIT "{ARCH_FLAGS}")

# Search path configuration
set(CMAKE_FIND_ROOT_PATH_MODE_PROGRAM NEVER)
set(CMAKE_FIND_ROOT_PATH_MODE_LIBRARY ONLY)
set(CMAKE_FIND_ROOT_PATH_MODE_INCLUDE ONLY)
set(CMAKE_FIND_ROOT_PATH_MODE_PACKAGE ONLY)

# Packaging
set(CPACK_DEBIAN_PACKAGE_ARCHITECTURE "{CPACK_DEBIAN_PACKAGE_ARCHITECTURE}")

# Toolchain and sysroot
set(TOOLCHAIN_DIR "/opt/x-tools/${{CROSS_GNU_TRIPLE}}")
set(CMAKE_SYSROOT "${{TOOLCHAIN_DIR}}/${{CROSS_GNU_TRIPLE}}/sysroot")

# Clang toolchain
option(TOOLCHAIN_USE_CLANG "Use Clang instead of GCC" Off)
cmake_dependent_option(TOOLCHAIN_USE_FLANG "Use LLVM Flang instead of GFortran"
    Off "TOOLCHAIN_USE_CLANG" Off)
if (TOOLCHAIN_USE_CLANG)
    # Select the GCC toolchain to use
    set(TOOLCHAIN_C_COMPILER ${{TOOLCHAIN_DIR}}/bin/${{CROSS_GNU_TRIPLE}}-gcc)

    # Find Clang
    set(TOOLCHAIN_CLANG_PREFIX "" CACHE STRING "Prefix to the Clang command")
    set(TOOLCHAIN_CLANG_SUFFIX "" CACHE STRING "Suffix to the Clang command")
    set(TOOLCHAIN_C_COMPILER_CLANG ${{TOOLCHAIN_CLANG_PREFIX}}clang${{TOOLCHAIN_CLANG_SUFFIX}}
        CACHE FILEPATH "Full name or path of the clang command")
    set(TOOLCHAIN_CXX_COMPILER_CLANG ${{TOOLCHAIN_CLANG_PREFIX}}clang++${{TOOLCHAIN_CLANG_SUFFIX}}
        CACHE FILEPATH "Full name or path of the clang++ command")
    if (TOOLCHAIN_USE_FLANG)
        set(TOOLCHAIN_Fortran_COMPILER_CLANG ${{TOOLCHAIN_CLANG_PREFIX}}flang-new${{TOOLCHAIN_CLANG_SUFFIX}}
            CACHE FILEPATH "Full name or path of the flang command")
    else()
        set(TOOLCHAIN_Fortran_COMPILER_CLANG "${{TOOLCHAIN_DIR}}/bin/${{CROSS_GNU_TRIPLE}}-gfortran"
            CACHE FILEPATH "Full name or path of the gfortran command")
    endif()
    # Use Clang as the cross-compiler
    set(CMAKE_C_COMPILER ${{TOOLCHAIN_C_COMPILER_CLANG}}
        CACHE FILEPATH "C compiler")
    set(CMAKE_CXX_COMPILER ${{TOOLCHAIN_CXX_COMPILER_CLANG}}
        CACHE FILEPATH "C++ compiler")
    set(CMAKE_Fortran_COMPILER ${{TOOLCHAIN_Fortran_COMPILER_CLANG}}
        CACHE FILEPATH "Fortran compiler")
    # Use Clang for linking Fortran code if GFortran is used as compiler
    if (NOT TOOLCHAIN_USE_FLANG)
        set(CMAKE_Fortran_CREATE_SHARED_LIBRARY "<CMAKE_C_COMPILER> <CMAKE_SHARED_LIBRARY_Fortran_FLAGS> <LANGUAGE_COMPILE_FLAGS> <LINK_FLAGS> <CMAKE_SHARED_LIBRARY_CREATE_Fortran_FLAGS> <SONAME_FLAG><TARGET_SONAME> -o <TARGET> <OBJECTS> <LINK_LIBRARIES>" CACHE STRING "")
        set(CMAKE_Fortran_LINK_EXECUTABLE "<CMAKE_C_COMPILER> <CMAKE_Fortran_LINK_FLAGS> <LINK_FLAGS> <FLAGS> <OBJECTS> -o <TARGET> <LINK_LIBRARIES>" CACHE STRING "")
        set(CMAKE_Fortran_CREATE_SHARED_MODULE ${{CMAKE_Fortran_CREATE_SHARED_LIBRARY}} CACHE STRING "")
        set(CMAKE_Fortran_STANDARD_LIBRARIES_INIT -lgfortran)
        set(CMAKE_Fortran_COMPILER_FORCED On)
    endif()

    # Get the machine triple from GCC
    execute_process(COMMAND ${{TOOLCHAIN_C_COMPILER}} -dumpmachine
                    OUTPUT_VARIABLE CROSS_GNU_TRIPLE_EFFECTIVE
                    ERROR_VARIABLE CROSS_GNU_TRIPLE_EFFECTIVE_ERROR
                    OUTPUT_STRIP_TRAILING_WHITESPACE)
    set(CROSS_GNU_TRIPLE_EFFECTIVE ${{CROSS_GNU_TRIPLE_EFFECTIVE}}
        CACHE STRING "The GNU triple of the toolchain actually in use")
    if (NOT CROSS_GNU_TRIPLE_EFFECTIVE)
        message(FATAL_ERROR "Unable to determine GCC triple ${{CROSS_GNU_TRIPLE_EFFECTIVE}} ${{CROSS_GNU_TRIPLE_EFFECTIVE_ERROR}}")
    endif()

    # Get the installation folder from GCC
    execute_process(COMMAND ${{TOOLCHAIN_C_COMPILER}} -print-search-dirs
                    OUTPUT_VARIABLE TOOLCHAIN_GCC_INSTALL
                    ERROR_VARIABLE TOOLCHAIN_GCC_INSTALL_ERROR)
    string(REGEX MATCH "(^|\\r|\\n)install: +([^\\r\\n]*)" 
        TOOLCHAIN_GCC_INSTALL_LINE ${{TOOLCHAIN_GCC_INSTALL}})
    if (NOT TOOLCHAIN_GCC_INSTALL_LINE)
        message(FATAL_ERROR "Unable to determine GCC installation ${{TOOLCHAIN_GCC_INSTALL}} ${{TOOLCHAIN_GCC_INSTALL_ERROR}}")
    endif()
    cmake_path(SET TOOLCHAIN_GCC_INSTALL_LIB NORMALIZE ${{CMAKE_MATCH_2}})
    cmake_path(SET TOOLCHAIN_GCC_INSTALL NORMALIZE ${{CMAKE_MATCH_2}})
    cmake_path(APPEND TOOLCHAIN_GCC_INSTALL "../../../..")
    cmake_path(ABSOLUTE_PATH TOOLCHAIN_GCC_INSTALL)
    set(TOOLCHAIN_GCC_INSTALL ${{TOOLCHAIN_GCC_INSTALL}}
        CACHE PATH "Path to GCC installation")
    message(STATUS "Using Clang toolchain with GCC installation ${{TOOLCHAIN_GCC_INSTALL}}")

    # Find a linker
    find_program(TOOLCHAIN_LINKER ${{CROSS_GNU_TRIPLE}}-ld REQUIRED
        HINTS ${{TOOLCHAIN_DIR}}/bin)

    # Specify architecture-specific flags
    set(ARCH_FLAGS "-target ${{CROSS_GNU_TRIPLE_EFFECTIVE}}")
    # Make sure that Clang finds the GCC installation and a suitable linker
    set(TOOLCHAIN_FLAGS "--gcc-toolchain=${{TOOLCHAIN_GCC_INSTALL}}")
    set(TOOLCHAIN_LINK_FLAGS "-L${{TOOLCHAIN_GCC_INSTALL_LIB}} -fuse-ld=${{TOOLCHAIN_LINKER}}")
    # Runtime libraries for Flang
    if (TOOLCHAIN_USE_FLANG)
        set(FLANG_LIB_DIR "/opt/${{CROSS_GNU_TRIPLE}}/flang/usr/local/lib")
        string(APPEND TOOLCHAIN_LINK_FLAGS " -L${{FLANG_LIB_DIR}}")
    endif()
    # Compilation flags
    string(APPEND CMAKE_C_FLAGS_INIT " ${{ARCH_FLAGS}} ${{TOOLCHAIN_FLAGS}}")
    string(APPEND CMAKE_CXX_FLAGS_INIT " ${{ARCH_FLAGS}} ${{TOOLCHAIN_FLAGS}}")
    if (TOOLCHAIN_USE_FLANG)
        string(APPEND CMAKE_Fortran_FLAGS_INIT " ${{ARCH_FLAGS}} ${{TOOLCHAIN_FLAGS}}")
        string(APPEND CMAKE_Fortran_FLAGS_INIT " --sysroot=${{CMAKE_SYSROOT}}")
    endif()
    # Linker flags
    string(APPEND CMAKE_EXE_LINKER_FLAGS_INIT " ${{TOOLCHAIN_LINK_FLAGS}}")
    string(APPEND CMAKE_MODULE_LINKER_FLAGS_INIT " ${{TOOLCHAIN_LINK_FLAGS}}")
    string(APPEND CMAKE_SHARED_LINKER_FLAGS_INIT " ${{TOOLCHAIN_LINK_FLAGS}}")
# GCC toolchain
else()
    set(CMAKE_C_COMPILER "${{TOOLCHAIN_DIR}}/bin/${{CROSS_GNU_TRIPLE}}-gcc"
        CACHE FILEPATH "C compiler")
    set(CMAKE_CXX_COMPILER "${{TOOLCHAIN_DIR}}/bin/${{CROSS_GNU_TRIPLE}}-g++"
        CACHE FILEPATH "C++ compiler")
    set(CMAKE_Fortran_COMPILER "${{TOOLCHAIN_DIR}}/bin/${{CROSS_GNU_TRIPLE}}-gfortran"
        CACHE FILEPATH "Fortran compiler")
endif()

# Locating Python
find_package(Python3 REQUIRED COMPONENTS Interpreter)
set(Python3_VERSION_MAJ_MIN "${{Python3_VERSION_MAJOR}}.${{Python3_VERSION_MINOR}}")
if (Python3_INTERPRETER_ID MATCHES "PyPy")
    set(Python3_PyPy_LIB_VERSION "${{Python3_VERSION_MAJ_MIN}}")
    if (Python3_VERSION_MAJ_MIN VERSION_LESS "3.9")
        set(Python3_PyPy_LIB_VERSION "${{Python3_VERSION_MAJOR}}")
    endif()
    set(PYTHON_STAGING_DIR "/opt/${{CROSS_GNU_TRIPLE}}/pypy${{Python3_VERSION_MAJ_MIN}}")
    set(Python3_LIBRARY "${{PYTHON_STAGING_DIR}}/bin/libpypy${{Python3_PyPy_LIB_VERSION}}-c.so")
    set(Python3_INCLUDE_DIR "${{PYTHON_STAGING_DIR}}/include/pypy${{Python3_VERSION_MAJ_MIN}}")
    string(REGEX MATCH "([0-9]+)\\.([0-9]+).*" _ ${{Python3_PyPy_VERSION}})
    set(PY_BUILD_EXT_SUFFIX ".pypy${{Python3_VERSION_MAJOR}}${{Python3_VERSION_MINOR}}-pp${{CMAKE_MATCH_1}}${{CMAKE_MATCH_2}}-${{CMAKE_SYSTEM_PROCESSOR}}-linux-gnu.so")
else()
    execute_process(COMMAND ${{Python3_EXECUTABLE}}
                        -c "import sys; print(sys.abiflags)"
                    OUTPUT_VARIABLE Python3_VERSION_ABI
                    OUTPUT_STRIP_TRAILING_WHITESPACE)
    set(Python3_VERSION_MAJ_MIN_ABI "${{Python3_VERSION_MAJ_MIN}}${{Python3_VERSION_ABI}}")
    set(PYTHON_STAGING_DIR "/opt/${{CROSS_GNU_TRIPLE}}/python${{Python3_VERSION_MAJ_MIN}}")
    set(Python3_LIBRARY "${{PYTHON_STAGING_DIR}}/usr/local/lib/libpython${{Python3_VERSION_MAJ_MIN_ABI}}.so")
    set(Python3_INCLUDE_DIR "${{PYTHON_STAGING_DIR}}/usr/local/include/python${{Python3_VERSION_MAJ_MIN_ABI}}")
endif()
list(APPEND CMAKE_FIND_ROOT_PATH "${{PYTHON_STAGING_DIR}}")
# For FindPython compatibility
set(Python_LIBRARY "${{Python3_LIBRARY}}")
set(Python_INCLUDE_DIR "${{Python3_INCLUDE_DIR}}")
"""


def get_cmake_toolchain_file(cfg: PlatformConfig):
    subs = {
        "CMAKE_SYSTEM_PROCESSOR": cmake_system_processor(cfg),
        "CMAKE_SYSTEM_NAME": cmake_system_name(cfg),
        "CROSS_GNU_TRIPLE": str(cfg),
        "CMAKE_LIBRARY_ARCHITECTURE": multiarch_lib_dir(cfg),
        "ARCH_FLAGS": arch_flags(cfg),
        "CPACK_DEBIAN_PACKAGE_ARCHITECTURE": cpack_debian_architecture(cfg),
    }
    return toolchain_contents.format(**subs)


if __name__ == "__main__":
    triple = sys.argv[1]
    outfile = sys.argv[2]
    cfg = PlatformConfig.from_string(triple)
    with open(outfile, "w") as f:
        f.write(get_cmake_toolchain_file(cfg))
