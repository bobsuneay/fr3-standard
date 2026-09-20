# 厂商驱动与本地补丁

厂商源码直接放在本仓库的 `third_party`，不需要另建厂商工作区：

```text
third_party/
├── fairino_dual_arm_ip.patch
├── fairino_shared_rpc.patch
└── frcobot_ros2-v3.0.0_robotV3.9.7/
    ├── fairino_msgs/
    ├── fairino_description/
    └── fairino_hardware_v3_9_7/
```

厂商源码/SDK 来自用户提供的归档，许可证按上游声明处理；补丁直接修改该驱动，
不添加另外的 ROS 硬件包。

在仓库根目录运行：

```bash
cd ~/fr3-standard
bash scripts/apply_fairino_patches.sh
```

脚本依次检查双 IP、夹爪插件、共享 SDK 连接三个补丁，跳过已应用内容，
先用临时副本验证，再备份并修改原源码。不要独立重复应用旧补丁，也不要强制接受失败的 hunk。

完整的更新、编译、启动和验收步骤见
[从 4fee185 升级](../docs/REAL_HARDWARE_FROM_4FEE185.md)。

## 驱动结构

- 手臂：`fairino_hardware/FairinoHardwareInterface`，6 个关节，保留 ServoJ 控制路径。
- 实机夹爪不加载 ros2_control 插件，使用 `src/fr3_direct_gripper` 直接调用 SDK。
- 手臂仍使用 `fairino_hardware/FairinoHardwareInterface`。
- `fairino_shared_rpc.patch` 不再是实机夹爪必需项；它只适用于旧的插件方案。

夹爪直接调用程序每次执行时建立一次 SDK 连接、执行命令后关闭，不需要
`RemoteCmdInterface` 服务，也不需要夹爪硬件补丁。
只有夹爪改为独立串口直连上位机时，才需要重新评估独立串口驱动方案。
