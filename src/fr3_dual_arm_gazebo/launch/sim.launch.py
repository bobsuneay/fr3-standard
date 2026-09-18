from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument('world', default_value=''),
        DeclareLaunchArgument('gui', default_value='true'),
        DeclareLaunchArgument('pause', default_value='false'),
        # TODO: Include gazebo_ros gazebo.launch.py and spawn the robot after
        # fr3_dual_arm_description exposes the complete dual-arm robot_description.
    ])
