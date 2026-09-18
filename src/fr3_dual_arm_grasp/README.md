# fr3_dual_arm_grasp

上层抓取、检测和双臂交接业务。

## 模块规划

```text
fr3_dual_arm_grasp/
├── perception.py        # 点云分割、螺丝位姿估计
├── moveit_interface.py  # MoveIt action/service 统一封装
├── cartesian.py         # 笛卡尔路径、重定时与安全校验
├── handover.py          # 双臂交接预检与执行
├── feedback.py          # 关节/夹爪反馈映射
├── grasp_node.py        # 状态机与外部服务
└── panel.py             # 可选操作面板
```

本包只依赖 MoveIt 和 ros2_control 的标准接口，不直接 import Gazebo 或厂商 SDK。
