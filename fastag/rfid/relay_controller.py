import logging
import time

try:
    import RPi.GPIO as GPIO
    GPIO_AVAILABLE = True
except ImportError:
    GPIO_AVAILABLE = False

class RelayController:
    def __init__(self):
        self.logger = logging.getLogger('RelayController')
        self.pins = [26, 20, 21]  # CH1, CH2, CH3
        self.logger.info("Initializing GPIO for relay control...")
        self.init_gpio()
        # Safety measure: ensure all relays are OFF on startup
        self.turn_off_all()
        self.logger.info("🔌 Safety check: All relays confirmed OFF on startup")
    
    def init_gpio(self):
        if not GPIO_AVAILABLE:
            self.logger.warning("GPIO is not available, skipping GPIO initialization.")
            return
        try:
            self.logger.info("Setting up GPIO mode (BCM)...")
            GPIO.setmode(GPIO.BCM)
            self.logger.info("Configuring relay pins (Active-Low, HIGH=OFF, LOW=ON)...")
            for pin in self.pins:
                GPIO.setup(pin, GPIO.OUT)
                GPIO.output(pin, GPIO.HIGH)  # Set to OFF state (HIGH for active-low)
            self.logger.info("✓ GPIO initialized successfully (Active-Low configuration)")
        except Exception as e:
            self.logger.error(f"✗ GPIO initialization error: {str(e)}")
    
    def turn_on(self, relay_number):
        if not GPIO_AVAILABLE:
            self.logger.warning("GPIO is not available, cannot turn on relay.")
            return False
        try:
            if 1 <= relay_number <= 3:
                pin = self.pins[relay_number - 1]
                self.logger.info(f"Turning ON relay {relay_number} (GPIO pin {pin})...")
                GPIO.output(pin, GPIO.LOW)  # LOW for active-low relays (turns ON)
                self.logger.info(f"✓ Relay {relay_number} turned ON")
                return True
            else:
                self.logger.error(f"✗ Invalid relay number: {relay_number}")
                return False
        except Exception as e:
            self.logger.error(f"✗ Error turning on relay {relay_number}: {str(e)}")
            return False
    
    def turn_off(self, relay_number):
        if not GPIO_AVAILABLE:
            self.logger.warning("GPIO is not available, cannot turn off relay.")
            return False
        try:
            if 1 <= relay_number <= 3:
                pin = self.pins[relay_number - 1]
                self.logger.info(f"Turning OFF relay {relay_number} (GPIO pin {pin})...")
                GPIO.output(pin, GPIO.HIGH)  # HIGH for active-low relays (turns OFF)
                self.logger.info(f"✓ Relay {relay_number} turned OFF")
                return True
            else:
                self.logger.error(f"✗ Invalid relay number: {relay_number}")
                return False
        except Exception as e:
            self.logger.error(f"✗ Error turning off relay {relay_number}: {str(e)}")
            return False
    
    def turn_off_all(self):
        if not GPIO_AVAILABLE:
            self.logger.warning("GPIO is not available, cannot turn off all relays.")
            return
        try:
            self.logger.info("Turning OFF all relays...")
            for pin in self.pins:
                GPIO.output(pin, GPIO.HIGH)  # HIGH for active-low relays (turns OFF)
            self.logger.info("✓ All relays turned OFF")
        except Exception as e:
            self.logger.error(f"✗ Error turning off all relays: {str(e)}")
    
    def cleanup(self):
        if not GPIO_AVAILABLE:
            self.logger.warning("GPIO is not available, skipping GPIO cleanup.")
            return
        try:
            self.logger.info("Cleaning up GPIO...")
            self.turn_off_all()
            GPIO.cleanup()
            self.logger.info("✓ GPIO cleanup completed")
        except Exception as e:
            self.logger.error(f"✗ GPIO cleanup error: {str(e)}") 