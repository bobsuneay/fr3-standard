# third_party

这里只放厂商驱动和外部依赖，不应修改其上游逻辑。

## 法奥 ROS2 驱动

把以下内容从用户提供的归档复制到 Ubuntu 工作区并编译：

```text
frcobot_ros2-v3.0.0_robotV3.9.7/
├── fairino_msgs/
├── fairino_description/
├── fairino_hardware_v3_9_7/
└── fairino3_v6_moveit2_config/   # 仅作为单臂参考，不作为本项目主配置
```

## HKV 夹爪驱动

本项目默认的 HKV TG-9801 夹爪挂在法奥 FR3 末端，由法奥控制器统一驱动，
因此不需要独立的 `ros2_hkv_gripper` USB 串口驱动。夹爪控制复用上面
`fairino_hardware_v3_9_7` 里的 SDK 接口：

- `ActGripper(index, act)`
- `MoveGripper(index, pos, vel, force, max_time, block, ...)`
- `GetGripperCurPosition(...)`

本仓库的 `fairino_gripper_interface.patch` 直接修改官方已有的
`fairino_hardware/FairinoHardwareInterface`，让同一个 ros2_control 硬件实例
同时处理 6 个手臂关节和 1 个夹爪关节。

这样每台机械臂只保持一条法奥 SDK RPC 连接，避免再开一个独立的
`FairinoGripperHardwareInterface` 造成同进程双 RPC 冲突。夹爪逻辑仍复用同一
个 `FRRobot`：

- `on_activate()`：连接控制器后执行 `ActGripper`；
- `read()`：手臂反馈之外调用 `GetGripperCurPosition`；
- `write()`：手臂 `ServoJ` 之外，在夹爪目标变化时调用 `MoveGripper`。

仅当夹爪改回独立串口直连上位机时，才需要：

```text
ros2_hkv_gripper/
```

## 说明

- 不要同时 source 多个 `fairino_hardware*` 版本。
- 官方驱动编译成功后，再在本项目的 `fr3_dual_arm_hardware` 中做 6 轴与夹爪适配。
- 第三方包 license 按各自上游声明处理。

## 必须打的补丁：让 FairinoHardwareInterface 支持双 IP

法奥 `fairino_hardware_v3_9_7` 的 `FairinoHardwareInterface` 默认把控制器 IP
写死为 `192.168.58.2`，并且没有读取 ros2_control 的 `robot_ip` 参数：

```cpp
// include/fairino_hardware/fairino_hardware_interface.hpp
#define CONTROLLER_IP_ADDRESS "192.168.58.2"
std::string _controller_ip = CONTROLLER_IP_ADDRESS;
```

因此左、右两个硬件实例都会去连 `192.168.58.2`，第一个连上，第二个报
“机械臂SDK连接失败！请检查端口时候被占用”。本项目在 URDF 里传的
`<param name="robot_ip">` 不会被它读取。

请修改 `fairino_hardware_v3_9_7/src/fairino_hardware_interface.cpp` 的
`on_init()`，在 `info_ = sysinfo;` 之后加：

```cpp
    auto robot_ip = info_.hardware_parameters.find("robot_ip");
    if (robot_ip != info_.hardware_parameters.end() && !robot_ip->second.empty()) {
        _controller_ip = robot_ip->second;
    }
    RCLCPP_INFO(rclcpp::get_logger("FairinoHardwareInterface"),
                "FairinoHardwareInterface connecting to robot IP: %s",
                _controller_ip.c_str());
```

重新编译 `fairino_hardware_v3_9_7` 后，左右臂才会分别连到各自配置的 IP。

仓库内已提供补丁文件 `third_party/fairino_dual_arm_ip.patch`。在
`frcobot_ros2-v3.0.0_robotV3.9.7/` 目录下执行：

```bash
git apply --check fairino_dual_arm_ip.patch   # 先检查
git apply fairino_dual_arm_ip.patch           # 再应用
```

或用 `patch -p1 < fairino_dual_arm_ip.patch`。应用后重新编译
`fairino_hardware_v3_9_7` 即可。

应用夹爪补丁：

```bash
patch -p1 --dry-run < /path/to/fr3_dualarm_deploy_ws/third_party/fairino_gripper_interface.patch
patch -p1 < /path/to/fr3_dualarm_deploy_ws/third_party/fairino_gripper_interface.patch
```

应用后重新编译 `fairino_hardware_v3_9_7`。`block` 必须配置为 `1`
（非阻塞），否则会在 ros2_control 控制循环里阻塞。

补充：`include/fairino_hardware/data_type_def.h:17` 里还有一个
`#define CONTROLLER_IP "192.168.58.2"`，它被 `command_server.cpp` /
`CNDE_thread.cpp` 使用（法奥的 `RemoteCmdInterface` 字符串指令服务和 UDP 线程）。
当前只做 6 轴手臂反馈时不用改它；以后用 `RemoteCmdInterface` 发 `MoveGripper`
控制夹爪时，如果那个节点也要连非默认 IP，同样需要让它从参数读 IP。
