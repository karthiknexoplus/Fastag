import RPi.GPIO as GPIO
import time

# Use BCM numbering
GPIO.setmode(GPIO.BCM)

# Define relay pins (BCM numbers)
RELAY_PINS = [26, 20, 21]  # CH1, CH2, CH3

# Set up pins as outputs and turn relays off (active low)
for pin in RELAY_PINS:
    GPIO.setup(pin, GPIO.OUT)
    GPIO.output(pin, GPIO.HIGH)

try:
    for i, pin in enumerate(RELAY_PINS):
        print(f"Turning ON Relay {i+1} (GPIO {pin})")
        GPIO.output(pin, GPIO.LOW)
        time.sleep(2)
        print(f"Turning OFF Relay {i+1} (GPIO {pin})")
        GPIO.output(pin, GPIO.HIGH)
        time.sleep(1)
finally:
    GPIO.cleanup()
    print("GPIO cleanup done.") 