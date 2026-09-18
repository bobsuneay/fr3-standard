"""Thin wrapper around MoveIt and ros2_control interfaces used by grasp_node.

The old project embeds this logic in ``ros_io.py``. Keep it here so the
state machine can remain simulator-agnostic.
"""


class DualArmMoveIt:
    def __init__(self, node):
        self.node = node
        # TODO: Create action clients:
        #   - /move_action
        #   - /execute_trajectory
        #   - /left_arm_controller/follow_joint_trajectory
        #   - /right_arm_controller/follow_joint_trajectory
        #   - /left_gripper_controller/gripper_action
        #   - /right_gripper_controller/gripper_action

    def move_to_joints(self, side, joints):
        raise NotImplementedError('Port MoveGroup goal construction from ros_io.py')

    def move_to_pose(self, side, pose):
        raise NotImplementedError('Port pose planning and execution from ros_io.py')

    def open_gripper(self, side, width):
        raise NotImplementedError('Port gripper action call')

    def close_gripper(self, side, width):
        raise NotImplementedError('Port gripper action call')

    def tcp_pose(self, side):
        raise NotImplementedError('Use /compute_fk with the measured joint state')

    def cancel(self):
        raise NotImplementedError('Cancel active MoveIt/controller goals')
