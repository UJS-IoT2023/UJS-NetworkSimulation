# CMakeLists.txt for experiment 3 - TCP vs UDP comparison
# This allows multiple files with main functions in the same directory

# Build lab3_task1
build_exec(
    EXECNAME lab3_task1
    EXECNAME_PREFIX scratch_exp3_
    SOURCE_FILES "lab3_task1.cc"
    LIBRARIES_TO_LINK "${ns3-libs}" "${ns3-contrib-libs}"
    EXECUTABLE_DIRECTORY_PATH ${CMAKE_CURRENT_BINARY_DIR}/
)

# Build lab3_tcp_udp_comparison
build_exec(
    EXECNAME lab3_tcp_udp_comparison
    EXECNAME_PREFIX scratch_exp3_
    SOURCE_FILES "lab3_tcp_udp_comparison.cc"
    LIBRARIES_TO_LINK "${ns3-libs}" "${ns3-contrib-libs}"
    EXECUTABLE_DIRECTORY_PATH ${CMAKE_CURRENT_BINARY_DIR}/
)
