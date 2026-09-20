# 从 4fee185 升级：双臂与夹爪共享 SDK 连接

适用目录是 `~/fr3-standard`。厂商源码直接修改在其 `third_party` 中，不创建 `fr3_vendor_ws`，不创建另外的硬件插件包。

## 1. 本次修复针对什么

2026-09-20 提供的两份启动日志中，左右夹爪先激活成功，随后左右手臂都停在
`Starting ...please wait...`。16:09 那份日志里的 SDK 失败和进程退出发生在
SIGINT 之后，不能把退出时的错误当作启动前已经证明的网络故障。

结合旧驱动代码，主要疑点是：同一侧的两个硬件插件各自创建一个 `FRRobot`，
分别对同一个 IP 调用 `RPC()`。本次修复移除这条重复连接路径：

- 左右仍各自运行一个 `controller_manager` 进程，分别读取现场配置的 IP。
- 同一进程中的 `FairinoHardwareInterface`（6 个关节）与
  `FairinoGripperHardwareInterface`（1 个开合关节）共享一个 SDK 实例。
- 两个插件的 SDK 调用用互斥锁串行化；最后一个使用者释放时才关闭连接。
- 启动指令从真实反馈初始化；夹爪反馈失败时报告错误，不伪造“已打开”状态。
- 夹爪命令变化时才调用 `MoveGripper`。本版本厂商头文件定义
  `block=0` 为阻塞、`block=1` 为非阻塞，因此保留 `block: 1`。

这是针对日志和代码定位出的重复连接问题的修复；尚未在你的控制柜上实测。
插件注册符号存在只证明相关代码编进库，不能单凭符号证明运行时加载、连接或控制成功。

## 2. 停止旧启动，更新仓库

先在原 launch 终端按 Ctrl+C，确认原来的双臂控制进程退出。不要在旧 launch
仍运行时再启动一份，也不要同时运行会连接同一控制柜的其他 SDK 程序。
保持工作区清空、急停可用；不要为通过检查而绕过机器人安全状态。

在新终端执行：

```bash
cd ~/fr3-standard
git status --short
git pull --ff-only origin main
```

如 Git 提示本地修改冲突或无法快进，停在这里保留输出；不要执行
`git reset --hard` 或 `git clean`，否则可能丢失本地修改或厂商源码。

目录应为：

```text
fr3-standard/
├── scripts/apply_fairino_patches.sh
├── src/
└── third_party/
    ├── fairino_dual_arm_ip.patch
    ├── fairino_gripper_interface.patch
    ├── fairino_shared_rpc.patch
    └── frcobot_ros2-v3.0.0_robotV3.9.7/
        ├── fairino_msgs/
        └── fairino_hardware_v3_9_7/
```

## 3. 自动检查并应用补丁

```bash
cd ~/fr3-standard
bash scripts/apply_fairino_patches.sh
```

脚本会先在临时副本中检查所有补丁，再备份相关源码，最后修改上述
`third_party/frcobot_ros2-v3.0.0_robotV3.9.7/fairino_hardware_v3_9_7`。

支持未打补丁、只打了双 IP、已经打了当前夹爪补丁，以及已经完成共享连接修复的情况。
备份路径会以 `Source backup:` 打印出来，位于临时目录；需要长期保留时请复制到自己的备份目录。
版本不匹配会在修改原始源码之前停止，不会强制覆盖；请把错误贴出来。

正常结尾为：

```text
PASS: shared-RPC source upgrade verified. Rebuild before launching.
```

重复执行应提示 `Shared-RPC upgrade is already applied`，不用重新打补丁。

如果你已经确认双 IP 与当前夹爪补丁都已应用，也可以只手动应用这次增量补丁：

```bash
cd ~/fr3-standard/third_party/frcobot_ros2-v3.0.0_robotV3.9.7
patch --batch --fuzz=0 --forward --dry-run -p1 < ../fairino_shared_rpc.patch &&
patch --batch --fuzz=0 --forward -p1 < ../fairino_shared_rpc.patch
```

用下面的**反向试运行**确认完整应用；不会撤销代码：

```bash
patch --batch --fuzz=0 --dry-run -R -p1 < ../fairino_shared_rpc.patch
echo $?
```

应返回 `0`。不要去掉 `--dry-run` 后执行 `-R`。
升级后旧补丁的反向检查可能因上下文已改变而失败，以新的共享连接补丁检查为准。

## 4. 只在主工作区编译这份驱动

打开一个未加载其他厂商工作区的新终端。不要再使用嵌套的厂商 `install`
作为本次构建结果，否则容易“改了一份、运行另一份”。

```bash
source /opt/ros/humble/setup.bash
cd ~/fr3-standard
colcon build --symlink-install \
  --base-paths src \
    third_party/frcobot_ros2-v3.0.0_robotV3.9.7/fairino_msgs \
    third_party/frcobot_ros2-v3.0.0_robotV3.9.7/fairino_hardware_v3_9_7 \
  --packages-up-to fairino_hardware_v3_9_7 fr3_dual_arm_bringup
```

只有编译成功后才继续：

```bash
source ~/fr3-standard/install/setup.bash
ros2 pkg prefix fairino_hardware_v3_9_7
driver_prefix="$(ros2 pkg prefix fairino_hardware_v3_9_7)"
strings "$driver_prefix/lib/fairino_hardware_v3_9_7/libfairino_hardware.so" \
  | grep -E 'Arm using shared SDK connection|Gripper using shared SDK connection'
```

包路径应在 `~/fr3-standard/install` 下，并且库里两条日志字符串都存在。
合并安装与默认隔离安装的 prefix 形态不同，上面的查询会自动取实际路径。
不要只检查 `registerPlugin` 符号就认定已经运行新版本。

## 5. 保留现场参数，不覆盖 YAML

已有现场配置不要用示例覆盖。你最近日志里的左臂是 `192.168.58.5`，
右臂是 `192.168.58.2`；以现场实际网络设置为准，不要照旧文档改成 `.4`。

核对 `~/fr3_dual_arm.hardware.yaml` 中：

- 左右 `robot_ip` 分别指向对应控制柜。
- 每侧的 `gripper_index` 与示教器一致，不要把左右编号简单理解为 1、2。
- `gripper.block: 1`，`open_pos` / `closed_pos` 方向与实物一致。
- `commissioned` 仅在完成现场检查后按实际情况设置。

如果是新部署，先自行创建并校准现场 YAML，可参考
`src/fr3_dual_arm_hardware/config/hardware.example.yaml`。
arms/scene 也是现场参数；已有文件应继续使用。

## 6. 先检查启动与反馈

```bash
source /opt/ros/humble/setup.bash
source ~/fr3-standard/install/setup.bash
ros2 launch fr3_dual_arm_bringup real.launch.py \
  hardware:=$HOME/fr3_dual_arm.hardware.yaml \
  arms:=$HOME/fr3_dual_arm.arms.yaml \
  scene:=$HOME/fr3_dual_arm.scene.yaml \
  enable_execution:=false \
  rviz:=false
```

上例假设这三个文件确实位于主目录；没有自定义 arms/scene 时可省略那两项使用包内默认值，
但默认场景不能替代现场标定。

**注意：`enable_execution:=false` 不是断电或纯只读模式。**
它让运动控制器保持 inactive、禁止 MoveIt 执行，但硬件仍会激活，
执行夹爪激活，并可能发送维持当前姿态的 ServoJ。必须按实机上电流程保障安全。

成功启动时，每侧应分别看到：

```text
Gripper using shared SDK connection: <该侧IP>
Arm using shared SDK connection: <该侧IP>
机械臂硬件启动成功!
```

手臂/夹爪日志先后顺序不重要。两侧硬件都应激活成功，不再停在第二次 RPC。

另开终端 source 同一套环境，检查：

```bash
source /opt/ros/humble/setup.bash
source ~/fr3-standard/install/setup.bash
ros2 control list_controllers -c /left_controller_manager
ros2 control list_controllers -c /right_controller_manager
ros2 control list_hardware_interfaces -c /left_controller_manager
ros2 control list_hardware_interfaces -c /right_controller_manager
ros2 topic echo /joint_states --once
```

此时**预期**每侧 joint_state_broadcaster 为 active，arm_controller 和
gripper_controller 为 inactive。inactive 不是连接失败，不要为了让列表全部 active 而直接执行运动。

若仍失败，请提供从启动开始到报错的完整日志，以及第 4 节的包路径与字符串检查输出。
RViz 的 planning_scene 服务等待通常是控制器尚未启动、MoveGroup 尚未被启动的后续现象，
应先处理硬件激活错误，不要先调整 RViz 或视觉识别插件。

## 7. 实机低速验收

确认双臂反馈、坐标系、关节方向、夹爪行程与安全区均正确后，停止当前 launch，
再由现场操作人员选择 `enable_execution:=true` 启动。
此时检查两侧 arm/gripper 控制器 active，再用：

```bash
ros2 action list -t | grep gripper
```

确认左右 `/left_gripper_controller/command` 和
`/right_gripper_controller/command` 是 `control_msgs/action/GripperCommand`。

先单侧、空载、低速小行程测试。命令 position 是左手指关节位移（米），
不是 0–100 的 SDK 百分比，也不是完整夹爪开口宽度。
实际速度/夹持力来自 YAML 的 `vel` / `force`；
当前驱动只有 position 命令接口，action 的 max_effort 不会覆盖 SDK 的 force。

不在本文提供可直接批量执行的双臂运动或全行程夹爪命令，避免在标定尚未确认时发生运动。
软件 Stop、action cancel 和进程退出都不能替代硬件急停。

## 8. 本次已完成的离线验证

```bash
python3 tests/shared_rpc/run.py \
  --vendor third_party/frcobot_ros2-v3.0.0_robotV3.9.7/fairino_hardware_v3_9_7 \
  --bash bash --real-sdk-headers
```

测试需要 Python 3、g++ 和 patch。它只在临时目录修改副本，不连接机器人。

- 在用户提供的 3.9.7 源码副本上验证补丁应用、反向检查、重复应用拒绝。
- 测试自动脚本重复运行不改变源码。
- 用真实驱动源文件和假的 ROS/SDK 接口测试两种激活顺序、两种释放顺序，
  同侧只调用一次 RPC、单插件释放不关闭另一插件的连接、重连和错误清理。
- 测试真实反馈初始化、夹爪开度映射、命令去重、反馈失败、ServoJ 错误和第六轴非法指令。
- 用厂商实际 SDK 头文件进行 C++ 语法/签名检查，ROS 侧仍是测试替身。

这些检查不等价于 Ubuntu 上完整的 ROS 构建、pluginlib 加载验证或实机运动验收。
