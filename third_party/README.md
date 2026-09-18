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

```text
ros2_hkv_gripper/
```

## 说明

- 不要同时 source 多个 `fairino_hardware*` 版本。
- 官方驱动编译成功后，再在本项目的 `fr3_dual_arm_hardware` 中做适配。
- 第三方包 license 按各自上游声明处理。
