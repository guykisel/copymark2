# !/usr/bin/env python
# Copymark2 v0.0.9: A simulation of real world file transfer performance
# Copyright (C) 2011  Guy Kisel
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
import sys

#store tuple pairs of file sizes and counts
calibrated_counts = {}

#the path on each drive where test files are created
TEST_FILE_PATH = osutil.make_path('copymark_temp_files/')

#source to target
WRITE = 'S->T'

#target to source
READ = 'S<-T'

TEST_NAME = 'Copymark2 0.0.9'
CPU = platform.processor().replace(',', '')

#build system info string for logging purposes
sysinfo = str(platform.architecture()) + '\n' + str(platform.uname())
sysinfo_raw = []
sysinfo_raw.extend(platform.architecture())
sysinfo_raw.extend(platform.uname())
if os.name == 'nt':
    sysinfo += '\n' + str(platform.win32_ver())
    sysinfo_raw.extend(platform.win32_ver())
    try:
        #look up the windows version in the registry
        import _winreg
        key = _winreg.OpenKey(_winreg.HKEY_LOCAL_MACHINE,
        'SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion')
        OS_VERSION = str(str(_winreg.QueryValueEx(key, 'ProductName')[0]) + ' ' + \
        str(platform.win32_ver()[2]) + ' ' + str(platform.version())).replace(',', '')
    except WindowsError, e:
        print e
        OS_VERSION = 'unknown'
elif osutil.OS == 'mac':
    #if not windows, assume it's running on a mac
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
elif osutil.OS == 'posix':
    try:
        distname, version, id = platform.linux_distribution()
        OS_VERSION = str(distname) + ' ' + str(version) + ' ' + str(id)
    except AttributeError:
        distname, version, id = platform.dist()
        OS_VERSION = str(distname) + ' ' + str(version) + ' ' + str(id)

print 'OS: ' + str(OS_VERSION)

def calibrate(file_size, source, target, start_count=None, calibration_script=None):
    """Calibrate a file count for a given file size."""
    global calibrated_counts

    if not start_count:
        start_count = 1

    #if the size has already been calibrated
    if file_size in calibrated_counts:
        return calibrated_counts[file_size], False

    start = osutil.get_time()
    print '*' * 79
    print 'Beginning calibration for file size: ' + str(file_size) + ' bytes.'
    print '*' * 79

    if not calibration_script:
        calibrated_count = default_calibration(file_size, start_count, source, target)
        files_generated = False
    else:
        calibrated_count, files_generated = external_calibration(file_size, start_count, source, target, calibration_script)

    end = osutil.get_time()

    duration = end - start
    print '*' * 79
    print 'Completed calibration for file size: ' + str(file_size) + ' bytes at ' + str(calibrated_count) + ' files.'
    print 'Calibration took ' + str(round(duration, 1)) + ' seconds.'
    print '*' * 79

    calibrated_counts[file_size] = calibrated_count
    return calibrated_count, files_generated

def external_calibration(file_size, start_count, source, target, script):
    """Use a user-supplied calibration script."""
    import subprocess
    if script.endswith('.py'):
        script = 'python ' + script
    print 'External calibration: ' + script + ' %d %d %s %s' % (file_size, start_count, source, target)
    p = subprocess.Popen(script + ' %d %d %s %s' % (file_size, start_count, source, target),
    stdin=subprocess.PIPE, stdout=subprocess.PIPE, shell=True)
    calibrated_count = None
    files_generated = False
    for line in p.stdout.readlines():
        print line.strip()
        if 'CALIBRATED_COUNT=' in line:
            calibrated_count = int(line.replace('CALIBRATED_COUNT=', ''))
        elif 'FILES_GENERATED=' in line:
            files_generated = bool(line.replace('FILES_GENERATED=', ''))
    try:
        return calibrated_count, files_generated
    except ValueError:
        sys.exit('External calibration did not return a calibrated value.')

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
            print '/!/ Doubling file count. /!/'
            calibrated_count *= 2
    osutil.delete_dir(os.path.join(source, TEST_FILE_PATH))
    osutil.delete_dir(os.path.join(target, TEST_FILE_PATH))
    return calibrated_count

def test(file_size, file_count, source, target, fill_index=-1, fill=False, direction=None, reuse=False, verbose=False, shell_copy=True):
    """Run an individual size/count pair."""

    if fill:
        fill_string = os.path.join(str(fill_index),str(file_size) + '_' + str(file_count))
    else:
        fill_string = ''
    #file generation/reuse logic
    if direction == WRITE:
        file_path = os.path.join(source, TEST_FILE_PATH)
        deletion_path = os.path.join(target, TEST_FILE_PATH, fill_string)
    else:
        file_path = os.path.join(target, TEST_FILE_PATH, fill_string)
        deletion_path = os.path.join(source, TEST_FILE_PATH)
    osutil.delete_dir(deletion_path)
    if not osutil.OS == 'mac':
        osutil.make_dir(deletion_path)
    if not reuse:
        #delete from both target and source
        osutil.delete_dir(file_path)
        osutil.make_dir(file_path)
        print 'Generating files in: ' + file_path
        osutil.generate_files(file_path, file_size, file_count)

    #remount drives to clear the file cache
    osutil.remount(file_path, verbose=True, confirm_unmount=True)
    osutil.remount(deletion_path, verbose=True, confirm_unmount=True)
    osutil.clear_file_cache()
    time.sleep(1)

    source_path = os.path.join(source, TEST_FILE_PATH)
    target_path = os.path.join(target, TEST_FILE_PATH, fill_string)
    if osutil.OS == 'mac':
        if direction == WRITE:
            target_path = target
        else:
            source_path = source

    #wait for disks to settle
    osutil.wait_for_dir_idle([target, source])

    if verbose:
        print 'Copying... '

    #test window
    start = osutil.get_time()
    if direction == WRITE:
        success = osutil.copy_dir(source_path, target_path, shell_copy=shell_copy, quiet=False)
    else:
        success = osutil.copy_dir(target_path, source_path, shell_copy=shell_copy, quiet=False)
    end = osutil.get_time()
    #end of test window

    duration = end - start

    counter = 0
    while True:
        if not os.path.isdir(osutil.make_path(deletion_path) + '/'):
            #raise exception because transfer failed
            print 'ERROR: Destination folder(' + str(deletion_path) + ') not found. Transfer failed.'
        elif not success:
            print 'ERROR: File copy function returned False. Transfer failed.'
        else:
            break
        counter += 1
        if counter > 5:
            raise Exception('File transfer failed.')
        time.sleep(5)

    print 'File transfer call returned. Waiting for disk activity to stop...'
    #wait for disks to settle
    last_activity = osutil.wait_for_dir_idle([target, source])
    true_duration = last_activity - start

    #print out some quick stats
    if verbose:
        total_size = file_size * file_count
        (printSize, units) = osutil.scale_bytes(total_size)
        scaled_speed, scaled_units = osutil.scale_bytes(total_size / duration)
        scaled_true_speed, scaled_true_units = osutil.scale_bytes(total_size / true_duration)
        print 'Perceived stats: ' + str(round(scaled_speed, 1)) + ' ' + scaled_units + '/s over ' + str(round(duration, 1)) + ' seconds.'
        print 'True stats: ' + str(round(scaled_true_speed, 1)) + ' ' + scaled_true_units + '/s over ' + str(round(true_duration, 1)) + ' seconds.'
        print 'Data transferred: ' + str(printSize) + ' ' + units

    return duration, start, end, true_duration

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
            if not calibration_script:
                calibration_method = '20 second minimum'
            else:
                calibration_method = calibration_script
            file_count, files_generated = calibrate(file_size, source, target, file_count, calibration_script)
        else:
            calibration_method = 'not calibrated'

        #writes always happen after reads, so reuse if write
        #if not the first trial and not sweeping, the previous trial had the same workload, so reuse
        #if calibrate mode is on and files were just generated, reuse
        if (direction == WRITE or (trial > 0 and not sweep) or (_calibrate and files_generated)):
            reuse = True
        else:
            reuse = False

        print ''
        print '*' * 79
        print 'Test run ' + str(i+1) + ' of ' + str(len(workload)) + ': Direction = ' + direction + ', Trial = ' + str(trial) + ', Reuse = ' + str(reuse)
        size, units = osutil.scale_bytes(file_size)
        total_size, total_units = osutil.scale_bytes(file_size * file_count)
        print 'File size: ' + str(size) + ' ' + str(units) + ' x ' + str(file_count) + ' files (' + str(total_size) + ' ' + str(total_units) + ' total)'
        print '*' * 79
        duration, start, end, true_duration = test(file_size, file_count, source, target, fill_index, fill, direction, reuse, verbose=True)
        time_elapsed = str(datetime.timedelta(seconds=int(osutil.get_time() - test_start_time))).replace(',',' ')
        print 'Time elapsed: ' + time_elapsed
        results.append(Result(source, target, file_size, file_count, direction, trial, fill_index, reuse, duration, start, end, time_elapsed, calibration_method, true_duration))

    osutil.delete_dir(source + TEST_FILE_PATH)
    osutil.delete_dir(target + TEST_FILE_PATH)
    return results


class Result(object):
    def __init__(self, source, target, file_size, file_count, direction, trial, fill_index, reuse, duration, start, end, time_elapsed, calibration_method, true_duration, notes=''):
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
        self.true_duration = true_duration

def log_results(results, logfile, calibrated_workload_filename):
    """Print results to a file in csv format."""
    date_struct = time.localtime()
    date = str(date_struct.tm_mon) + '/' + str(date_struct.tm_mday) + '/' + str(date_struct.tm_year)

    log = open(logfile, 'w')

    result_dict = {}

    #column names
    log.write('reading from, writing to, I/O direction, MiB/s, MB/s, total bytes, file size, file count, duration, true_duration, true_MiB/s, start time, end time, trial, fill index, test, OS, CPU, start date, test duration, calibration method, notes\n')
    for result in results:

        result_tuple = (result.direction, result.file_size, result.file_count)
        if result_tuple not in result_dict:
            result_dict[result_tuple] = []

        if result.direction == WRITE:
            reading_from = result.source
            writing_to = result.target
        else:
            reading_from = result.target
            writing_to = result.source
        total_size = result.file_size * result.file_count
        MiBps = (float(total_size) / 1048576) / result.duration
        MBps = (float(total_size) / 1000000) / result.duration
        trueMiBps = (float(total_size) / 1048576) / result.true_duration
        result_dict[result_tuple].append((MiBps, result.start))

        row = ''
        row += reading_from + ','
        row += writing_to + ','
        row += result.direction + ','
        row += str(MiBps) + ','
        row += str(MBps) + ','
        row += str(total_size) + ','
        row += str(result.file_size) + ','
        row += str(result.file_count) + ','
        row += str(result.duration) + ','
        row += str(result.true_duration) + ','
        row += str(trueMiBps) + ','
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

    if results[0].calibration_method != 'not calibrated':
        calibrated_workload = open(calibrated_workload_filename, 'w')

    keys = result_dict.keys()
    for key in sorted(keys, key=lambda k: float(result_dict[k][0][1])):
        values = [tuple[0] for tuple in result_dict[key]]
        median_row = key[0] + ',' + str(key[1]) + ',' + str(key[2]) + ',' + str(osutil.median(values)) + ',' + str(relative_standard_deviation(values)) + '\n'
        log.write(median_row)
        if key[0] == WRITE:
            (size, units) = osutil.scale_bytes(key[1])
            workload_row = str(key[2]) + ' ' + str(size) + ' ' + str(units) + '\n'
            if results[0].calibration_method != 'not calibrated':
                calibrated_workload.write(workload_row)
        print median_row

    print 'Test completed at ' + time.asctime()

def relative_standard_deviation(data):
    import math
    if len(data) <= 1:
        return 0
    n = 0
    Sum = 0
    Sum_sqr = 0

    for x in data:
        n += 1
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
            print 'Invalid workload entry: ' + str(line)
            sys.exit()
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
                print 'Invalid workload entry: ' + str(line)
                sys.exit()
            count = int(line_list[0])
            size = osutil.convertToBytes(float(line_list[1]), line_list[2])

            if not sweep:
                #writes
                for i in xrange(0, trials):
                    workload.append(WorkItem(size, count, READ, i, fill_index))
                #reads
                for i in xrange(0, trials):
                    workload.append(WorkItem(size, count, WRITE, i, fill_index))
            else:
                dummy_list.append((size, count, None, None))

        if sweep:
            for i in xrange(0, trials):
                list = []
                for tuple in dummy_list:
                    list.append(WorkItem(tuple[0], tuple[1], READ, i, fill_index))
                    list.append(WorkItem(tuple[0], tuple[1], WRITE, i, fill_index))
                workload.extend(list)

    return workload

class WorkItem(object):
    def __init__(self, file_size, file_count, direction, trial, fill_index):
        self.file_size = file_size
        self.file_count = file_count
        self.direction = direction
        self.trial = trial
        self.fill_index = fill_index

def main(source, target, workload_file, calibrate, calibration_script, logfile, trials, sweep, fill):
    if not source.endswith('\\') or source.endswith('/'):
        source = os.path.normpath(source + '/').replace('\\ ', ' ')
    if not target.endswith('\\') or target.endswith('/'):
        target = os.path.normpath(target + '/').replace('\\ ', ' ')
    if sweep:
        print 'Sweep mode is on.'
    osutil.restart_explorer()
    time.sleep(5)
    test_start_time = osutil.get_time()
    workload = parse_workload(workload_file, trials, sweep, fill, source, target)
    results = run_workload(workload, calibration_script, source, target, calibrate, sweep, test_start_time, fill)
    calibrated_workload_filename = os.path.splitext(workload_file)[0] + '_calibrated' + os.path.splitext(workload_file)[1]
    log_results(results, logfile, calibrated_workload_filename)

def has_admin():
    """Return true if the script is running with admin rights."""
    try:
        import ctypes
    except ImportError:
        return True
    try:
        is_admin = os.getuid() == 0
    except AttributeError:
        is_admin = ctypes.windll.shell32.IsUserAnAdmin() != 0
    return is_admin

if __name__ == "__main__":
    import sys
    print 'Python version = ' + str(sys.version)
    import optparse
    import osutil
    if osutil.OS == 'windows':
        try:
            import wmi
        except ImportError:
            print 'Copymark requires the Python WMI module in Windows. http://timgolden.me.uk/python/wmi/index.html'
            sys.exit()
    usage = 'usage: %prog [options] <source dir> <target dir> <workload file>'
    parser = optparse.OptionParser(usage)
    parser.add_option('-c', '--calibrate', action='store_true', dest='calibrate', default=False, help='Automatically calibrate file counts. Defaults to False.')
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
                if options.calibration_script:
                    options.calibrate = True
                main(args[0], args[1], args[2], options.calibrate, options.calibration_script, options.logfile, options.trials, options.sweep, options.fill)
        except OSError, e:
            if 'Error 740' in str(e):
                print 'Copymark must be run with admin rights. Exiting.'
                sys.exit()
            else:
                raise
    else:
        print 'Copymark must be run with admin rights. Exiting.'
        sys.exit()