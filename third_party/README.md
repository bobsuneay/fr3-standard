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

需要补一个薄封装 `fairino_hardware/FairinoGripperHardwareInterface`（ros2_control
`SystemInterface`），在 `read()` 中读 `GetGripperCurPosition`，在 `write()` 中把
手指位置映射成 0–100 百分比后调用 `MoveGripper`。

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

补充：`include/fairino_hardware/data_type_def.h:17` 里还有一个
`#define CONTROLLER_IP "192.168.58.2"`，它被 `command_server.cpp` /
`CNDE_thread.cpp` 使用（法奥的 `RemoteCmdInterface` 字符串指令服务和 UDP 线程）。
当前只做 6 轴手臂反馈时不用改它；以后用 `RemoteCmdInterface` 发 `MoveGripper`
控制夹爪时，如果那个节点也要连非默认 IP，同样需要让它从参数读 IP。
