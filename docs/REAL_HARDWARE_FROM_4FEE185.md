# 从 4fee185 部署双臂 FR3 + 法奥控制器夹爪

本文说明如何从桌面副本的 4fee185 版本更新到当前 main，并在同一个 fr3-standard/third_party 目录中应用法奥驱动补丁、编译和验收实机双臂与夹爪。

## 1. 目录要求

不需要创建 fr3_vendor_ws。厂商源码直接放在本仓库的 third_party 中：

```text
fr3-standard/
├── src/
└── third_party/
    ├── fairino_dual_arm_ip.patch
    ├── fairino_gripper_interface.patch
    └── frcobot_ros2-v3.0.0_robotV3.9.7/
        ├── fairino_msgs/
        └── fairino_hardware_v3_9_7/
```

补丁只针对 fairino_hardware_v3_9_7，不要应用到其他版本目录。

## 2. 从 4fee185 更新代码

进入桌面副本并确认版本：

```bash
cd ~/fr3-standard
git status
git log -1 --oneline
```

如果显示 4fee185 Add Fairino dual-IP patch file，直接快进更新：

```bash
git fetch origin
git pull --ff-only origin main
```

不要使用以下命令清理未跟踪的厂商源码：

```bash
git reset --hard
git clean -fd
```

更新后确认夹爪补丁存在：

```bash
ls third_party/fairino_gripper_interface.patch
git log --oneline --decorate -6
```

当前相关提交包括：

```text
8daa83b Fix real gripper hardware integration
96df9f9 Add from-scratch deployment guide
e381636 Share Fairino RPC between arm and gripper hardware
7bc4e81 Add Fairino gripper hardware interface
4fee185 Add Fairino dual-IP patch file
```

## 3. 应用法奥驱动补丁

进入补丁根目录。这里同时能看到补丁和 fairino_hardware_v3_9_7：

```bash
cd ~/fr3-standard/third_party
ls fairino_dual_arm_ip.patch
ls fairino_gripper_interface.patch
ls frcobot_ros2-v3.0.0_robotV3.9.7/fairino_hardware_v3_9_7/src/fairino_hardware_interface.cpp
```

先检查并应用双 IP 补丁：

```bash
patch --dry-run -p1 < fairino_dual_arm_ip.patch
patch -p1 < fairino_dual_arm_ip.patch
```

成功时应看到：

```text
checking file fairino_hardware_v3_9_7/src/fairino_hardware_interface.cpp
```

再检查并应用夹爪补丁：

```bash
patch --dry-run -p1 < fairino_gripper_interface.patch
patch -p1 < fairino_gripper_interface.patch
```

如果提示 Reversed (or previously applied) patch detected，说明补丁已经应用，不要重复执行。可用下面的命令确认：

```bash
patch --dry-run -R -p1 < fairino_gripper_interface.patch
```

## 4. 检查补丁内容

```bash
rg -n \
"robot_ip|gripper_index|ActGripper|MoveGripper|GetGripperCurPosition|has_gripper" \
frcobot_ros2-v3.0.0_robotV3.9.7/fairino_hardware_v3_9_7/include/fairino_hardware/fairino_hardware_interface.hpp \
frcobot_ros2-v3.0.0_robotV3.9.7/fairino_hardware_v3_9_7/src/fairino_hardware_interface.cpp
```

应能看到 robot_ip、gripper_index、ActGripper、MoveGripper、GetGripperCurPosition 和 has_gripper。

当前版本把夹爪接入已有的 fairino_hardware/FairinoHardwareInterface，左右每个控制器只建立一条 Fairino RPC 连接。

## 5. 编译厂商驱动

```bash
cd ~/fr3-standard/third_party/frcobot_ros2-v3.0.0_robotV3.9.7
colcon build --symlink-install \
  --packages-select fairino_msgs fairino_hardware_v3_9_7
source install/setup.bash
```

## 6. 配置实机参数

复制示例配置：

```bash
cp ~/fr3-standard/src/fr3_dual_arm_hardware/config/hardware.example.yaml \
   ~/fr3_dual_arm.hardware.yaml
cp ~/fr3-standard/src/fr3_dual_arm_description/config/arms.yaml \
   ~/fr3_dual_arm.arms.yaml
cp ~/fr3-standard/src/fr3_dual_arm_description/config/scene.yaml \
   ~/fr3_dual_arm.scene.yaml
```

编辑 ~/fr3_dual_arm.hardware.yaml：

```yaml
driver_package: fairino_hardware_v3_9_7
firmware: '3.9.7'
commissioned: true

left:
  robot_ip: '192.168.58.4'
  gripper_index: 1

right:
  robot_ip: '192.168.58.2'
  gripper_index: 1

gripper:
  vel: 50
  force: 50
  maxtime: 30000
  block: 1
  open_pos: 0
  closed_pos: 100
```

robot_ip 和 gripper_index 必须以现场实际配置为准；open_pos 和 closed_pos 需要根据夹爪实际开合方向校准。

## 7. 编译 fr3-standard

先加载厂商环境，再编译主工程：

```bash
source ~/fr3-standard/third_party/frcobot_ros2-v3.0.0_robotV3.9.7/install/setup.bash
cd ~/fr3-standard
colcon build --symlink-install \
  --packages-up-to fr3_dual_arm_bringup
source install/setup.bash
```

## 8. 启动与验收

第一次只启动反馈和控制器，不执行机械臂轨迹：

```bash
ros2 launch fr3_dual_arm_bringup real.launch.py \
  hardware:=~/fr3_dual_arm.hardware.yaml \
  arms:=~/fr3_dual_arm.arms.yaml \
  scene:=~/fr3_dual_arm.scene.yaml \
  enable_execution:=false \
  rviz:=false
```

检查控制器和硬件接口：

```bash
ros2 control list_controllers -c /left_controller_manager
ros2 control list_controllers -c /right_controller_manager
ros2 control list_hardware_interfaces -c /left_controller_manager
ros2 control list_hardware_interfaces -c /right_controller_manager
```

确认左右手臂反馈正常、夹爪控制器已经加载后，再用 enable_execution:=true 重新启动。

检查夹爪 action：

```bash
ros2 action list -t | grep gripper
```

测试左夹爪打开和闭合：

```bash
ros2 action send_goal \
  /left_gripper_controller/command \
  control_msgs/action/GripperCommand \
  "{command: {position: 0.03, max_effort: 50.0}}"

ros2 action send_goal \
  /left_gripper_controller/command \
  control_msgs/action/GripperCommand \
  "{command: {position: 0.0, max_effort: 50.0}}"
```

右夹爪把 action 名称替换为 /right_gripper_controller/command。

## 9. 常见问题

### 找不到夹爪补丁

```bash
cd ~/fr3-standard
git pull --ff-only origin main
ls third_party/fairino_gripper_interface.patch
```

### 补丁找不到目标文件

必须在下面这个目录执行补丁命令：

```bash
cd ~/fr3-standard/third_party
ls frcobot_ros2-v3.0.0_robotV3.9.7/fairino_hardware_v3_9_7/src/fairino_hardware_interface.cpp
```

### 补丁已经应用

看到 Reversed (or previously applied) patch detected 时不要重复应用：

```bash
patch --dry-run -R -p1 < fairino_gripper_interface.patch
```

### 修改后仍使用旧驱动

重新编译并按顺序加载环境：

```bash
source ~/fr3-standard/third_party/frcobot_ros2-v3.0.0_robotV3.9.7/install/setup.bash
source ~/fr3-standard/install/setup.bash
```

软件停止、RViz Stop 或 action cancel 都不能替代硬件急停。

