# To change this template, choose Tools | Templates
# and open the template in the editor.

__author__="kisel_g"
__date__ ="$Jun 11, 2010 3:46:29 PM$"

import sys
import copymark2
import math
import os

MIN_DURATION = 20
MAX_DURATION = 30

def larger(num1, num2):
    """Return the larger of two values."""
    if num1 >= num2:
        return num1
    return num2

def smaller(num1, num2):
    """Return the smaller of two values."""
    if num1 <= num2:
        return num1
    return num2

if __name__ == "__main__":
    #file size is in bytes
    file_size = int(sys.argv[1])
    start_count = int(sys.argv[2])
    source = str(sys.argv[3]).strip()
    target = str(sys.argv[4]).strip()

    log = open('smart_log.txt', 'w')

    calibrated_count = start_count
    cycles = 0
    count = None
    log.write('Running initial tests.\n')
    #initial test runs
    read_duration = copymark2.test(file_size, calibrated_count, source, target, 'calibration', direction=copymark2.READ, reuse=False, verbose=True)[0]
    write_duration = copymark2.test(file_size, calibrated_count, source, target, 'calibration', direction=copymark2.WRITE, reuse=True, verbose=True)[0]
    
    done = False
    while True:
        log.write('Last read duration = ' + str(read_duration) + '\n')
        log.write('Last write duration = ' + str(write_duration) + '\n')
        log.flush()
        os.fsync(log.fileno())
        #calibrate based on the smaller of the two durations
        duration = smaller(write_duration, read_duration)
        #if the duration is under one second, multiply the file count by MIN_DURATION
        if duration < 1:
            print 'Duration under 1 second, multiplying by MIN_DURATION.'
            log.write('Duration under 1 second, multiplying by MIN_DURATION.\n')
            calibrated_count *= MIN_DURATION
        #else, if the duration is under MIN_DURATION, multiply it by the ratio of MIN_DURATION to the duration
        elif duration < MIN_DURATION:
            count = calibrated_count
            print 'Duration under ' + str(MIN_DURATION) + ' seconds, multiplying by ratio.'
            log.write('Duration under ' + str(MIN_DURATION) + ' seconds, multiplying by ratio.\n')
            calibrated_count *= (MIN_DURATION / duration) * 1.1
            calibrated_count = int(math.ceil(calibrated_count))
            if calibrated_count == count:
                calibrated_count += 1
            cycles += 1
        #else, if the duration is over MAX_DURATION, multiply it by the ratio of MAX_DURATION to the duration
        elif duration > MAX_DURATION:
            if cycles < 4 and not calibrated_count == 1:
                count = calibrated_count
                print 'Duration over ' + str(MAX_DURATION) + ' seconds, multiplying by ratio.'
                log.write('Duration over ' + str(MAX_DURATION) + ' seconds, multiplying by ratio.\n')
                calibrated_count *= (MAX_DURATION / duration) * .95
                calibrated_count = int(math.ceil(calibrated_count))
                if calibrated_count == count:
                    done = True
                cycles += 1
            else:
                done = True
        #if the duration is within the bounds or the earlier checks decided calibration is done, end the loop
        if (duration > MIN_DURATION and duration < MAX_DURATION) or done:
            print 'Done.'
            log.write('Done.\n')
            break
        print 'New count: ' + str(calibrated_count) + ' files.'
        if count:
            log.write('Previous count: ' + str(count) + ' files.\n')
        log.write('New count: ' + str(calibrated_count) + ' files.\n')
        log.write('Cycle: ' + str(cycles) + '\n')
        log.flush()
        os.fsync(log.fileno())

        #test again
        read_duration = copymark2.test(file_size, calibrated_count, source, target, 'calibration', direction=copymark2.READ, reuse=False, verbose=True)[0]
        write_duration = copymark2.test(file_size, calibrated_count, source, target, 'calibration', direction=copymark2.WRITE, reuse=True, verbose=True)[0]

    print 'CALIBRATED_COUNT=' + str(calibrated_count)
    #smart.py leaves the test files behind, so it's safe for copymark2 to reuse them
    print 'FILES_GENERATED=True'