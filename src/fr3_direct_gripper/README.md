# Direct FAIRINO SDK gripper control

This package intentionally does not implement a ros2_control hardware plugin.
The executable creates one `FRRobot`, calls `RPC`, activates the configured
gripper, performs one SDK operation, and closes the RPC connection.

Examples:

```bash
ros2 run fr3_direct_gripper fairino_gripper_cli -- --ip 192.168.58.5 --index 1 --read
ros2 run fr3_direct_gripper fairino_gripper_cli -- --ip 192.168.58.5 --index 1 --percent 50
```

The percentage is the FAIRINO SDK's 0–100 position, not meters. Test the
direction and limits unloaded. Real-mode launch only starts the arm controllers;
it does not expose a gripper action.
