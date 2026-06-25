cmake_minimum_required(VERSION 3.8)
project(sparky_description)

find_package(ament_cmake REQUIRED)

install(
  DIRECTORY config launch meshes rviz urdf
  DESTINATION share/${PROJECT_NAME}
)

# RViZ Velocity Marker Tool 
install(PROGRAMS
  scripts/velocity_marker.py
  DESTINATION lib/${PROJECT_NAME}
)

ament_package()