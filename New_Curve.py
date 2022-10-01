#Run a single lap and return the maximium number of features to be classified.

import RPi.GPIO as GPIO # GPIO = Global Pin Input Output
import time
import board
import adafruit_bno055 # Our Euler angle and accelerometer
import busio
import numpy as np

i2c = busio.I2C(board.SCL, board.SDA) # Activating the pins on the Pi for Tx/Rx data from an I2C sensor.
sensor = adafruit_bno055.BNO055_I2C(i2c) # Activating this protocol on the sensor board.
motor = 13 #This was a PWM pin on the Pi. This special pin was able to output a PWM value to the DRV8871 DC Drive.
# Below is the first method. This was to set up the pins on the Pi.
def setup():
    global pwm # PWM for sending those specific values to Pin 13 for the DC Driver.
    GPIO.setmode(GPIO.BCM) # 'BCM' was used if you're using only one Pi. If you use 'BOARD', it will change the values of the pins!
    GPIO.setup(motor, GPIO.OUT) # Set the motor as an output, as RPi pins can be set either/or Input or Output
    GPIO.output(motor, GPIO.LOW) # Don't need the dang motor running immediately at startup! Set this to LOW = 0 VDC.
    pwm = GPIO.PWM(motor, 100) # Utilizing the PWM library. Define the pin you're using and the range of speed it has.
    pwm.start(0) # We want the starting point to be 0! 0 = OFF or LOW. 
    GPIO.setwarnings(False) #This was an odd one. Got some interesting error messages, so we use this to turn those off. Do you need it? I don't know.
