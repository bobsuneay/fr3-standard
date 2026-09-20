# FR3 双臂抓取与检测部署工作区

实机更新请先看 [双臂与夹爪共享 SDK 连接升级说明](docs/REAL_HARDWARE_FROM_4FEE185.md)。
如果夹爪先激活、手臂卡在 `Starting ...please wait...`，本次修复让同侧两个硬件插件共享一个连接。
厂商源码直接修改在 `~/fr3-standard/third_party`，不需要另建工作区。

这是一个从 `fr3-sim5` 中 **`fr3_bolt_inspection_cell`** 提炼出来的新 ROS 2 工作区骨架。

目标不是把原来的 `fr3_dual_bolt_cell` / `fr3_bolt_inspection_cell` 整个复制过来，而是把它的真实场景参数、双臂模型、点云识别、定点抓取、检测与交接能力，按主流的 ROS 2 分层结构重新组织。

## 设计原则

- 模型与场景共享，仿真与实机共用同一套 MoveIt 配置。
- 上层抓取业务不直接依赖 Gazebo 或厂商 SDK。
- 仿真、mock、实机只切换底层硬件接口，不修改抓取逻辑。
- 厂商驱动和第三方模型放入 `third_party`，与业务代码隔离。
- 实机安全边界清晰：软件取消不能替代急停，实机启动前必须完成现场配置与低速验收。

## 目录结构

```text
fr3-standard/
├── src/
│   ├── fr3_dual_arm_description/      # URDF/xacro、FR3/HKV 网格、场景参数
│   ├── fr3_dual_arm_moveit_config/    # SRDF、运动学、控制器桥接
│   ├── fr3_dual_arm_gazebo/           # Gazebo 仿真专用：world、控制器、启动
│   ├── fr3_dual_arm_hardware/         # 实机 ros2_control 硬件接口适配
│   ├── fr3_dual_arm_bringup/          # 仿真/mock/实机统一入口
│   ├── fr3_dual_arm_grasp/            # 定点抓取、检测、交接应用
│   └── fr3_dual_arm_calibration/      # 手眼标定与相机外参管理
├── third_party/                      # 法奥官方驱动与补丁
├── scripts/apply_fairino_patches.sh   # 检查、备份并修改厂商驱动
├── docs/
│   ├── ARCHITECTURE.md
│   ├── PORTING_MAP.md
│   ├── DEPLOYMENT.md
│   └── REAL_HARDWARE_FROM_4FEE185.md
├── build/
├── install/
└── log/
```

## 启动方式

在 Ubuntu 22.04 + ROS 2 Humble 环境编译后：

```bash
source /opt/ros/humble/setup.bash
cd ~/fr3-standard
rosdep install --from-paths src --ignore-src -r -y
colcon build --symlink-install
source install/setup.bash
```

仿真预览：

```bash
ros2 launch fr3_dual_arm_bringup sim.launch.py enable_execution:=true
```

无 Gazebo 的 mock 模式：

```bash
ros2 launch fr3_dual_arm_bringup mock.launch.py enable_execution:=true
```

实机模式：

```bash
ros2 launch fr3_dual_arm_bringup real.launch.py \
  hardware:=$HOME/fr3_dual_arm.hardware.yaml \
  enable_execution:=false
```

实机第一次运行必须使用 `enable_execution:=false`，先确认反馈和控制器状态。
这不是纯只读/断电模式：硬件仍会激活，并可能发送维持姿态的 ServoJ；必须保持现场安全措施。

## 当前状态

本目录先交付清晰的工程骨架、真实参数和迁移说明。`fr3_bolt_inspection_cell` 中已经实现但尚未迁入本工作区的模块，请按 [docs/PORTING_MAP.md](docs/PORTING_MAP.md) 逐项迁移。
