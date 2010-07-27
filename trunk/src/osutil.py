# To change this template, choose Tools | Templates
# and open the template in the editor.

__author__="Kisel_g"
__date__ ="$Mar 10, 2010 9:52:47 AM$"

import os
import subprocess
import sys
import time
import threading
import re
import platform

filesystem_lock = threading.RLock()

if os.name == 'nt':
    try:
        from win32com.shell import shell, shellcon
    except ImportError:
        print 'pywin32 not installed'
        pass
else:
    startTime = time.time()

try:
    import wmi
    c = wmi.WMI()
except ImportError:
    print 'WMI not installed'
    pass

class filesystemLock():
    def __init__(self, f):
        self.f = f

    def __call__(self, *args, **kwargs):
        filesystem_lock.acquire()
        return_value = self.f(*args, **kwargs)
        filesystem_lock.release()
        return return_value

def windows_version():
    if sys.platform == 'win32':
        import _winreg
        key = _winreg.OpenKey(_winreg.HKEY_LOCAL_MACHINE,
        'SOFTWARE\\Microsoft\Windows NT\\CurrentVersion')
        os_version = str(str(_winreg.QueryValueEx(key, 'ProductName')[0]) + ' ' + str(platform.win32_ver()[2]) + ' ' + str(platform.version())).replace(',', '')
        return os_version
    else:
        return None

def remount(dir, verbose=False):
    if os.name == 'nt':
        drive_letter = get_drive_letter(dir)
        if verbose:
            print 'Remounting ' + drive_letter + ' (dir=' + dir + ')...',
        drive_letter = drive_letter.replace(':', '').replace('/', '').replace('\\', '')
        output = diskpart(['select volume ' + drive_letter, 'remove', 'assign letter=' + drive_letter])
        if verbose:
            for line in output:
                if 'successfully assigned' in line:
                    print 'success.'
                    return
            print 'unable to remount.'

def get_drive_letter(dir):
    drive_letter = os.path.dirname(dir)
    while drive_letter != os.path.dirname(drive_letter):
        drive_letter = os.path.dirname(drive_letter)
    return drive_letter

def median(list):
    sorted_list = sorted(list)
    if len(list) < 0:
        raise EmptyListError
    medianIndex = len(list) / 2
    if len(list) % 2 != 0:
        return sorted_list[medianIndex]
    else:
        return (sorted_list[medianIndex] + sorted_list[medianIndex - 1]) / 2

def get_disk_space(path):
    if os.name == 'nt':
        import win32api
        tuple = win32api.GetDiskFreeSpace(make_path(path))
        return tuple[0] * tuple[1] * tuple[2]
    elif os.name == 'posix':
        os.system('df ' + make_path(path) + ' > ' + make_path(path, \
                                                              'dirsize.txt'))
        dir = open(make_path(path, 'dirsize.txt'), 'r')
        dir.readline()
        return dir.readline().split(' ')[3]

def delay(seconds, verbose=False):
    seconds = int(seconds)
    if verbose:
        print 'Pausing for ' + str(seconds) + ' second(s): '
    for i in range(seconds):
        if verbose:
            print str((seconds - 1) - i) + '\r',
        time.sleep(1)
    if os.name == 'nt' and verbose:
        sys.stdout.write('\b\n')

def disable_autorun():
    import _winreg
    key = _winreg.OpenKey(_winreg.HKEY_LOCAL_MACHINE,
    'Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\Explorer')
    #return _winreg.QueryValueEx(key, 'ProductName')[0]:
    _winreg.SetValueEx(key, 'NoDriveTypeAutoRun', 0, _winreg.REG_DWORD, 0xFF)

def get_time():
    global startTime
    if os.name == 'nt':
        return time.clock()
    elif os.name == 'posix':
        return time.time() - startTime

def print80Stars():
    print('*' * 79)

def convertToBytes(size, units):
    size = float(size)
    if units == 'KiB':
        size *= 1024
    elif units == 'MiB':
        size *= 1024 * 1024
    elif units == 'GiB':
        size *= 1024 * 1024 * 1024
    elif units == 'TiB':
        size *= 1024 * 1024 * 1024 * 1024
    elif units != 'Bytes':
        print 'ERROR: Specify size as KiB, MiB, GiB, TiB, or Bytes'
    return int(size)

def scale_bytes(size):
    size = float(size)
    unit = 0
    while size >= 1024:
        size /= 1024
        unit += 1
    size = round(size, 2)
    if unit == 0:
        return (size, 'Bytes')
    elif unit == 1:
        return (size, 'KiB')
    elif unit == 2:
        return (size, 'MiB')
    elif unit == 3:
        return (size, 'GiB')
    elif unit == 4:
        return (size, 'TiB')

def filegen(path, size, verbose=False):
    op_sys = os.name
    if op_sys == 'nt':
        #use the random data file creator tool
        if verbose:
            print 'Generating file: ' + str(size) + ' bytes'
        os.system('rdfc "' + path + '" ' + str(size) + ' > nul')
    elif op_sys == 'posix':
        if size >= 1048576:
            #generate 1 MiB of random bytes
            os.system('dd if=/dev/urandom of=temp.txt bs=1 count=1048576')
        while size >= 1048576:
            #repeatedly concatenate the above generated data to generate a
            #larger file
            os.system('cat temp.txt >> "' + path + '"')
            size -= 1048576
        if size > 0:
            os.system('dd if=/dev/urandom of=temp.txt bs=1 count=' + str(size))
            os.system('cat temp.txt >> "' + path + '"')
        delete_file('temp.txt')

def generate_files(file_path, file_size, file_count):
    initial_file_name = '.txt'.zfill(len(str(file_count)) + 4)
    filegen(file_path + '\\' + initial_file_name, file_size)
    if file_count > 1:
        duplicate_file(file_count, file_path + '\\' + initial_file_name)

def make_path(*args):
    path = ''
    for item in args:
        path += os.path.normpath(item)
    path = os.path.normpath(path)
    return path

@filesystemLock
def delete_file(path):
    op_sys = os.name
    if os.path.isfile(path):
        if op_sys == 'nt':
            os.system('del /Q "' + path + '"')
        elif op_sys == 'posix':
            os.system('rm -f "' + path + '"')
            delay(3)

@filesystemLock
def delete_dir(path):
    op_sys = os.name
    delete_file(path)
    if os.path.isdir(path):
        if op_sys == 'nt':
            os.system('rmdir /S /Q "' + path + '"')
        elif op_sys == 'posix':
            os.system('rm -rf "' + path + '"')
            delay(3)

@filesystemLock
def make_dir(path):
    op_sys = os.name
    if not os.path.isdir(path):
        if op_sys == 'nt':
            os.system('md "' + path + '"')
        elif op_sys == 'posix':
            os.system('mkdir "' + path + '"')
            delay(3)

def copy_files(sourcePath, targetPath):
    """Deprecated. Exists for backwards-compatibility. Use copy_dir or copy_file."""
    if targetPath[-4:] != '.txt':
        dir = True
    else:
        dir = False
    return copy(sourcePath, targetPath, is_dir=dir)


def copy(sourcePath, targetPath, is_dir=True, verbose=False):
    sourcePath = make_path(sourcePath)
    targetPath = make_path(targetPath)
    if verbose:
        print 'Copying ' + sourcePath + ' to ' + targetPath
    op_sys = os.name
    if is_dir:
        make_dir(targetPath)
    if op_sys == 'nt':
        shfileopstruct = (0, shellcon.FO_COPY, sourcePath, targetPath, shellcon.FOF_SILENT | shellcon.FOF_NOCONFIRMATION | shellcon.FOF_NOERRORUI | shellcon.FOF_NOCONFIRMMKDIR,\
                                 None, None)
        r_int, r_boolean = shell.SHFileOperation (shfileopstruct)
        if r_int == 0 and shfileopstruct[5] == None:
            return True
        else:
            return False
    elif op_sys == 'posix':
        if not os.path.isdir(sourcePath):
            os.system('cp -R "' + sourcePath + '" "' + targetPath + '"')
        else:
            os.system('osascript finder_copy.scpt "' + make_path(sourcePath) + \
                      '" "' + make_path(targetPath) + '"')
        return True

def copy_dir(sourcePath, targetPath):
    if os.name == 'nt':
        sourcePath += '\\*'
    return copy(sourcePath, targetPath, is_dir=True)

def copy_file(sourcePath, targetPath):
    return copy(sourcePath, targetPath, is_dir=False)

def duplicate_file(count, file_path, verbose=False):
    if verbose:
        print 'Duplicating ' + file_path + ' ' + str(count) + ' times.'
    import shutil
    for i in xrange(1, count):
        shutil.copyfile(os.path.normpath(file_path), make_path(os.path.split(file_path)[0], '\\' + (str(i) + '.txt').zfill(len(os.path.split(file_path)[1]))))

def files_differ(sourcePath, targetPath):
    op_sys = os.name
    if op_sys == 'nt':
        p = subprocess.Popen('fc /b ' + sourcePath + ' ' + targetPath,
        stdout=subprocess.PIPE)
        for line in p.stdout.readlines():
            if 'FC: no differences encountered' in line:
                return False
        return True

@filesystemLock
def os_disk_letter():
    """Windows only. Returns the drive letter of the OS drive."""
    op_sys = os.name
    if op_sys == 'nt':
        p = subprocess.Popen(['echo', '%windir%'],
        stdout=subprocess.PIPE, shell=True)
        for line in p.stdout.readlines():
            if ':\\' in line:
                return line[0]
        return None

@filesystemLock
def non_os_disks():
    """Return a list of all non-system drives."""
    os_disk = None
    while os_disk == None:
        all_disks = all_disk_details()
        os_letter = os_disk_letter()
        for disk in all_disks:
            for letter in disk[4]:
                print letter
                if letter == os_letter:
                    os_disk = disk
        time.sleep(1)
    all_disks.remove(os_disk)
    return all_disks

@filesystemLock
def os_disk():
    """Return the system drive."""
    all_disks = all_disk_details()
    os_letter = os_disk_letter()
    for disk in all_disks:
        for letter in disk[4]:
            if letter == os_letter:
                return disk
    return None

@filesystemLock
def all_disk_details():
    """Return all drives."""
    all_disk_numbers = disk_numbers()
    details = []
    for disk_number in all_disk_numbers:
        details.append(disk_details(disk_number))
    return details

@filesystemLock
def disk_details(disk_number):
    """Return the details of a given drive."""
    output = diskpart(['select disk ' + str(disk_number[0]), 'detail disk'])
    drive_letters = []
    for i, line in enumerate(output):
        if i == 8:
            device_name = line.strip()
        if 'Type   :' in line:
            type = line[8:].strip()
        letter = volume_match(line)
        if letter != None:
            drive_letters.append(letter)
    return (disk_number[0], device_name, type, disk_number[1], drive_letters)

@filesystemLock
def volume_match(line):
    """For a given line from 'detail disk', return the drive letter."""
    #txt='  Volume 4     F   New Volume   NTFS   Partition    466 GB  Healthy'

    re1='(\\s+)'	# White Space 1
    re2='(Volume)'	# Word 1
    re3='(\\s+)'	# White Space 2
    re4='(\\d+)'	# Integer Number 1
    re5='(\\s+)'	# White Space 3
    re6='(.)'	# Any Single Character 1
    re7='(\\s+)'	# White Space 4

    rg = re.compile(re1+re2+re3+re4+re5+re6+re7,re.IGNORECASE|re.DOTALL)
    m = rg.search(line)
    if m:
        ws1=m.group(1)
        word1=m.group(2)
        ws2=m.group(3)
        int1=m.group(4)
        ws3=m.group(5)
        c1=m.group(6)
        ws4=m.group(7)
        #print "("+ws1+")"+"("+word1+")"+"("+ws2+")"+"("+int1+")"+"("+ws3+")"+"("+c1+")"+"("+ws4+")"+"\n"
        return c1
    return None

@filesystemLock
def disk_numbers():
    """Return the disk numbers of all disks."""
    disks = []
    op_sys = os.name
    if op_sys == 'nt':
        output = diskpart(['list disk'])
        for line in output:
            number = disk_number_and_size(line)
            if number != None:
                disks.append(number)
    return disks

@filesystemLock
def disk_number_and_size(line):
    """Return the disk number and size for a given line from 'list disk'."""
    txt='   Disk 0    Online        74 GB      0 B'

    re1='(\\s+)'	# White Space 1
    re2='(Disk)'	# Word 1
    re3='(\\s+)'	# White Space 2
    re4='(\\d+)'	# Integer Number 1
    re5='(\\s+)'	# White Space 3
    re6='(Online)'	# Word 2
    re7='(\\s+)'	# White Space 4
    re8='(\\d+)'	# Integer Number 2
    re9='(\\s+)'	# White Space 5

    rg = re.compile(re1+re2+re3+re4+re5+re6+re7+re8+re9,re.IGNORECASE|re.DOTALL)
    m = rg.search(line)
    if m:
        ws1=m.group(1)
        word1=m.group(2)
        ws2=m.group(3)
        int1=m.group(4)
        ws3=m.group(5)
        word2=m.group(6)
        ws4=m.group(7)
        int2=m.group(8)
        ws5=m.group(9)
        #print "("+ws1+")"+"("+word1+")"+"("+ws2+")"+"("+int1+")"+"("+ws3+")"+"("+word2+")"+"("+ws4+")"+"("+int2+")"+"("+ws5+")"+"\n"
        return (int(int1), int(int2))
    return None

@filesystemLock
def clean_disk(number):
    """Clean the disk."""
    success = False
    start = time.clock()
    while not success:
        print 'cleaning disk: ' + str(number)
        output = diskpart(['select disk ' + str(number), 'clean'])
        for line in output:
            if 'DiskPart succeeded in cleaning the disk.' in line:
                success = True
        if time.clock() - start > 60:
            print "can't clean disk: " + str(number)
            return False
    return True

@filesystemLock
def clean_drive_letter(letter):
    """Clean the disk containing the specified drive letter."""
    drives = non_os_disks()
    for drive in drives:
        letters = drive[4]
        if letter in letters:
            print 'cleaning drive: ' + str(drive)
            clean_disk(drive[0])
            return True
    return False        

@filesystemLock
def convert_mbr(number):
    p = diskpart(['select disk ' + str(number), 'convert mbr'])

@filesystemLock
def convert_gpt(number):
    p = diskpart(['select disk ' + str(number), 'convert gpt'])

@filesystemLock
def rescan():
    p = diskpart(['rescan'])

@filesystemLock
def create_partition(number, size, offset=0, letter=None):
    """Create a partition on the drive and assign it a drive letter. Size in MB."""
    success = False
    if letter == None:
        letter = find_open_letter()
    start = time.clock()
    while not success:
        failstring = ''
        output = diskpart(['select disk ' + str(number), 'create partition primary size=' + str(int(size)), 'assign letter=' + str(letter)])
        for line in output:
            if 'DiskPart succeeded in creating the specified partition.' in line:
                success = True
            elif 'DiskPart was unable to create the specified partition.' in line:
                failstring += line
                pass
        if not success:
            print failstring        
            print 'Failed to create partition. Retrying in 2 seconds.'
            time.sleep(2)
        if time.clock() - start > 60:
            print "can't partition disk: " + str(letter)
            return None
    return letter

@filesystemLock
def find_open_letter(used_letters=[]):
    """Find the first unused drive letter."""
    from string import ascii_uppercase
    letters = volume_letters()
    letters.append('A')
    letters.append('B')
    if not 'C' in letters:
        letters.append('C')
    print 'letters in use: ' + str(sorted(letters))
    for letter in ascii_uppercase:
        if letter not in letters and letter not in used_letters:
            return letter

@filesystemLock
def volume_letters():
    """Return all currently used drive letters."""
    re1='(\\s+)'	# White Space 1
    re2='(Volume)'	# Word 1
    re3='(\\s+)'	# White Space 2
    re4='(\\d+)'	# Integer Number 1
    re5='(\\s+)'	# White Space 3
    re6='(.)'	# Any Single Character 1
    re7='(\\s+)'	# White Space 4

    rg = re.compile(re1+re2+re3+re4+re5+re6+re7,re.IGNORECASE|re.DOTALL)
    letters = []
    while letters == []:
        output = diskpart('list volume')
        time.sleep(5)
        for line in output:
            m = rg.search(line)
            if m:
                ws1=m.group(1)
                word1=m.group(2)
                ws2=m.group(3)
                int1=m.group(4)
                ws3=m.group(5)
                c1=m.group(6)
                ws4=m.group(7)
                #print "("+ws1+")"+"("+word1+")"+"("+ws2+")"+"("+int1+")"+"("+ws3+")"+"("+c1+")"+"("+ws4+")"+"\n"
                letters.append(c1)
        time.sleep(1)
    return letters

@filesystemLock
def format(drive_letter, fs='NTFS'):
    """Format a volume."""
    print 'formatting: ' + str(drive_letter)
    drive_letter = drive_letter[0]
    y = open('y.txt', 'w')
    y.write('Y')
    y.close()
    time.sleep(1)
    p = subprocess.Popen('format %s: /FS:%s /Q /X /V: < y.txt' % (drive_letter, fs),
    stdin=subprocess.PIPE, stdout=subprocess.PIPE, shell=True)
    time.sleep(1)
    delete_file('y.txt')

@filesystemLock
def create_formatted_partition(number, size, offset=0, letter=None, fs='NTFS'):
    """Create a partition on the drive and assign it a drive letter, then format it. Size in MB."""
    print 'creating formatted partition'
    letter = create_partition(number, size, offset, letter)
    time.sleep(20)
    if letter != None:
        format(letter, fs)
    return letter

@filesystemLock
def find_disk_number(disk_number):
    result = None
    start = time.clock()
    while result == None:
        numbers = disk_numbers()
        for number in numbers:
            if number[0] == disk_number:
                result = number
        time.sleep(1)
        if time.clock() - start > 60:
            print "can't find disk: " + str(disk_number)
            break
    return result

@filesystemLock
def split_disk(disk_number, partitions=4, letters=None, fs='NTFS', table=None):
    """Split a disk into evenly sized partitions. Partitions cannot be set to more than 4."""
    if partitions > 4:
        partitions = 4

    clean_disk(disk_number)

    #workaround for diskpart crash in vista and 7:
    #if "detail disk" is run on an unformatted disk, diskpart crashes
    convert_mbr(disk_number)
    create_formatted_partition(disk_number, 8, letter=find_open_letter())

    # print 'sleeping for 10 seconds'
    time.sleep(10)
    details = disk_details(find_disk_number(disk_number))
    
    #workaround for diskpart crash in vista and 7:
    #if "detail disk" is run on an unformatted disk, diskpart crashes
    clean_disk(disk_number)

    if table == 'MBR':
        convert_mbr(disk_number)
    elif table == 'GPT':
        convert_gpt(disk_number)
    import math
    disk_size = math.floor(details[3]-1) * 1024
    # print 'disk size = ' + str(disk_size)

    disk_over_part = math.floor(float(disk_size) / float(partitions))
    # print 'disk over part = ' + str(disk_over_part)
    partition_size = int(disk_over_part) - 1
    # print 'part size = ' + str(partition_size)
    letters_created = []
    for i in xrange(partitions):
        if letters == None or len(letters) == 0:
            letter=find_open_letter()
        else:
            letter=letters.pop()
        letter = create_formatted_partition(disk_number, partition_size, letter=letter, fs=fs)
        time.sleep(10)
        if letter != None:
            letters_created.append(letter)
    return letters_created

@filesystemLock
def diskpart(commands=None, verbose=False):
    """Run a given set of diskpart commands."""
    if os.name == 'nt':
        if commands != None:
            script = 'temp.txt'
            temp = open(script, 'w')
            if type(commands) == type('blah'):
                if verbose:
                    print 'Diskpart will run: ' + str(commands)
                temp.write(commands)
            else:
                for command in commands:
                    if verbose:
                        print 'Diskpart will run: ' + str(command)
                    temp.write(command + '\n')

            temp.close()
            time.sleep(3)

            if verbose:
                print 'Diskpart executing commands.'
            outfilename = 'diskpartout.txt'
            os.system(('diskpart /s %s > ' % script) + outfilename)
            p = open(outfilename, 'r')
            lines = p.readlines()
            p.close()
            time.sleep(2)
            delete_file(script)
            delete_file(outfilename)
            return lines
    else:
        raise NotImplementedError()
    
def reboot(seconds):
    if os.name == 'nt':
        os.system('shutdown -r -f -t ' + str(seconds))

def get_total_memory():    
    info = c.Win32_ComputerSystem()[0]
    
    return int(info.TotalPhysicalMemory)

def get_available_memory():
    info = c.Win32_PerfFormattedData_PerfOS_Memory()[0]
    
    return int(info.AvailableBytes)

def get_number_of_cores():
    info = c.Win32_Processor()[0]
    
    return int(info.NumberOfCores)

def get_number_of_logical_processors():
    info = c.Win32_Processor()[0]
    
    return int(info.NumberOfLogicalProcessors)

def get_percent_idle_time(cpu):
    info = c.Win32_PerfFormattedData_PerfOS_Processor()[cpu]
    
    return int(info.PercentIdleTime)

def get_percent_processor_time(cpu):
    info = c.Win32_PerfFormattedData_PerfOS_Processor()[cpu]
    
    return int(info.PercentProcessorTime)

def get_process_percent_processor_time(procName):
    list = []
    
    for i in c.Win32_PerfFormattedData_PerfProc_Process():
        if(i.Name == procName):
            
            list += [int(i.PercentProcessorTime), i.IDProcess]
    
    return list

def wmi_format(driveLetter, fileSystem='NTFS', quickFormat=True,
        clusterSize=4096, label=''):
    """Take a drive letter and format the volume.
    
    Keyword arguments:
      - driveLetter -- volume to be formatted
      - fileSystem -- File system format to use for this volume. The default is\
            'NTFS'. Possible values for this parameter: 'NTFS', 'FAT32', 'FAT'
      - quickFormat -- whether to quick format the drive
      - clusterSize -- Disk allocation unit size/cluster size.
      - label -- Label to use for the new volume; can contain up to 11 chars \
            for FAT/FAT32 volumes, and up to 32 chars for NTFS.
    
    """
    for i in c.Win32_Volume():
        if(driveLetter in i.Caption):
            i.Format(FileSystem=fileSystem, QuickFormat=quickFormat,
                    ClusterSize=clusterSize, Label=label)