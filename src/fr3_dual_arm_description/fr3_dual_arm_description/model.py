"""Small description helpers that keep the larger assembly logic out of launch files."""

from pathlib import Path

import yaml


SIDES = ('left', 'right')


def load_yaml(path):
    return yaml.safe_load(Path(path).read_text(encoding='utf-8'))


def arm_joints(side):
    return [f'{side}_j{i}' for i in range(1, 7)]


def gripper_joints(side):
    return [f'{side}_left_finger_joint', f'{side}_right_finger_joint']


def all_joints():
    joints = []
    for side in SIDES:
        joints.extend(arm_joints(side))
        joints.extend(gripper_joints(side))
    return joints
