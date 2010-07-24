# To change this template, choose Tools | Templates
# and open the template in the editor.

__author__="kisel_g"
__date__ ="$Jun 11, 2010 3:46:29 PM$"

import sys
import copymark2
import math

MIN_DURATION = 20
MAX_DURATION = 30

def larger(num1, num2):
    if num1 >= num2:
        return num1
    return num2

def smaller(num1, num2):
    if num1 <= num2:
        return num1
    return num2

if __name__ == "__main__":
    file_size = int(sys.argv[1])
    start_count = int(sys.argv[2])
    source = str(sys.argv[3]).strip()
    target = str(sys.argv[4]).strip()

calibrated_count = start_count
cycles = 0
#initial test runs
write_duration = copymark2.test(file_size, calibrated_count, source, target, direction=copymark2.WRITE, reuse=False, verbose=True)[0]
read_duration = copymark2.test(file_size, calibrated_count, source, target, direction=copymark2.READ, reuse=True, verbose=True)[0]

done = False
while True:
    duration = smaller(write_duration, read_duration)
    #if the duration is under one second, multiply the file count by MIN_DURATION
    if duration < 1:
        print 'Duration under 1 second, multiplying by MIN_DURATION.'
        calibrated_count *= MIN_DURATION
    #else, if the duration is under MIN_DURATION, multiply it by the ratio of MIN_DURATION to the duration
    elif duration < MIN_DURATION:
        count = calibrated_count
        print 'Duration under ' + str(MIN_DURATION) + ' seconds, multiplying by ratio.'
        calibrated_count *= (MIN_DURATION / duration) * 1.1
        calibrated_count = int(math.ceil(calibrated_count))
        if calibrated_count == count:
            count += 1
        cycles += 1
    #else, if the duration is over MAX_DURATION, multiply it by the ratio of MAX_DURATION to the duration
    elif duration > MAX_DURATION:
        if cycles < 4 and not calibrated_count == 1:
            count = calibrated_count
            print 'Duration over ' + str(MAX_DURATION) + ' seconds, multiplying by ratio.'
            calibrated_count *= (MAX_DURATION / duration) * .95
            calibrated_count = int(math.ceil(calibrated_count))
            if calibrated_count == count:
                done = True
            cycles += 1
        else:
            done = True
    elif (duration > MIN_DURATION and duration < MAX_DURATION) or done:
        print 'Done.'
        break
    print 'New count: ' + str(calibrated_count) + ' files.'
    write_duration = copymark2.test(file_size, calibrated_count, source, target, direction=copymark2.WRITE, reuse=False, verbose=True)[0]
    read_duration = copymark2.test(file_size, calibrated_count, source, target, direction=copymark2.READ, reuse=True, verbose=True)[0]

print 'CALIBRATED_COUNT=' + str(calibrated_count)