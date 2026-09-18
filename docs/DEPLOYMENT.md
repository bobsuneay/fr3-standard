# 实机部署清单

## 1. 硬件确认

- 两台 FR3 控制柜版本确认，默认对应 `3.9.7` 源码。
- 两个 HKV TG-9801 夹爪分别连接不同串口。
- 两台机器人 IP 不同，建议避免都使用默认 `192.168.58.2`。
- 相机、急停、工作区域清空。

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
