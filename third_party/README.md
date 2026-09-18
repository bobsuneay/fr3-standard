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
