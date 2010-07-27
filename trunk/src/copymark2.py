# Copymark2 v0.0.4: A simulation of real world file transfer performance
# Copyright (C) 2010  Guy Kisel
# Project hosted at http://code.google.com/p/copymark2/

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

__author__="kisel_g"
__date__ ="$May 25, 2010 3:30:10 PM$"

import osutil
import os
import platform
import datetime
import time

#store tuple pairs of file sizes and counts
calibrated_counts = {}

TEST_FILE_PATH = osutil.make_path('\\copymark_temp_files\\')
WRITE = 'S->T'
READ = 'T->S'
TEST_NAME = 'Copymark2 0.0.4'
CPU = platform.processor().replace(',', '')

#build system info string for logging purposes
sysinfo = str(platform.architecture()) + '\n' + str(platform.uname())
sysinfo_raw = []
sysinfo_raw.extend(platform.architecture())
sysinfo_raw.extend(platform.uname())
if os.name == 'nt':
    sysinfo += '\n' + str(platform.win32_ver())
    sysinfo_raw.extend(platform.win32_ver())
    import _winreg
    key = _winreg.OpenKey(_winreg.HKEY_LOCAL_MACHINE,
    'SOFTWARE\\Microsoft\Windows NT\\CurrentVersion')
    OS_VERSION = str(str(_winreg.QueryValueEx(key, 'ProductName')[0]) + ' ' + str(platform.win32_ver()[2]) + ' ' + str(platform.version())).replace(',', '')
else:
    startTime = time.time()
    sysinfo += '\n'
    OS_VERSION = ''
    import types
    if type(platform.mac_ver()) == types.ListType or \
    type(platform.mac_ver()) == types.TupleType:
        for item in platform.mac_ver():
            if type(item) == str:
                sysinfo += item
                sysinfo_raw.extend(item)
                OS_VERSION += item

def calibrate(file_size, source, target, start_count=None, calibration_script=None):
    """Calibrate a file count for a given file size."""
    global calibrated_counts

    if start_count == None:
        start_count = 1

    #if the size has already been calibrated
    if file_size in calibrated_counts:
        return (calibrated_counts[file_size], False)

    start = osutil.get_time()
    print '*' * 79
    print 'Beginning calibration for file size: ' + str(file_size) + ' bytes.'
    print '*' * 79

    if calibration_script == None:
        calibrated_count = default_calibration(file_size, start_count, source, target)
    else:
        calibrated_count = external_calibration(file_size, start_count, source, target, calibration_script)

    end = osutil.get_time()

    duration = end - start
    print '*' * 79
    print 'Completed calibration for file size: ' + str(file_size) + ' bytes at ' + str(calibrated_count) + ' files.'
    print 'Calibration took ' + str(round(duration, 1)) + ' seconds.'
    print '*' * 79

    calibrated_counts[file_size] = calibrated_count
    return (calibrated_count, True)

def external_calibration(file_size, start_count, source, target, script):
    """Use a user-supplied calibration script."""
    import subprocess
    print 'External calibration: ' + script + ' %d %d %s %s' % (file_size, start_count, source, target)
    p = subprocess.Popen(script + ' %d %d %s %s' % (file_size, start_count, source, target),
    stdin=subprocess.PIPE, stdout=subprocess.PIPE, shell=True)
    for line in p.stdout.readlines():
        print line.strip()
        if 'CALIBRATED_COUNT=' in line:
            return int(line.replace('CALIBRATED_COUNT=', ''))
    return int(p.stdout.readline())

def default_calibration(file_size, start_count, source, target):
    """Run the default calibration algorithm. Until writes and reads both take over 20 seconds, keep doubling the file count."""
    calibrated_count = start_count
    while True:
        print 'Write calibration trial. Size: ' + str(file_size) + ' Count: ' + str(calibrated_count)
        write_duration = test(file_size, calibrated_count, source, target, 'calibration', direction=WRITE, reuse=False)[0]
        print 'Read calibration trial. Size: ' + str(file_size) + ' Count: ' + str(calibrated_count)
        read_duration = test(file_size, calibrated_count, source, target, 'calibration', direction=READ, reuse=True)[0]
        if write_duration > 20 and read_duration > 20:
            print 'Done calibrating.'
            break
        else:
            print '/!\\ Doubling file count. /!\\'
            calibrated_count *= 2
    osutil.delete_dir(source + TEST_FILE_PATH)
    osutil.delete_dir(target + TEST_FILE_PATH)
    return calibrated_count

def test(file_size, file_count, source, target, fill_index=-1, fill=False, direction=None, reuse=False, verbose=False):
    """Run an individual size/count pair."""

    if fill:
        fill_string = '\\' + str(fill_index) + '\\' + str(file_size) + '_' + str(file_count) + '\\'
    else:
        fill_string = ''

    #file generation/reuse logic
    if direction == WRITE:
        file_path = source + TEST_FILE_PATH
        deletion_path = target + TEST_FILE_PATH + fill_string
    else:
        file_path = target + TEST_FILE_PATH + fill_string
        deletion_path = source + TEST_FILE_PATH
    if reuse:
        osutil.delete_dir(deletion_path)
        osutil.make_dir(deletion_path)
    else:
        #delete from both target and source
        osutil.delete_dir(file_path)
        osutil.make_dir(file_path)
        osutil.delete_dir(deletion_path)
        osutil.make_dir(deletion_path)
        osutil.generate_files(file_path, file_size, file_count)

    #remount drives
    osutil.remount(file_path)
    osutil.remount(deletion_path)

    if verbose:
        print 'Copying... ',

    #test window
    start = osutil.get_time()
    if direction == WRITE:
        success = osutil.copy_dir(source + TEST_FILE_PATH, target + TEST_FILE_PATH + fill_string)
    else:
        success = osutil.copy_dir(target + TEST_FILE_PATH + fill_string, source + TEST_FILE_PATH)
    end = osutil.get_time()

    duration = end - start

    if not os.path.isdir(osutil.make_path(target + TEST_FILE_PATH + fill_string)) or not success:
        #raise exception because transfer failed
        print 'ERROR: Destination folder not found. Transfer failed.'
        raise Exception()

    if verbose:
        total_size = file_size * file_count
        (printSize, units) = osutil.scale_bytes(total_size)
        scaled_speed, scaled_units = osutil.scale_bytes(total_size / duration)
        print 'Transfer complete: ' + str(round(scaled_speed, 1)) + ' ' + scaled_units + '/s over ' + str(round(duration, 1)) + ' seconds.'
        print 'Data transferred: ' + str(printSize) + ' ' + units

    return (duration, start, end)

def run_workload(workload, calibration_script, source, target, _calibrate, sweep, test_start_time, fill):
    """Run through a workload specified as a list of tuples. Tuples
    follow the format (file_size, file_count, calibrate, direction, trial) where calibrate
    is a Boolean."""
    results = []
    for i, workitem in enumerate(workload):
        file_size = workitem.file_size
        file_count = workitem.file_count
        direction = workitem.direction
        trial = workitem.trial
        fill_index = workitem.fill_index

        if _calibrate:
            if calibration_script == None:
                calibration_method = '20 second minimum'
            else:
                calibration_method = calibration_script
            file_count, files_generated = calibrate(file_size, source, target, file_count, calibration_script)
        else:
            calibration_method = 'not calibrated'

        #reads always happen after writes, so reuse if read
        #if not the first trial and not sweeping, the previous trial had the same workload, so reuse
        #if calibrate mode is on and files were just generated, reuse
        if direction == READ or (trial > 0 and not sweep) or (_calibrate and files_generated):
            reuse = True
        else:
            reuse = False

        print ''
        print '*' * 79
        print 'Test run ' + str(i+1) + ' of ' + str(len(workload)) + ': Direction = ' + direction + ', Trial = ' + str(trial)
        size, units = osutil.scale_bytes(file_size)
        print 'File size: ' + str(size) + ' ' + str(units) + ' x ' + str(file_count) + ' files'
        print '*' * 79
        duration, start, end = test(file_size, file_count, source, target, fill_index, fill, direction, reuse, verbose=True)
        time_elapsed = str(datetime.timedelta(seconds=int(osutil.get_time() - test_start_time))).replace(',',' ')
        print 'Time elapsed: ' + time_elapsed
        results.append(Result(source, target, file_size, file_count, direction, trial, fill_index, reuse, duration, start, end, time_elapsed, calibration_method))

    osutil.delete_dir(source + TEST_FILE_PATH)
    osutil.delete_dir(target + TEST_FILE_PATH)
    return results


class Result():
    def __init__(self, source, target, file_size, file_count, direction, trial, fill_index, reuse, duration, start, end, time_elapsed, calibration_method, notes=''):
        self.source = source
        self.target = target
        self.file_size = file_size
        self.file_count = file_count
        self.direction = direction
        self.trial = trial
        self.reuse = reuse
        self.duration = duration
        self.start = start
        self.end = end
        self.time_elapsed = time_elapsed
        self.notes = notes
        self.calibration_method = calibration_method
        self.fill_index = fill_index

def log_results(results, logfile):
    """Print results to a file in csv format."""
    date_struct = time.localtime()
    date = str(date_struct.tm_mon) + '/' + str(date_struct.tm_mday) + '/' + str(date_struct.tm_year)

    with open(logfile, 'w') as log:

        result_dict = {}

        #column names
        log.write('reading from, writing to, I/O direction, MiB/s, MB/s, total bytes, file size, file count, duration, start time, end time, trial, fill index, test, OS, CPU, start date, test duration, calibration method, notes\n')
        for result in results:

            result_tuple = (result.direction, result.file_size, result.file_count)
            if result_tuple not in result_dict:
                result_dict[result_tuple] = []

            if result.direction == WRITE:
                reading_from = result.source
                writing_to = result.target
                iodirection = 'S->T'
            else:
                reading_from = result.target
                writing_to = result.source
                iodirection = 'T->S'
            total_size = result.file_size * result.file_count
            MiBps = (float(total_size) / 1048576) / result.duration
            MBps = (float(total_size) / 1000000) / result.duration

            result_dict[result_tuple].append(MiBps)

            row = ''
            row += reading_from + ','
            row += writing_to + ','
            row += iodirection + ','
            row += str(MiBps) + ','
            row += str(MBps) + ','
            row += str(total_size) + ','
            row += str(result.file_size) + ','
            row += str(result.file_count) + ','
            row += str(result.duration) + ','
            row += str(result.start) + ','
            row += str(result.end) + ','
            row += str(result.trial) + ','
            row += str(result.fill_index) + ','
            row += TEST_NAME + ','
            row += OS_VERSION + ','
            row += CPU + ','
            row += date + ','
            row += str(result.time_elapsed) + ','
            row += str(result.calibration_method) + ','
            row += str(result.notes) + ','

            log.write(row + '\n')

        median_header = '\nMedians:\ndirection, size, count, median MiB/s, relative standard deviation\n'
        log.write(median_header)
        print median_header

        for key, value in sorted(result_dict.iteritems()):
            median_row = key[0] + ',' + str(key[1]) + ',' + str(key[2]) + ',' + str(osutil.median(value)) + ',' + str(relative_standard_deviation(value)) + '\n'
            log.write(median_row)
            print median_row

def relative_standard_deviation(data):
    import math
    if len(data) <= 1:
        return 0
    n = 0
    Sum = 0
    Sum_sqr = 0

    for x in data:
        n = n + 1
        Sum = Sum + x
        Sum_sqr = Sum_sqr + x*x

    mean = Sum/n
    variance = (Sum_sqr - Sum*mean)/(n - 1)
    standard_deviation = math.sqrt(variance)
    relative = (standard_deviation * 100) / mean
    return relative

def workload_size(workload_file, trials):
    total_size = 0
    for line in open(workload_file, 'r'):
        line_list = line.split()
        if len(line_list) != 3:
            #TODO: raise exception
            pass
        count = int(line_list[0])
        size = osutil.convertToBytes(float(line_list[1]), line_list[2])
        total_size += count * size
    total_size *= trials
    return total_size

def parse_workload(workload_file, trials, sweep, fill, source, target):
    """Convert workload file to a list of tuples in the format
    (file_size, file_count, direction, trial)
    that run_workload() can read."""
    workload = []
    dummy_list = []
    if fill:
        fill_cycles = int(osutil.get_disk_space(target) / workload_size(workload_file, trials))
    else:
        fill_cycles = 1
    for fill_index in xrange(fill_cycles):
        for line in open(workload_file, 'r'):
            line_list = line.split()
            if len(line_list) != 3:
                #TODO: raise exception
                pass
            count = int(line_list[0])
            size = osutil.convertToBytes(float(line_list[1]), line_list[2])

            if not sweep:
                #writes
                for i in xrange(0, trials):
                    workload.append(WorkItem(size, count, WRITE, i, fill_index))
                #reads
                for i in xrange(0, trials):
                    workload.append(WorkItem(size, count, READ, i, fill_index))
            else:
                dummy_list.append((size, count, None, None))

        if sweep:
            for i in xrange(0, trials):
                list = []
                for tuple in dummy_list:
                    list.append(WorkItem(tuple[0], tuple[1], WRITE, i, fill_index))
                    list.append(WorkItem(tuple[0], tuple[1], WRITE, i, fill_index))
                workload.extend(list)

    return workload

class WorkItem():
    def __init__(self, file_size, file_count, direction, trial, fill_index):
        self.file_size = file_size
        self.file_count = file_count
        self.direction = direction
        self.trial = trial
        self.fill_index = fill_index

def main(source, target, workload_file, calibrate, calibration_script, logfile, trials, sweep, fill):
    test_start_time = osutil.get_time()
    workload = parse_workload(workload_file, trials, sweep, fill, source, target)
    results = run_workload(workload, calibration_script, source, target, calibrate, sweep, test_start_time, fill)
    log_results(results, logfile)

def has_admin():
    """Return true if the script is running with admin rights."""

    import ctypes
    try:
     is_admin = os.getuid() == 0
    except AttributeError:
     is_admin = ctypes.windll.shell32.IsUserAnAdmin() != 0
    return is_admin

if __name__ == "__main__":
    import optparse
    usage = 'usage: %prog [options] <source dir> <target dir> <workload file>'
    parser = optparse.OptionParser(usage)
    parser.add_option('-c', '--calibrate', action='store_true', dest='calibrate', default=True, help='Automatically calibrate file counts. Defaults to True.')
    parser.add_option('-H', '--heuristic', action='store', type='string', dest='calibration_script', help='Specify an external calibration heuristic.')
    parser.add_option('-l', '--logfile', action='store', type='string', dest='logfile', default='log.csv', help='Specify a log file. Defaults to log.csv.')
    parser.add_option('-t', '--trials', action='store', type='int', dest='trials', default=1, help='Number of trials to run. Defaults to 1.')
    parser.add_option('-s', '--sweep', action='store_true', dest='sweep', default=False, help='Run full sweeps instead of running each file size <trials> times. Defaults to False.')
    parser.add_option('-f', '--fill', action='store_true', dest='fill', default=False, help='Drive fill mode - gradually fill a drive while benchmarking. Defaults to False.')
    (options, args) = parser.parse_args()
    if has_admin():
        try:
            if len(args) < 3:
                print 'Run "copymark2.py -h" for help.'
            else:
                main(args[0], args[1], args[2], options.calibrate, options.calibration_script, options.logfile, options.trials, options.sweep, options.fill)
        except WindowsError, e:
            if 'Error 740' in str(e):
                print 'Copymark must be run with admin rights. Exiting.'
    else:
        print 'Copymark must be run with admin rights. Exiting.'
        #os.system('runas /user:Administrator "python copymark2.py"') #TODO need to pass args

#    print 'Press Enter to exit...'
#    raw_input()