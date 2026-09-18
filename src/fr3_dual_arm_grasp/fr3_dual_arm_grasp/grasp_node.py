"""External service entry point for the dual-arm pick/inspection workflow.

The full state machine from ``fr3_bolt_inspection_cell.task_node`` should be
ported here. This minimal node only defines the public service interface so
the bringup and UI packages can be developed independently.
"""

import rclpy
from rclpy.node import Node
from std_srvs.srv import Trigger


class GraspNode(Node):
    def __init__(self):
        super().__init__('fr3_dual_arm_grasp')
        self.create_service(Trigger, '/grasp/start', self.start)
        self.create_service(Trigger, '/grasp/stop', self.stop)
        self.create_service(Trigger, '/grasp/status', self.status)

    def start(self, request, response):
        response.success = False
        response.message = 'TODO: port pick/inspection state machine'
        return response

    def stop(self, request, response):
        response.success = False
        response.message = 'TODO: cancel current motion while preserving grasp'
        return response

    def status(self, request, response):
        response.success = True
        response.message = 'IDLE'
        return response


def main():
    rclpy.init()
    node = GraspNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
