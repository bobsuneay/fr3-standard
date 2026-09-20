# 实机部署清单

具体更新、补丁与编译步骤以 [共享 SDK 连接升级说明](REAL_HARDWARE_FROM_4FEE185.md) 为准。

## 1. 硬件确认

- 两台 FR3 控制柜版本确认，默认对应 `3.9.7` 源码。
- 两个 HKV TG-9801 夹爪挂在各自机械臂末端，由法奥控制器统一驱动，**不要**再通过 USB 串口直连上位机。
- 在示教器/手册上确认每台机器人对应的夹爪编号 `gripper_index`（通常为 1，多夹爪时不同）。
- 两台机器人 IP 不同，建议避免都使用默认 `192.168.58.2`。
- 相机、急停、工作区域清空。

本项目实机启动不再通过 `RemoteCmdInterface` 手动发指令，而是由
实机 ros2_control 只加载 `fairino_hardware/FairinoHardwareInterface` 控制手臂。
夹爪由 `fr3_direct_gripper/fairino_gripper_cli` 直接调用法奥 SDK；不需要
`fairino_gripper_interface.patch` 或 `fairino_shared_rpc.patch`。

## 2. 现场参数

只有新部署且目标文件不存在时才复制示例，再校准。已有现场配置不要覆盖：

```bash
cp -n src/fr3_dual_arm_hardware/config/hardware.example.yaml ~/fr3_dual_arm.hardware.yaml
cp -n src/fr3_dual_arm_description/config/arms.yaml ~/fr3_dual_arm.arms.yaml
cp -n src/fr3_dual_arm_description/config/scene.yaml ~/fr3_dual_arm.scene.yaml
```

需要实测：

- 左/右基座相对世界坐标系的 6D 安装位姿
- TCP 和夹爪开度/行程
- 相机外参
- 桌面、立柱、被抓零件的位置
- 每台机器人实际的 `gripper_index` 与夹爪开合百分比（`open_pos` / `closed_pos`）

> `hardware.example.yaml` 里已经删除了 `serial_port`，改为 `gripper_index`。
> 夹爪开合现在通过法奥 SDK 完成，`ros2_hkv_gripper`（USB 串口 Modbus）只适用于夹爪独立串口直连的场景。

## 3. 先反馈后执行

`enable_execution:=false` 只让运动控制器 inactive，硬件仍会激活，
并可能发送维持姿态的 ServoJ；它不是安全停机或纯只读模式。

```bash
ros2 launch fr3_dual_arm_bringup real.launch.py \
  hardware:=$HOME/fr3_dual_arm.hardware.yaml \
  enable_execution:=false
```

确认：

```bash
ros2 control list_controllers -c /left_controller_manager
ros2 control list_controllers -c /right_controller_manager
ros2 topic echo /joint_states --once
```

实机夹爪直接控制（SDK 百分比 0–100）：

```bash
ros2 run fr3_direct_gripper fairino_gripper_cli -- \
  --ip 192.168.58.5 --index 1 --read
ros2 run fr3_direct_gripper fairino_gripper_cli -- \
  --ip 192.168.58.5 --index 1 --percent 50
```

右夹爪把 IP 替换成右控制柜地址。`--percent` 的方向以现场实测为准，
先空载、小范围测试；程序会直接调用 `ActGripper` 和非阻塞 `MoveGripper`。

## 4. 低速小范围验收

- 每只手臂单独做小幅度关节运动。
- 每个夹爪空载开合。
- 双臂联合规划前再次检查碰撞。

## 5. 上线抓取

```bash
ros2 launch fr3_dual_arm_bringup real.launch.py \
  hardware:=$HOME/fr3_dual_arm.hardware.yaml \
  enable_execution:=true
```

> 软件停止、RViz Stop 或 action cancel 都不能替代硬件急停。
