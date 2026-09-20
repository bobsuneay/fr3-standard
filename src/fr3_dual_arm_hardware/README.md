# fr3_dual_arm_hardware

这是实机部署的核心差异包。当前提供 ros2_control `SystemInterface` 骨架，`read()` 和 `write()` 尚未接入厂商通信。

## 后续接入

1. 把 `fairino_hardware_v3_9_7` 放入 `third_party` 并编译。
2. 6 轴手臂直接复用 `fairino_hardware/FairinoHardwareInterface`（按 `robot_ip` 走 RPC/socket）。
3. 夹爪按 `gripper_index` 走法奥 SDK：厂商驱动补丁会修改
   `fairino_hardware/FairinoHardwareInterface`，让 6 轴手臂和夹爪共用同一个
   硬件实例和同一条 RPC 连接。
   - `read()` 调 `GetGripperCurPosition` 回读 0–100 位置。
   - `write()` 把手指关节位置映射成 0–100 后调 `MoveGripper`。
   - 补丁见 `../../third_party/fairino_gripper_interface.patch`。
4. 夹爪开合参数在 `hardware.example.yaml` 的 `gripper.vel / force / maxtime / block / open_pos / closed_pos` 中配置。
   - `block` 必须为 `1`，避免在 ros2_control 控制循环内阻塞。

## 安全

- 实机启动前必须把 `commissioned` 改为 `true`。
- 第一次启动使用 `enable_execution:=false`。
- 软件取消不能替代硬件急停。
