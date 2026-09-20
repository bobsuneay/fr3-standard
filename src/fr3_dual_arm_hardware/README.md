# fr3_dual_arm_hardware

这是实机部署的核心差异包。当前提供 ros2_control `SystemInterface` 骨架，`read()` 和 `write()` 尚未接入厂商通信。

## 后续接入

1. 把 `fairino_hardware_v3_9_7` 放入 `third_party` 并编译。
2. 6 轴手臂直接复用 `fairino_hardware/FairinoHardwareInterface`（按 `robot_ip` 走 RPC/socket）。
3. 实机夹爪不加载 ros2_control 硬件插件，直接由 `fr3_direct_gripper/fairino_gripper_cli`
   调用法奥 SDK 的 `ActGripper`、`MoveGripper`、`GetGripperCurPosition`。
4. 实机 ros2_control 只负责 6 轴手臂；夹爪参数中的 `gripper_index` 仍用于现场配置。
   - `block` 必须为 `1`，按现场法奥夹爪接口要求配置。

## 安全

- 实机启动前必须把 `commissioned` 改为 `true`。
- 第一次启动使用 `enable_execution:=false`。
- 软件取消不能替代硬件急停。
