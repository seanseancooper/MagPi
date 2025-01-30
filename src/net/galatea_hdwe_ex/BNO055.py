#!/usr/bin/python3

import board
import busio

import time
from time import strftime
import json

import adafruit_bno055

bno055 = adafruit_bno055.BNO055_I2C(busio.I2C(board.SCL, board.SDA))

config = json.load(open("config.json", "r"))
bno_config = config['bno055']

bno055.mode = bno_config['MODE']
#bno055.external_crystal = bno_config['EXTERNAL_CRYSTAL']
#bno055.use_external_crystal = bno_config['USE_EXTERNAL_CRYSTAL']

ACCELERATION_ENABLED = bno_config['ACCELERATION_ENABLED']
    #bno055.accel_bandwidth = bno_config['ACCELERATION_ACCEL_BANDWIDTH']
    #bno055.accel_mode = bno_config['ACCELERATION_ACCEL_MODE']
    #bno055.accel_range = bno_config['ACCELERATION_ACCEL_RANGE']

GYRO_ENABLED = bno_config['GYRO_ENABLED']
    #bno055.gyro_bandwidth = bno_config['GYRO_GYRO_BANDWIDTH']
    #bno055.gyro_mode = bno_config['GYRO_GYRO_MODE']
    #bno055.gyro_range = bno_config['GYRO_GYRO_RANGE']

MAGNET_ENABLED = bno_config['MAGNET_ENABLED']
    #bno055.magnet_mode = bno_config['MAGNET_MAGNET_MODE']
    #bno055.magnet_operation_mode = bno_config['MAGNET_MAGNET_OPERATION_MODE']
    #bno055.magnet_rate = bno_config['MAGNET_MAGNET_RATE']

TEMPERATURE_ENABLED = bno_config['TEMPERATURE_ENABLED']
EULER_ENABLED =  bno_config['EULER_ENABLED']
QUATERNION_ENABLED =  bno_config['QUATERNION_ENABLED']
LINEAR_ACCELEROMETER_ENABLED =  bno_config['LINEAR_ACCELEROMETER_ENABLED']
GRAVITY_ENABLED =  bno_config['GRAVITY_ENABLED']

# basically never change this
bno055.mode = adafruit_bno055.NDOF_FMC_OFF_MODE

'''
+------------------+-------+---------+------+----------+
| Mode             | Accel | Compass | Gyro | Absolute |
+==================+=======+=========+======+==========+
| CONFIG_MODE      |   -   |   -     |  -   |     -    |
+------------------+-------+---------+------+----------+
| ACCONLY_MODE     |   X   |   -     |  -   |     -    |
+------------------+-------+---------+------+----------+
| MAGONLY_MODE     |   -   |   X     |  -   |     -    |
+------------------+-------+---------+------+----------+
| GYRONLY_MODE     |   -   |   -     |  X   |     -    |
+------------------+-------+---------+------+----------+
| ACCMAG_MODE      |   X   |   X     |  -   |     -    |
+------------------+-------+---------+------+----------+
| ACCGYRO_MODE     |   X   |   -     |  X   |     -    |
+------------------+-------+---------+------+----------+
| MAGGYRO_MODE     |   -   |   X     |  X   |     -    |
+------------------+-------+---------+------+----------+
| AMG_MODE         |   X   |   X     |  X   |     -    |
+------------------+-------+---------+------+----------+
| IMUPLUS_MODE     |   X   |   -     |  X   |     -    |
+------------------+-------+---------+------+----------+
| COMPASS_MODE     |   X   |   X     |  -   |     X    |
+------------------+-------+---------+------+----------+
| M4G_MODE         |   X   |   X     |  -   |     -    |
+------------------+-------+---------+------+----------+
| NDOF_FMC_OFF_MODE|   X   |   X     |  X   |     X    |
+------------------+-------+---------+------+----------+
| NDOF_MODE        |   X   |   X     |  X   |     X    |
+------------------+-------+---------+------+----------+

bno055.accel_mode
    ACCEL_NORMAL_MODE = const(0x00)  # Default. For accel_mode property
    ACCEL_SUSPEND_MODE = const(0x20)
    ACCEL_LOWPOWER1_MODE = const(0x40)
    ACCEL_STANDBY_MODE = const(0x60)
    ACCEL_LOWPOWER2_MODE = const(0x80)
    ACCEL_DEEPSUSPEND_MODE = const(0xA0)

bno055.accel_range
    ACCEL_2G = const(0x00)  # For accel_range property
    ACCEL_4G = const(0x01)  # Default
    ACCEL_8G = const(0x02)
    ACCEL_16G = const(0x03)

bno055.accel_bandwidth
    ACCEL_7_81HZ = const(0x00)  # For accel_bandwidth property
    ACCEL_15_63HZ = const(0x04)
    ACCEL_31_25HZ = const(0x08)
    ACCEL_62_5HZ = const(0x0C)  # Default
    ACCEL_125HZ = const(0x10)
    ACCEL_250HZ = const(0x14)
    ACCEL_500HZ = const(0x18)
    ACCEL_1000HZ = const(0x1C)


bno055.gyro_mode
    GYRO_NORMAL_MODE = const(0x00)  # Default. For gyro_mode property
    GYRO_FASTPOWERUP_MODE = const(0x01)
    GYRO_DEEPSUSPEND_MODE = const(0x02)
    GYRO_SUSPEND_MODE = const(0x03)
    GYRO_ADVANCEDPOWERSAVE_MODE = const(0x04)

bno055.gyro_range
    GYRO_2000_DPS = const(0x00)  # Default. For gyro_range property
    GYRO_1000_DPS = const(0x01)
    GYRO_500_DPS = const(0x02)
    GYRO_250_DPS = const(0x03)
    GYRO_125_DPS = const(0x04)

bno055.gyro_bandwidth
    GYRO_523HZ = const(0x00)  # For gyro_bandwidth property
    GYRO_230HZ = const(0x08)
    GYRO_116HZ = const(0x10)
    GYRO_47HZ = const(0x18)
    GYRO_23HZ = const(0x20)
    GYRO_12HZ = const(0x28)
    GYRO_64HZ = const(0x30)
    GYRO_32HZ = const(0x38)  # Default


bno055.magnet_operation_mode
    MAGNET_LOWPOWER_MODE = const(0x00)  # For magnet_operation_mode property
    MAGNET_REGULAR_MODE = const(0x08)  # Default
    MAGNET_ENHANCEDREGULAR_MODE = const(0x10)
    MAGNET_ACCURACY_MODE = const(0x18)

bno055.magnet_mode
    MAGNET_NORMAL_MODE = const(0x00)  # for magnet_power_mode property
    MAGNET_SLEEP_MODE = const(0x20)
    MAGNET_SUSPEND_MODE = const(0x40)
    MAGNET_FORCEMODE_MODE = const(0x60)  # Default

bno055.magnet_rate
    MAGNET_2HZ = const(0x00)  # For magnet_rate property
    MAGNET_6HZ = const(0x01)
    MAGNET_8HZ = const(0x02)
    MAGNET_10HZ = const(0x03)
    MAGNET_15HZ = const(0x04)
    MAGNET_20HZ = const(0x05)  # Default
    MAGNET_25HZ = const(0x06)
    MAGNET_30HZ = const(0x07)

'''

def startup():
    # get the logfile location
    # log the component has started

    #if not bno055.begin():
    #    raise RuntimeError('Failed to initialize BNO055! Is the sensor connected?')

    print("component BNO055 started")
    # initialize for stats
    pass

def shutdown():
    # log the component has stopped
    # do disconnections and cleanups
    pass

def getData(bno):
    return json.dumps(bno, indent=4)

def main():
    startup()
    evt_id = 0

    while True:
        evt_id +=1
        bno = {}
        bno.update({"id": evt_id})

        t0 = strftime("%Y-%m-%d %H:%M:%S")
        bno.update({"t0": t0})

        t1 = time.perf_counter()
        bno.update({"t1": "{0:.4f}".format(t1)})

        bno.update({"d": None})

        # THE SENSORS ARE FACTORY TRIMMED TO REASONABLY TIGHT OFFSETS,
        # MEANING YOU CAN GET VALID DATA EVEN BEFORE THE CALIBRATION
        # PROCESS IS COMPLETE, BUT PARTICULARLY IN NDOF MODE YOU SHOULD
        # DISCARD DATA AS LONG AS THE SYSTEM CALIBRATION STATUS IS 0
        # IF YOU HAVE THE CHOICE.

        # Tuple containing sys, gyro, accel, and mag calibration data.
        bno.update({"sys_cal": bno055.calibration_status[0]})
        bno.update({"gyro_cal": bno055.calibration_status[1]})
        bno.update({"mag_cal": bno055.calibration_status[2]})
        bno.update({"accl_cal": bno055.calibration_status[3]})

        bno.update({"mode": bno055.mode})

        if ACCELERATION_ENABLED:
            # meters per second squared.
            accl = {}

            accl.update({"x": bno055.acceleration[0]})
            accl.update({"y": bno055.acceleration[1]})
            accl.update({"z": bno055.acceleration[2]})
            bno.update({"accl" : accl})

        if GYRO_ENABLED:
            # degrees per second.
            gyro = {}

            gyro.update({"x": bno055.gyro[0]})
            gyro.update({"y": bno055.gyro[1]})
            gyro.update({"z": bno055.gyro[2]})
            bno.update({"gyro" : gyro})

        if MAGNET_ENABLED:
            # microteslas.
            mag = {}

            mag.update({"x": bno055.magnetic[0]})
            mag.update({"y": bno055.magnetic[1]})
            mag.update({"z": bno055.magnetic[2]})
            bno.update({"mag" : mag})

        if TEMPERATURE_ENABLED:
            # degrees Celsius.
            temp = {}
            temp.update({"c": bno055.temperature})
            bno.update({"temp" : temp})

        if EULER_ENABLED:
            # euler - 3-tuple of orientation Euler angle values.
            euler = {}

            euler.update({"x": bno055.euler[0]})
            euler.update({"y": bno055.euler[1]})
            euler.update({"z": bno055.euler[2]})
            bno.update({"euler" : euler})

        if QUATERNION_ENABLED:
            # quaternion - 4-tuple of orientation quaternion values.
            quat = {}

            quat.update({"x": bno055.quaternion[0]})
            quat.update({"y": bno055.quaternion[1]})
            quat.update({"z": bno055.quaternion[2]})
            quat.update({"v": bno055.quaternion[3]})
            bno.update({"quat" : quat})

        if LINEAR_ACCELEROMETER_ENABLED:
            # linear acceleration meters per second squared.
            line = {}

            line.update({"x": bno055.linear_acceleration[0]})
            line.update({"y": bno055.linear_acceleration[1]})
            line.update({"z": bno055.linear_acceleration[2]})
            bno.update({"line" : line})

        if GRAVITY_ENABLED:
            # gravity - 3-tuple of X, Y, Z gravity acceleration values
            # (i.e. without the effect of linear acceleration) in
            # meters per second squared.
            grav = {}

            grav.update({"x": bno055.gravity[0]})
            grav.update({"y": bno055.gravity[1]})
            grav.update({"z": bno055.gravity[2]})
            bno.update({"grav" : grav})

        t2 = time.perf_counter()
        bno.update({"d": "{0:.4f}".format(t2 - t1)})

        print(getData(bno))

if __name__ == "__main__":
    main()


