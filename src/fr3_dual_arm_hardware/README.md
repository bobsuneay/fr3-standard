# fr3_dual_arm_hardware

这是实机部署的核心差异包。当前提供 ros2_control `SystemInterface` 骨架，`read()` 和 `write()` 尚未接入厂商通信。

## 后续接入

1. 把 `fairino_hardware_v3_9_7` 放入 `third_party` 并编译。
2. 6 轴手臂直接复用 `fairino_hardware/FairinoHardwareInterface`（按 `robot_ip` 走 RPC/socket）。
3. 夹爪按 `gripper_index` 走法奥 SDK：实现 `fairino_hardware/FairinoGripperHardwareInterface`。
   - `read()` 调 `GetGripperCurPosition` 回读 0–100 位置。
   - `write()` 把手指关节位置映射成 0–100 后调 `MoveGripper`。
   - 该插件实现前，`real.launch.py` 暂时用 `mock_components/GenericSystem` 占位，
     这样实机启动不会因缺插件而崩溃，可以先用 6 轴手臂反馈做验收。
4. 夹爪开合参数在 `hardware.example.yaml` 的 `gripper.vel / force / maxtime / block / open_pos / closed_pos` 中配置。

## 安全

- 实机启动前必须把 `commissioned` 改为 `true`。
- 第一次启动使用 `enable_execution:=false`。
- 软件取消不能替代硬件急停。
