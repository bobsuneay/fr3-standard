cmake_minimum_required(VERSION 3.8)
project(fr3_direct_gripper)

find_package(ament_cmake REQUIRED)

set(FAIRINO_VENDOR_ROOT "${CMAKE_CURRENT_SOURCE_DIR}/../../third_party/frcobot_ros2-v3.0.0_robotV3.9.7"
    CACHE PATH "Fairino vendor package root")
set(FAIRINO_LIB "${FAIRINO_VENDOR_ROOT}/fairino_hardware_v3_9_7/libfairino/lib/libfairino.so.2.3.7")
if(NOT EXISTS "${FAIRINO_LIB}")
  message(FATAL_ERROR "Fairino SDK not found: ${FAIRINO_LIB}")
endif()

add_executable(fairino_gripper_cli src/fairino_gripper_cli.cpp)
target_compile_features(fairino_gripper_cli PRIVATE cxx_std_17)
target_include_directories(fairino_gripper_cli PRIVATE
  "${FAIRINO_VENDOR_ROOT}/fairino_hardware_v3_9_7")
target_link_libraries(fairino_gripper_cli PRIVATE "${FAIRINO_LIB}")
set_target_properties(fairino_gripper_cli PROPERTIES
  BUILD_RPATH "${FAIRINO_VENDOR_ROOT}/fairino_hardware_v3_9_7/libfairino/lib")

install(TARGETS fairino_gripper_cli DESTINATION lib/${PROJECT_NAME})
ament_package()
