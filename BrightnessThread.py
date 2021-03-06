import time
import threading
import TSL2561
import Settings
import logging
import sys

log = logging.getLogger('root')
# log.setLevel(logging.DEBUG)
#
# stream = logging.StreamHandler(sys.stdout)
# stream.setLevel(logging.DEBUG)
#
# formatter = logging.Formatter('[%(asctime)s] %(levelname)8s %(module)15s: %(message)s')
# stream.setFormatter(formatter)
#
# log.addHandler(stream)

LOOP_TIME = float(0.1)


class BrightnessThread(threading.Thread):
    def __init__(self, settings):
        threading.Thread.__init__(self)
        self.controlObjects = []
        self.stopping = False

        self.sensor = TSL2561.TSL2561()
        self.sensor.setGain(1)

        # self.settings = Settings.Settings()
        self.settings = settings

        self.currentLevel = 0
        self.manualTimeout = 0

        self.readings = [15] * 10  # average over the last 10 readings

    def registerControlObject(self, object):
        self.controlObjects.append(object)

    def stop(self):
        self.stopping = True

    def maxBrightness(self):
        self.setBrightness(self.settings.getInt('max_brightness'))

    def setBrightness(self, level):
        self.manualTimeout = self.settings.getInt('brightness_timeout') * (1 / LOOP_TIME)
        self.currentLevel = level
        self.updateBrightness()

    def updateBrightness(self):
        for obj in self.controlObjects:
            obj.setBrightness(self.currentLevel)

    def run(self):
        maxBright = self.settings.getInt('max_brightness')
        minBright = self.settings.getInt('min_brightness')

        while (not self.stopping):
            time.sleep(LOOP_TIME)

            # We set the brightness manually, so just count down until we can resume auto-brightness
            if (self.manualTimeout > 0):
                self.manualTimeout = -1
                continue

            reading = float(self.sensor.readFull())

            # if(reading>100):
            #   reading = 100 # Seems like a sensible max for the IR sensor, can go into the 10's of thousands

            #percentage = reading/100
            #newLevel = int(percentage * maxBright)

            newLevel = int(reading / 333.33333333333333)

            if (newLevel > maxBright):
                newLevel = maxBright
            if (newLevel < minBright):
                newLevel = minBright

            self.readings.pop(0)
            self.readings.append(newLevel)

            avgLevel = int(sum(self.readings) / float(len(self.readings)))

            levelDiff = abs(self.currentLevel - avgLevel)

            #log.debug("Reading: %s, Percentage: %s, NewLevel: %s, AvgLevel: %s, Diff: %s" % (reading,percentage,newLevel,avgLevel,levelDiff))
            #log.debug("Reading: %s, NewLevel: %s, AvgLevel: %s, Diff: %s" % (reading,newLevel,avgLevel,levelDiff))

            if (levelDiff >= 2):
                #log.debug("Updating brightness to %s" % (avgLevel))
                self.currentLevel = avgLevel
                self.updateBrightness()

        self.setBrightness(0)

