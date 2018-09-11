# Written mostly by Josh Bradshaw and modified by Jake Misra
# Test is meant to run all 3 motors through slightly accelerated testing
# Each cycle is around 3 seconds (1 per motor)

from motor import bezier
import subprocess
import logging
import datetime
import argparse

formatter = logging.Formatter('%(asctime)s %(name)-12s %(levelname)-8s %(message)s')
logging.basicConfig(filename='/data/logs/bearing_lifetime_test.log',
                    level=logging.DEBUG, formatter=formatter)



# The following has been updated from what we consider the "safe" values. Originally:
# Z:    "full_travel_distance_mm": 205
#       "safe_mmps": 20,
# S:    "safe_mmps": 20,

MOTORS_CONFIG = {
    "Z": {
        "full_travel_distance_mm": 50,
        "safe_mmps": 25,
        "direction": 1,
        "RevolutionsPerMM": 0.25,
    },
    "W": {
        "full_travel_distance_mm": 100,
        "safe_mmps": 200,
        "direction": -1,
        "RevolutionsPerMM": 0.027777777
    },
    "S": {
        "full_travel_distance_mm": 30,
        "safe_mmps": 60,
        "direction": -1,
        "RevolutionsPerMM": 0.026525,
    }
}


def full_scale_motor_test(motor, mmps, dist_mm, direction):
    # move away from limit switch
    motor.move(mmps=mmps, mm=-direction * dist_mm)
    # move toward limit switch
    actual_time_ticks, expected_time_ticks = motor.move(mmps=mmps, mm=1.5 * direction * dist_mm, limit='S')
    return actual_time_ticks, expected_time_ticks


if __name__ == '__main__':
    subprocess.call('/etc/init.d/sauron stop', shell=True)

    argparser = argparse.ArgumentParser(description='Trigger a dispense every 5 seconds')
    argparser.add_argument('--i', default=0, type=int, help='the initial dispense number', action='store', dest='i')
    args = argparser.parse_args()

    z_motor = bezier.Motor('Z')
    s_motor = bezier.Motor('S')
    w_motor = bezier.Motor('W')

    z_motor.home(mm=250)
    s_motor.home(mm=-250)
    w_motor.home(mm=-250)

    cycle_number = args.i

    motor_stats = {
        'Z': {
            'num_revolutions': 0,
        },
        'S': {
            'num_revolutions': 0,
        },
        'W': {
            'num_revolutions': 0,
        }
    }

    while True:
        logging.info('Iteration executed: {}'.format(datetime.datetime.now()))
        logging.info('Test iteration: {}'.format(cycle_number))
        for motor in [z_motor, s_motor, w_motor]:
            motor_configuration = MOTORS_CONFIG[motor.motor]
            actual_time_ticks, expected_time_ticks = full_scale_motor_test(motor, motor_configuration["safe_mmps"],
                                                                           motor_configuration["full_travel_distance_mm"],
                                                                           motor_configuration["direction"])
            motor_stats[motor.motor]['num_revolutions'] += 2 * motor_configuration["full_travel_distance_mm"] * motor_configuration["RevolutionsPerMM"]

            log_message = "Motor: {} Expected return time (ticks): {} Actual return time (ticks): {}".format(motor.motor, expected_time_ticks, actual_time_ticks)
            logging.info(log_message)

        motor_log_message = "Motor Revolutions for Z: {}, for W: {}, for S: {}".format(motor_stats['Z']['num_revolutions'], motor_stats['W']['num_revolutions'], motor_stats['S']['num_revolutions'])
        logging.info(motor_log_message)


        cycle_number += 1
