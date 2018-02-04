cmake_minimum_required(VERSION 3.2 FATAL_ERROR)
include(ExternalProject)

project(Boost-Pretty-Printer LANGUAGES CXX)

# Parameters passed to cmake via -D:
# boost_major, boost_minor, boost_patchlevel - boost version
# gdb - custom gdb path

if (NOT DEFINED gdb)
    set(gdb gdb)
endif(NOT DEFINED gdb)
set(python_testuite "${CMAKE_SOURCE_DIR}/tests/testsuite.py")
set(python_interactive_source "${CMAKE_SOURCE_DIR}/tests/interactive.gdb")
set(python_interactive_target "${CMAKE_BINARY_DIR}/interactive.gdb")

# Download boost library sources
if (NOT DEFINED boost_major)
    message(FATAL_ERROR "You must set boost_major environment variable")
endif()
if (NOT DEFINED boost_minor)
    message(FATAL_ERROR "You must set boost_minor environment variable")
endif()
if (NOT DEFINED boost_patchlevel)
    set(boost_patchlevel 0)
endif()
set(boost_url "http://sourceforge.net/projects/boost/files/boost/${boost_major}.${boost_minor}.${boost_patchlevel}/boost_${boost_major}_${boost_minor}_${boost_patchlevel}.tar.bz2/download")
set(boost_prefix "${CMAKE_BINARY_DIR}/boost-${boost_major}.${boost_minor}.${boost_patchlevel}")
ExternalProject_Add(boost
  URL ${boost_url}
  PREFIX ${boost_prefix}
  CONFIGURE_COMMAND ""
  BUILD_COMMAND ""
  INSTALL_COMMAND "")
ExternalProject_Get_Property(boost SOURCE_DIR)
include_directories(BEFORE SYSTEM "${SOURCE_DIR}")

# Build C++ testsuite part
add_compile_options(
        -std=c++11 -O0 -g3 -ggdb -fno-eliminate-unused-debug-types -Wall -Wextra -Wno-unused-label
        -Wno-unused-variable -Wno-unused-but-set-variable -pedantic)
add_definitions(-DBOOST_INTRUSIVE_VARIADIC_TEMPLATES)
add_executable(bin tests/testsuite.cpp)
add_dependencies(bin boost)

add_custom_target(check
        ${CMAKE_COMMAND} -E env "PYTHONPATH=$ENV{PYTHONPATH}:${CMAKE_SOURCE_DIR}"
            "${gdb}" --nx --batch -x "${python_testuite}" "$<TARGET_FILE:bin>"
        WORKING_DIRECTORY "${CMAKE_SOURCE_DIR}"
        DEPENDS ${python_testuite})
add_dependencies(check bin)

add_custom_target(interactive
        ${CMAKE_COMMAND} -E env "PYTHONPATH=$ENV{PYTHONPATH}:${CMAKE_SOURCE_DIR}"
        "${gdb}" -x "${python_interactive_target}" --nx "$<TARGET_FILE:bin>" 
        DEPENDS ${python_testuite}
        USES_TERMINAL)
add_dependencies(check bin boost)
configure_file("${python_interactive_source}" "${python_interactive_target}")
