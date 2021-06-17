from pid import PID
from lowpass import LowPassFilter
from yaw_controller import YawController
import rospy

GAS_DENSITY = 2.858
ONE_MPH = 0.44704

class Controller(object):
    def __init__(self, vehicle_mass, fuel_capacity, wheel_radius, decel_limit, accel_limit, 
                 max_steer_angle, wheel_base, steer_ratio, max_lat_accel, loop_rate):
        self.sample_time = 1.0/loop_rate

        mass = (vehicle_mass + fuel_capacity*GAS_DENSITY)

        # Implement the PID controller for the throttle and brake combined.
        # For positive values of control, the throttle will be used.
        # For negative values of control, it will be converted to brake.
        kp = 0.2
        ki = 0.002
        kd = 0.005
        v_mn = -1.0
        v_mx = 1.0
        self.vel_controller = PID(kp, ki, kd, v_mn, v_mx)
        self.max_brake = decel_limit * mass * wheel_radius

        min_speed = 10
        self.yaw_controller = YawController(wheel_base, steer_ratio, min_speed, 
                                             max_lat_accel, max_steer_angle)
        
        tau = 2
        ts = 5
        self.steering_lpf = LowPassFilter(tau, ts)

    def control(self, current_vel, dbw_enabled, linear_vel, angular_vel):
        if not dbw_enabled:
            self.vel_controller.reset()
            return 0., 0., 0.
        
        steering = self.yaw_controller.get_steering(linear_vel, angular_vel, current_vel)
        final_steering = self.steering_lpf.filt(steering)

        vel_error = linear_vel - current_vel
        throttle_cmd = self.vel_controller.step(vel_error, self.sample_time)
        
        if linear_vel >= 1.5:
            throttle = throttle_cmd
            brake = 0
        else:
            throttle = 0
            brake = - self.max_brake * 0.4

        # Return throttle, brake, steer
        return throttle, brake, final_steering
    