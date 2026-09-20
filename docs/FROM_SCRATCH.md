# FR3 双臂 + HKV 夹爪从零部署说明

> 本文是历史安装记录。实机驱动目录、补丁、构建和启动命令已由
> [共享 SDK 连接升级说明](REAL_HARDWARE_FROM_4FEE185.md) 替代。
> 已有 `~/fr3-standard/third_party` 的用户不要照本文再建 `fr3_vendor_ws`，
> 也不要套用旧的独立连接或合并关节补丁步骤。

本文面向一台新的 Ubuntu 22.04 机器，从安装 ROS 2 Humble 开始，到夹爪低速验收结束。

## 0. 硬件与厂商包准备

现场需要准备：

- 两台 FR3，控制柜版本对应 `3.9.7`
- 两个 HKV TG-9801 夹爪分别挂在两台 FR3 末端，由法奥控制器统一驱动
- 法奥 SDK 归档 `frcobot_ros2-v3.0.0_robotV3.9.7`

假设厂商归档位于：

```bash
~/vendor/frcobot_ros2-v3.0.0_robotV3.9.7
```

其中至少包含：

```text
fairino_msgs/
fairino_description/
fairino_hardware_v3_9_7/
```

## 1. 安装 ROS 2 Humble

```bash
sudo apt update
sudo apt install -y curl gnupg lsb-release

sudo curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key \
  -o /usr/share/keyrings/ros-archive-keyring.gpg

echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] http://packages.ros.org/ros2/ubuntu $(lsb_release -cs) main" \
  | sudo tee /etc/apt/sources.list.d/ros2.list > /dev/null

sudo apt update
sudo apt install -y ros-humble-desktop python3-rosdep
```

初始化 rosdep：

```bash
sudo rosdep init
rosdep update
```

## 2. 安装项目需要的系统工具

```bash
sudo apt install -y \
  python3-colcon-common-extensions \
  python3-vcstool \
  python3-pip \
  python3-yaml \
  patch \
  build-essential
```

## 3. 克隆 fr3-standard

```bash
mkdir -p ~/fr3_ws
cd ~/fr3_ws

git clone https://github.com/bobsuneay/fr3-standard.git
cd fr3-standard
git checkout main
```

定义路径变量：

```bash
FR3_REPO=~/fr3_ws/fr3-standard
```

## 4. 准备厂商驱动工作区

建议单独建立驱动工作区，不直接混入项目工作区：

```bash
mkdir -p ~/fr3_vendor_ws/src

cp -r ~/vendor/frcobot_ros2-v3.0.0_robotV3.9.7/fairino_msgs \
      ~/fr3_vendor_ws/src/

cp -r ~/vendor/frcobot_ros2-v3.0.0_robotV3.9.7/fairino_hardware_v3_9_7 \
      ~/fr3_vendor_ws/src/
```

如需完全干净的环境，可以直接从备份重新复制厂商包。

## 5. 给厂商驱动打补丁

进入驱动工作区的 `src` 目录：

```bash
cd ~/fr3_vendor_ws/src
```

先打双 IP 补丁：

```bash
patch -p1 --dry-run < "$FR3_REPO/third_party/fairino_dual_arm_ip.patch"
patch -p1 < "$FR3_REPO/third_party/fairino_dual_arm_ip.patch"
```

再打夹爪合并补丁：

```bash
patch -p1 --dry-run < "$FR3_REPO/third_party/fairino_gripper_interface.patch"
patch -p1 < "$FR3_REPO/third_party/fairino_gripper_interface.patch"
```

验证补丁是否成功：

```bash
grep -n 'hardware_parameters.find("robot_ip")' \
  fairino_hardware_v3_9_7/src/fairino_hardware_interface.cpp

grep -n 'gripper_index' \
  fairino_hardware_v3_9_7/src/fairino_hardware_interface.cpp

grep -n 'GetGripperCurPosition' \
  fairino_hardware_v3_9_7/src/fairino_hardware_interface.cpp
```

注意：夹爪补丁不会新增独立的 `FairinoGripperHardwareInterface` 类，而是直接修改官方
`FairinoHardwareInterface`，让 6 轴手臂和夹爪共用同一个硬件实例、同一条法奥 SDK RPC 连接。

## 6. 编译厂商驱动

```bash
source /opt/ros/humble/setup.bash

cd ~/fr3_vendor_ws

rosdep install --from-paths src --ignore-src -r -y --rosdistro humble

colcon build --symlink-install \
  --packages-up-to fairino_hardware_v3_9_7

source ~/fr3_vendor_ws/install/setup.bash
```

## 7. 编译 fr3-standard

```bash
source /opt/ros/humble/setup.bash
source ~/fr3_vendor_ws/install/setup.bash

cd "$FR3_REPO"

rosdep install --from-paths src --ignore-src -r -y --rosdistro humble

colcon build --symlink-install

source "$FR3_REPO/install/setup.bash"
```

## 8. 准备现场配置

```bash
cp "$FR3_REPO/src/fr3_dual_arm_hardware/config/hardware.example.yaml" \
   ~/fr3_dual_arm.hardware.yaml

cp "$FR3_REPO/src/fr3_dual_arm_description/config/arms.yaml" \
   ~/fr3_dual_arm.arms.yaml

cp "$FR3_REPO/src/fr3_dual_arm_description/config/scene.yaml" \
   ~/fr3_dual_arm.scene.yaml
```

编辑 `~/fr3_dual_arm.hardware.yaml`：

```yaml
driver_package: fairino_hardware_v3_9_7
firmware: '3.9.7'
commissioned: true

left:
  robot_ip: 192.168.58.5
  gripper_index: 1

right:
  robot_ip: 192.168.58.2
  gripper_index: 1

gripper:
  vel: 50
  force: 50
  maxtime: 30000
  block: 1
  open_pos: 0
  closed_pos: 100
```

`robot_ip`、`gripper_index`、`open_pos` 和 `closed_pos` 必须按现场实测填写。

## 9. 每个终端都按这个顺序 source

```bash
source /opt/ros/humble/setup.bash
source ~/fr3_vendor_ws/install/setup.bash
source ~/fr3_ws/fr3-standard/install/setup.bash

export ROS_DOMAIN_ID=32
```

建议写入 `~/fr3_env.sh` 后直接 `source ~/fr3_env.sh`。

## 10. 只读反馈启动

```bash
ros2 launch fr3_dual_arm_bringup real.launch.py \
  hardware:=$HOME/fr3_dual_arm.hardware.yaml \
  enable_execution:=false
```

另开终端检查控制器：

```bash
ros2 control list_controllers -c /left_controller_manager
ros2 control list_controllers -c /right_controller_manager
```

应看到每侧都有：

```text
joint_state_broadcaster  active
arm_controller           inactive
gripper_controller       inactive
```

检查硬件接口：

```bash
ros2 control list_hardware_interfaces -c /left_controller_manager
ros2 control list_hardware_interfaces -c /right_controller_manager
```

每侧应只有一组 `FairinoHardwareInterface`，包含 6 个手臂关节和 1 个
`*_left_finger_joint`。

## 11. 低速空载测试夹爪

确认 action：

```bash
ros2 action list -t | grep gripper
```

测试左夹爪开、合：

```bash
ros2 action send_goal /left_gripper_controller/command \
  control_msgs/action/GripperCommand \
  "{command: {position: 0.03, max_effort: 0.0}}"

ros2 action send_goal /left_gripper_controller/command \
  control_msgs/action/GripperCommand \
  "{command: {position: 0.00025, max_effort: 0.0}}"
```

测试右夹爪：

```bash
ros2 action send_goal /right_gripper_controller/command \
  control_msgs/action/GripperCommand \
  "{command: {position: 0.03, max_effort: 0.0}}"
```

## 12. 通过后再开启执行

```bash
ros2 launch fr3_dual_arm_bringup real.launch.py \
  hardware:=$HOME/fr3_dual_arm.hardware.yaml \
  enable_execution:=true
```

## 13. 常见问题定位

- 启动日志卡在 `FairinoHardwareInterface: Starting ...please wait...`：
  通常是 RPC 连接或伺服模式问题，检查该侧 IP、急停和控制柜使能状态。
- `ActGripper` 失败：检查 `gripper_index` 以及夹爪是否已在示教器上配置并启用。
- 夹爪不动：检查 `open_pos` / `closed_pos` 标定，并确认 `block: 1`。
- 找不到 `FairinoHardwareInterface`：说明厂商驱动没有重新编译，或没有 source
  `~/fr3_vendor_ws/install/setup.bash`。
