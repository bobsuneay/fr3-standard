# fr3_dual_arm_hardware

这是实机部署的核心差异包。当前提供 ros2_control `SystemInterface` 骨架，`read()` 和 `write()` 尚未接入厂商通信。

## 后续接入

1. 把 `fairino_hardware_v3_9_7` 和 `ros2_hkv_gripper` 放入 `third_party` 并编译。
2. 在 `read()` 中读取两台 FR3 的实际关节角。
3. 在 `write()` 中发送轨迹目标。
4. 夹爪通过 `ros2_hkv_gripper/GripperHardwareInterface` 接入，或在本接口中集成。

## 安全

- 实机启动前必须把 `commissioned` 改为 `true`。
- 第一次启动使用 `enable_execution:=false`。
- 软件取消不能替代硬件急停。
