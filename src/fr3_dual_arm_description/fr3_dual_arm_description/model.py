"""Build the dual-arm FR3 model and controller/MoveIt parameters.

This is intentionally a small, self-contained replacement for the old
``fr3_dual_bolt_cell.model``.  The mechanical URDF is assembled once from
YAML + the vendor single-arm URDF; Gazebo and MoveIt are still launched
separately in the gazebo/bringup packages.
"""

from copy import deepcopy
from pathlib import Path
import math
import xml.etree.ElementTree as ET

import yaml


SIDES = ('left', 'right')
PACKAGE = 'fr3_dual_arm_description'


def read_yaml(path):
    return yaml.safe_load(Path(path).read_text(encoding='utf-8'))


def vector(value, count, label):
    if (not isinstance(value, list) or len(value) != count or
            any(type(v) not in (float, int) or not math.isfinite(v) for v in value)):
        raise ValueError(f'{label} must contain {count} finite numbers')


def validate_arms(cfg):
    for side in SIDES:
        for key, length in (('xyz', 3), ('rpy', 3), ('initial', 6)):
            vector(cfg[side][key], length, f'{side}.{key}')
    g = cfg['gripper']
    for key in ('flange_xyz', 'flange_rpy', 'tcp_xyz', 'tcp_rpy'):
        vector(g[key], 3, key)
    if not (0 < g['open_gap'] / 2 <= g['finger_travel'] <= 0.05):
        raise ValueError('Require 0 < open_gap/2 <= finger_travel <= 0.05 m')
    if cfg['left']['xyz'] == cfg['right']['xyz']:
        raise ValueError('Both bases cannot occupy the same position')
    return cfg


def element(parent, tag, **attributes):
    return ET.SubElement(parent, tag, {k: str(v) for k, v in attributes.items()})


def numbers(values):
    return ' '.join(map(str, values))


def fixed(root, name, parent, child, xyz=(0, 0, 0), rpy=(0, 0, 0)):
    joint = element(root, 'joint', name=name, type='fixed')
    element(joint, 'parent', link=parent)
    element(joint, 'child', link=child)
    element(joint, 'origin', xyz=numbers(xyz), rpy=numbers(rpy))


def inertial(link, mass, size, xyz=(0, 0, 0)):
    block = element(link, 'inertial')
    element(block, 'origin', xyz=numbers(xyz))
    element(block, 'mass', value=mass)
    a, b, c = size
    element(block, 'inertia', ixx=mass * (b * b + c * c) / 12,
            iyy=mass * (a * a + c * c) / 12,
            izz=mass * (a * a + b * b) / 12,
            ixy=0, ixz=0, iyz=0)


def box(link, size, xyz=(0, 0, 0), visual=False):
    block = element(link, 'visual' if visual else 'collision')
    element(block, 'origin', xyz=numbers(xyz))
    element(element(block, 'geometry'), 'box', size=numbers(size))
    if visual:
        material = element(block, 'material', name=link.get('name') + '_metal')
        element(material, 'color', rgba='0.35 0.38 0.40 1')


def mesh(link, name, xyz=(0, 0, 0), yaw=0):
    block = element(link, 'visual')
    element(block, 'origin', xyz=numbers(xyz), rpy=f'0 0 {yaw}')
    element(element(block, 'geometry'), 'mesh',
            filename=f'package://{PACKAGE}/meshes/hkv_tg9801/{name}.stl',
            scale='.001 .001 .001')
    material = element(block, 'material', name=link.get('name') + '_' + name + '_material')
    color = '0.1882 0.1882 0.1882 1' if name in ('base_body', 'finger') else '0.68 0.70 0.72 1'
    element(material, 'color', rgba=color)


def add_gripper(root, side, cfg):
    p = side + '_'
    g = cfg['gripper']
    element(root, 'link', name=p + 'tool0')
    fixed(root, p + 'wrist_to_tool', p + 'wrist3_link', p + 'tool0',
          g['flange_xyz'], g['flange_rpy'])
    palm = element(root, 'link', name=p + 'gripper_palm')
    inertial(palm, 0.65, (0.06, 0.16, 0.09), (0, 0, 0.04))
    mesh(palm, 'flange')
    mesh(palm, 'base_body', (0, 0, 0.0615))
    mesh(palm, 'rail_155', (0, 0, 0.067))
    box(palm, (0.16, 0.0705, 0.0615), (0, 0.00325, 0.03075))
    box(palm, (0.155, 0.007, 0.0048), (0, 0, 0.0694))
    fixed(root, p + 'tool_to_gripper', p + 'tool0', p + 'gripper_palm')

    for index, sign in enumerate((-1, 1)):
        finger = 'left' if index == 0 else 'right'
        link_name = p + finger + '_finger'
        joint_name = p + finger + '_finger_joint'
        link = element(root, 'link', name=link_name)
        inertial(link, 0.08, (0.008, 0.018, 0.07), (0, 0, 0.04))
        mesh(link, 'slider')
        mesh(link, 'finger', (0, 0, 0.008), 0 if index == 0 else math.pi)
        box(link, (0.024, 0.017, 0.0065), (0, 0, 0.00485))
        box(link, (0.0285, 0.040, 0.0717), (0, 0, 0.04385), visual=False)
        joint = element(root, 'joint', name=joint_name, type='prismatic')
        element(joint, 'parent', link=p + 'gripper_palm')
        element(joint, 'child', link=link_name)
        element(joint, 'origin', xyz=f'{sign * 0.01545} 0 .067')
        element(joint, 'axis', xyz=f'{sign} 0 0')
        element(joint, 'limit', lower=0, upper=0.05, effort=100, velocity=0.10)
        element(joint, 'dynamics', damping=2.0, friction=0.10)
        surface = element(root, 'gazebo', reference=link_name)
        element(surface, 'selfCollide').text = 'true'
        for tag, value in (('mu1', 1), ('mu2', 1), ('kp', 100000), ('kd', 10)):
            element(surface, tag).text = str(value)

    element(root, 'link', name=p + 'gripper_tcp')
    fixed(root, p + 'palm_to_tcp', p + 'gripper_palm', p + 'gripper_tcp',
          g['tcp_xyz'], g['tcp_rpy'])


def control(root, name, plugin, joints, initial=None, parameters=None):
    system = element(root, 'ros2_control', name=name, type='system')
    hardware = element(system, 'hardware')
    element(hardware, 'plugin').text = plugin
    for key, value in (parameters or {}).items():
        element(hardware, 'param', name=key).text = str(value)
    for joint_name in joints:
        joint = element(system, 'joint', name=joint_name)
        element(joint, 'command_interface', name='position')
        state = element(joint, 'state_interface', name='position')
        if 'finger_joint' in joint_name:
            element(joint, 'state_interface', name='velocity')
        if initial is not None:
            element(state, 'param', name='initial_value').text = str(initial.get(joint_name, 0))
    return system


def common_model(scene_path):
    scene = read_yaml(scene_path)
    root = ET.Element('robot', name='fr3_dual_arm')
    element(root, 'link', name='world')

    support = scene['support']
    foot = scene['support']
    for name, size, mass, color, z in (
        ('support_link', support['size'], 15, '0.60 0.65 0.70 1', support['size'][2] / 2),
        ('support_foot', support['foot_size'], 8, '0.25 0.28 0.30 1', support['foot_size'][2] / 2),
    ):
        link = element(root, 'link', name=name)
        inertial(link, mass, size, (0, 0, z if name == 'support_link' else 0))
        box(link, size, (0, 0, z if name == 'support_link' else 0), visual=True)
        box(link, size, (0, 0, z if name == 'support_link' else 0))

    fixed(root, 'world_to_support', 'world', 'support_link')
    fixed(root, 'support_to_foot', 'support_link', 'support_foot',
          (0, 0, support['foot_size'][2] / 2))

    camera = scene['camera']
    head = element(root, 'link', name='head_camera_link')
    inertial(head, 0.2, (0.045, 0.13, 0.045))
    box(head, (0.045, 0.13, 0.045), visual=True)
    box(head, (0.045, 0.13, 0.045))
    fixed(root, 'support_to_head_camera', 'support_link', 'head_camera_link',
          camera['xyz'], camera['rpy'])
    element(root, 'link', name='head_camera_optical_frame')
    fixed(root, 'head_camera_optical_joint', 'head_camera_link',
          'head_camera_optical_frame', rpy=(-math.pi / 2, 0, -math.pi / 2))
    cam = element(root, 'gazebo', reference='head_camera_link')
    element(cam, 'material').text = 'Gazebo/Black'
    sensor = element(cam, 'sensor', name='head_rgbd_sensor', type='depth')
    element(sensor, 'always_on').text = 'true'
    element(sensor, 'update_rate').text = str(camera['rate'])
    element(sensor, 'camera', name='head_rgbd')
    camera_el = sensor.find('camera')
    element(camera_el, 'horizontal_fov').text = str(camera['horizontal_fov'])
    image = element(camera_el, 'image')
    element(image, 'width').text = str(camera['width'])
    element(image, 'height').text = str(camera['height'])
    element(image, 'format').text = 'R8G8B8'
    clip = element(camera_el, 'clip')
    element(clip, 'near').text = str(camera['near'])
    element(clip, 'far').text = str(camera['far'])
    plugin = element(sensor, 'plugin', name='head_camera_ros', filename='libgazebo_ros_camera.so')
    ros = element(plugin, 'ros')
    element(ros, 'namespace').text = '/'
    element(plugin, 'camera_name').text = 'head_camera'
    element(plugin, 'frame_name').text = 'head_camera_optical_frame'
    element(plugin, 'min_depth').text = str(camera['near'])
    element(plugin, 'max_depth').text = str(camera['far'])

    return root, scene


def build_model(share, scene_path, arms, controller_file=''):
    share = Path(share)
    arms = validate_arms(arms)
    root, scene = common_model(scene_path)
    vendor = ET.parse(share / 'urdf' / 'fr3_arm.urdf').getroot()
    initial = {}
    all_joints = []

    for side in SIDES:
        p = side + '_'
        plate = element(root, 'link', name=p + 'mount_plate')
        inertial(plate, 0.5, (0.15, 0.15, 0.02))
        box(plate, (0.15, 0.15, 0.02), (0, 0, -0.01))
        box(plate, (0.15, 0.15, 0.02), (0, 0, -0.01), visual=True)
        fixed(root, p + 'plate_mount', 'support_link', p + 'mount_plate',
              arms[side]['xyz'], arms[side]['rpy'])

        for original in vendor:
            node = deepcopy(original)
            for part in node.iter():
                for key in ('name', 'link', 'joint', 'reference'):
                    if key in part.attrib:
                        part.set(key, p + part.get(key))
            root.append(node)

        fixed(root, p + 'base_mount', 'support_link', p + 'base_link',
              arms[side]['xyz'], arms[side]['rpy'])
        add_gripper(root, side, arms)
        for joint_name in (p + 'wrist_to_tool', p + 'tool_to_gripper', p + 'palm_to_tcp'):
            gazebo = element(root, 'gazebo', reference=joint_name)
            element(gazebo, 'preserveFixedJoint').text = 'true'

        for link in vendor.findall('link'):
            surface = element(root, 'gazebo', reference=p + link.get('name'))
            element(surface, 'selfCollide').text = 'true'
            element(surface, 'material').text = 'Gazebo/White'

        joints = [f'{side}_j{i}' for i in range(1, 7)]
        joints += [f'{side}_left_finger_joint', f'{side}_right_finger_joint']
        all_joints.extend(joints)
        for i, value in enumerate(arms[side]['initial'], 1):
            initial[f'{side}_j{i}'] = value

    # A single GazeboSystem exposes both arms and avoids duplicate ros2_control
    # parameters that Humble complains about when using two system blocks.
    control(root, 'gazebo_system', 'gazebo_ros2_control/GazeboSystem',
            all_joints, initial)
    plugin = element(element(root, 'gazebo'), 'plugin', name='gazebo_ros2_control',
                     filename='libgazebo_ros2_control.so')
    element(plugin, 'robot_param').text = 'robot_description'
    element(plugin, 'robot_param_node').text = 'robot_state_publisher'
    element(plugin, 'parameters').text = str(controller_file)
    return root


def semantic(root, arms):
    srdf = ET.Element('robot', name=root.get('name'))
    for side in SIDES:
        group = element(srdf, 'group', name=side + '_arm')
        element(group, 'chain', base_link=side + '_base_link', tip_link=side + '_gripper_tcp')
        group = element(srdf, 'group', name=side + '_gripper')
        element(group, 'joint', name=side + '_left_finger_joint')
        element(group, 'joint', name=side + '_right_finger_joint')
        element(srdf, 'end_effector', name=side + '_hkv',
                parent_link=side + '_gripper_palm', group=side + '_gripper',
                parent_group=side + '_arm')
        ready = element(srdf, 'group_state', name='ready', group=side + '_arm')
        for i, v in enumerate(arms[side]['initial'], 1):
            element(ready, 'joint', name=f'{side}_j{i}', value=v)
        for name, q in (('closed', 0.00025), ('open', arms['gripper']['open_gap'] / 2)):
            state = element(srdf, 'group_state', name=name, group=side + '_gripper')
            element(state, 'joint', name=side + '_left_finger_joint', value=q)
            element(state, 'joint', name=side + '_right_finger_joint', value=q)
        element(srdf, 'disable_collisions', link1=side + '_wrist3_link',
                link2=side + '_gripper_palm', reason='Mounting')
        element(srdf, 'disable_collisions', link1=side + '_mount_plate',
                link2=side + '_base_link', reason='Mounting')
    both = element(srdf, 'group', name='both_arms')
    for side in SIDES:
        element(both, 'group', name=side + '_arm')
    for joint in root.findall('joint'):
        element(srdf, 'disable_collisions', link1=joint.find('parent').get('link'),
                link2=joint.find('child').get('link'), reason='Adjacent')
    return ET.tostring(srdf, encoding='unicode')


def controllers():
    result = {'controller_manager': {'ros__parameters': {'update_rate': 100, 'use_sim_time': True}}}
    for side in SIDES:
        names = (side + '_joint_state_broadcaster', side + '_arm_controller',
                 side + '_gripper_controller')
        for name, kind in zip(names, (
                'joint_state_broadcaster/JointStateBroadcaster',
                'joint_trajectory_controller/JointTrajectoryController',
                'joint_trajectory_controller/JointTrajectoryController')):
            result['controller_manager']['ros__parameters'][name] = {'type': kind}
        result[names[0]] = {'ros__parameters': {
            'joints': [f'{side}_j{i}' for i in range(1, 7)] +
                      [f'{side}_left_finger_joint', f'{side}_right_finger_joint'],
            'interfaces': ['position'], 'use_local_topics': False}}
        result[names[1]] = {'ros__parameters': {
            'joints': [f'{side}_j{i}' for i in range(1, 7)],
            'command_interfaces': ['position'], 'state_interfaces': ['position'],
            'allow_partial_joints_goal': False, 'state_publish_rate': 50.0,
            'constraints': {'goal_time': 2.0, 'stopped_velocity_tolerance': 0.05}}}
        result[names[2]] = {'ros__parameters': {
            'joints': [f'{side}_left_finger_joint', f'{side}_right_finger_joint'],
            'command_interfaces': ['position'], 'state_interfaces': ['position', 'velocity'],
            'allow_partial_joints_goal': False}}
    return result


def moveit_config(root, arms):
    mapping = {'controller_names': []}
    kinematics = {}
    ompl = {}
    for group in ('left_arm', 'right_arm', 'both_arms', 'left_gripper', 'right_gripper'):
        ompl[group] = {'planner_configs': ['RRTConnectkConfigDefault'],
                       'longest_valid_segment_fraction': 0.005}
    for side in SIDES:
        kinematics[side + '_arm'] = {
            'kinematics_solver': 'kdl_kinematics_plugin/KDLKinematicsPlugin',
            'kinematics_solver_timeout': 0.1,
            'kinematics_solver_search_resolution': 0.005}
        for suffix, kind, action, joints in (
                ('arm_controller', 'FollowJointTrajectory', 'follow_joint_trajectory',
                 [f'{side}_j{i}' for i in range(1, 7)]),
                ('gripper_controller', 'FollowJointTrajectory', 'follow_joint_trajectory',
                 [f'{side}_left_finger_joint', f'{side}_right_finger_joint'])):
            name = side + '_' + suffix
            mapping['controller_names'].append(name)
            mapping[name] = {'type': kind, 'action_ns': action, 'default': True, 'joints': joints}
    limits = {}
    for joint in root.findall('joint'):
        if joint.get('type') in ('revolute', 'prismatic') and joint.find('mimic') is None:
            velocity = min(float(joint.find('limit').get('velocity')), 0.3)
            limits[joint.get('name')] = {
                'has_velocity_limits': True, 'max_velocity': velocity,
                'has_acceleration_limits': True, 'max_acceleration': 0.3}
    return {
        'robot_description_semantic': semantic(root, arms),
        'robot_description_kinematics': kinematics,
        'robot_description_planning': {
            'joint_limits': limits,
            'default_velocity_scaling_factor': 0.1,
            'default_acceleration_scaling_factor': 0.1},
        'planning_pipelines': ['ompl'],
        'default_planning_pipeline': 'ompl',
        'ompl': ompl,
        'moveit_controller_manager': 'moveit_simple_controller_manager/MoveItSimpleControllerManager',
        'moveit_simple_controller_manager': mapping,
    }
