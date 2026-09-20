# 实机部署清单

## 1. 硬件确认

- 两台 FR3 控制柜版本确认，默认对应 `3.9.7` 源码。
- 两个 HKV TG-9801 夹爪挂在各自机械臂末端，由法奥控制器统一驱动，**不要**再通过 USB 串口直连上位机。
- 在示教器/手册上确认每台机器人对应的夹爪编号 `gripper_index`（通常为 1，多夹爪时不同）。
- 两台机器人 IP 不同，建议避免都使用默认 `192.168.58.2`。
- 相机、急停、工作区域清空。

夹爪走法奥 SDK 接口（`ActGripper` / `MoveGripper` / `GetGripperCurPosition`），
通过法奥驱动的 `RemoteCmdInterface` 服务下发字符串指令，例如：

```bash
ros2 service call /remote_cmd_interface fairino_msgs/srv/RemoteCmdInterface \
  "{cmd_str: 'MoveGripper(1,50)'}"
```

本项目实机启动不再通过 `RemoteCmdInterface` 手动发指令，而是由
`fairino_hardware/FairinoGripperHardwareInterface` 把 ros2_control 的
`GripperCommand` action 映射到 SDK `MoveGripper`。该接口和双 IP 读取已经
直接写入 `../fr3-inspection-sim2real/src/fairino_hardware_v3_9_7`，重新编译
这个厂商驱动目录即可。

## 2. 现场参数

复制并修改：

```bash
cp src/fr3_dual_arm_hardware/config/hardware.example.yaml ~/fr3_dual_arm.hardware.yaml
cp src/fr3_dual_arm_description/config/arms.yaml ~/fr3_dual_arm.arms.yaml
cp src/fr3_dual_arm_description/config/scene.yaml ~/fr3_dual_arm.scene.yaml
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
