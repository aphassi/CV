cmake_minimum_required(VERSION 3.20)
project(image_processor)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

# Главный бинарник
add_executable(
    image_processor
    image_processor.cpp
    src/bmp_encoder.cpp
    src/args.cpp
    src/filter.cpp
    src/crop.cpp
    src/grayscale.cpp
    src/negative.cpp
    src/sharpen.cpp
    src/edge.cpp
    src/blur.cpp
    src/false.cpp
    src/processor.cpp
)

target_include_directories(image_processor PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}
    ${CMAKE_CURRENT_SOURCE_DIR}/src
    ${CMAKE_CURRENT_SOURCE_DIR}/src/utility
)
