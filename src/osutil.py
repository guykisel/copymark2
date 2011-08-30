# To change this template, choose Tools | Templates
# and open the template in the editor.

__author__ = "Kisel_g"
__date__ = "$Mar 10, 2010 9:52:47 AM$"

import os
import subprocess
import sys
import time
import threading
import re
import platform
import types
import shutil

if platform.mac_ver()[0] != '':
    OS = 'mac'
elif os.name == 'nt':
    OS = 'windows'
elif os.name == 'posix':
    OS = 'posix'
else:
    OS = 'other'

#used by filesystemLock class
filesystem_lock = threading.RLock()

if OS == 'windows':
    print 'OS is Windows.'
    time.clock()
    try:
        import win32file
        import win32gui
        import win32con
        import pythoncom
        import pywintypes
        from win32com.shell import shell, shellcon
    except ImportError:
        pass
else:
    startTime = time.time()

try:
    import wmi
    c = wmi.WMI()
except ImportError:
    pass

FILES_COPIED = 0

def restart_explorer():
    if os.name == 'nt':
        subprocess.check_call(
            'taskkill /f /fi "STATUS eq RUNNING" /im explorer.exe'
        )
        subprocess.check_call(
            'cmd /c start "explorer.exe" "' + str(os.path.join(os.environ.get('SYSTEMROOT'), 'explorer.exe')) + '"'
        )

class filesystemLock(object):
    """Decorator to prevent more than one thread from trying to access
    filesystem functions at the same time.

    """

    def __init__(self, f):
        self.f = f

    def __call__(self, *args, **kwargs):
        filesystem_lock.acquire()
        return_value = self.f(*args, **kwargs)
        filesystem_lock.release()
        return return_value

def windows_version():
    """Return a human-readable windows version from the registry."""
    if sys.platform == 'win32':
        import _winreg

        key = _winreg.OpenKey(_winreg.HKEY_LOCAL_MACHINE,
                              'SOFTWARE/Microsoft\Windows NT/CurrentVersion')
        os_version = str(str(_winreg.QueryValueEx(key, 'ProductName')[0]) +\
                         ' ' + str(platform.win32_ver()[2]) + ' ' +\
                         str(platform.version())).replace(',', '')
        return os_version
    else:
        return None
        
def clear_file_cache():
    if OS == 'posix':
        subprocess.call('sync', shell=True)
        subprocess.call('echo 1 > /proc/sys/vm/drop_caches', shell=True)
    elif OS == 'mac':
        subprocess.call('sync', shell=True)
        subprocess.call('sync', shell=True)
        subprocess.call('du -sx', shell=True)
        subprocess.call('sync', shell=True)

def remount(dir, verbose=False, confirm_unmount=False):
    """Unmount and remount the drive corresponding to the given directory.
    Clears file handles. Only supported in Windows.
    
    """
    if os.name == 'nt':
        drive_letter = get_drive_letter(dir)
        if verbose:
            print 'Remounting ' + drive_letter + ' (dir=' + dir + ')...',
        drive_letter = drive_letter.replace(':', '').replace('\\',
                                                             '').replace('/',
                                                                         '')
        volume = None
        output = diskpart(['select volume ' + drive_letter])
        re1='(Volume)'	# Word 1
        re2='( )'	# White Space 1
        re3='(\\d+)'	# Integer Number 1
        re4='( )'	# White Space 2
        re5='(is)'	# Word 2
        re6='( )'	# White Space 3
        re7='(the)'	# Word 3
        re8='( )'	# White Space 4
        re9='(selected)'	# Word 4
        re10='( )'	# White Space 5
        re11='(volume)'	# Word 5
        re12='(\\.)'	# Any Single Character
        rg = re.compile(re1+re2+re3+re4+re5+re6+re7+re8+re9+re10+re11+re12,re.IGNORECASE|re.DOTALL)
        for line in output:
            m = rg.search(line)
            if m:
                volume = m.group(3)
        attempts = 0
        while True:
            if os.path.isdir(drive_letter + ':/'):
                attempts += 1
                output = diskpart(['select volume ' + drive_letter, 'remove'])
            else:
                break
            if not confirm_unmount:
                break
        print str(attempts) + ' attempts required to unmount drive.'
        if attempts > 1:
            file = open('remounts.txt', 'w+')
            file.write(str(time.asctime()) + ' - ' + str(attempts) + ' remount attempts.')
        output = diskpart(['select volume ' + str(volume), 'assign letter=' + drive_letter])
        if verbose:
            for line in output:
                if 'successfully assigned' in line:
                    return
            print 'Unable to remount.'
    elif os.name == 'posix':
        path = os.path.abspath(dir)
        while not os.path.ismount(path):
            path = os.path.dirname(path)
        try:
            device = get_mount_point(dir)
            print 'Remounting ' + path + ' on ' + device
            if OS == 'posix':
                unmount_string = 'umount "' + path + '"'
            elif OS == 'mac':
                unmount_string = 'diskutil unmount "' + path + '"'
            #print unmount_string
            subprocess.call(unmount_string, shell=True)
            time.sleep(3)
            if not OS == 'mac':
                mkdir_string = 'mkdir "' + path + '"'
                #print mkdir_string
                subprocess.call(mkdir_string, shell=True)
                time.sleep(1)
            if OS == 'posix':
                mount_string = 'mount /dev/' + device + ' "' + path + '"'
            elif OS == 'mac':
                mount_string = 'diskutil mount /dev/' + device
            #print mount_string
            subprocess.call(mount_string, shell=True)
            time.sleep(3)
            print 'Remount complete.'
        except OSError, e:
            print e
            print 'Remount of ' + dir + ' failed.'

def get_drive_letter(dir):
    """Get the drive letter of a given directory. For example, given 
    "C:/temp/blah", this function returns "C:/".

    """
    drive_letter = os.path.dirname(dir)
    while drive_letter != os.path.dirname(drive_letter):
        drive_letter = os.path.dirname(drive_letter)
    return drive_letter

def median(list):
    """Return the median value in a list."""
    sorted_list = sorted(list)
    if len(list) < 0:
        raise EmptyListError
    medianIndex = len(list) / 2
    if len(list) % 2 != 0:
        return sorted_list[medianIndex]
    else:
        return (sorted_list[medianIndex] + sorted_list[medianIndex - 1]) / 2

def get_disk_space(path):
    """Return the free disk space of a drive (in bytes)."""
    if os.name == 'nt':
        import win32api

        tuple = win32api.GetDiskFreeSpace(make_path(path))
        return tuple[0] * tuple[1] * tuple[2]
    elif os.name == 'posix':
        os.system('df ' + make_path(path) + ' > ' + make_path(path,\
                                                              'dirsize.txt'))
        dir = open(make_path(path, 'dirsize.txt'), 'r')
        dir.readline()
        return dir.readline().split(' ')[3]

def delay(seconds, verbose=False):
    """Pause for a given number of seconds, printing the time remaining
    once per second.

    """
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
    """Disable the windows autorun feature."""
    if os.name == 'nt':
        import _winreg

        key = _winreg.OpenKey(_winreg.HKEY_LOCAL_MACHINE,
                              'Software/Microsoft/Windows/CurrentVersion/Policies/Explorer')
        #return _winreg.QueryValueEx(key, 'ProductName')[0]:
        _winreg.SetValueEx(key, 'NoDriveTypeAutoRun', 0, _winreg.REG_DWORD, 0xFF)

def get_time():
    """Get the time in seconds since osutil was first loaded."""
    global startTime
    if os.name == 'nt':
        return time.clock()
    elif os.name == 'posix':
        return time.time() - startTime

def convertToBytes(size, units):
    """Convert a filesize given in KiB, MiB, GiB, or TiB to a # of bytes."""
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
    """Convert a filesize given in bytes to KiB, MiB, GiB, or TiB."""
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
    """Generate a file made up of random data."""
    if os.name == 'nt':
    #use the random data file creator tool
        if verbose:
            print 'Generating file: ' + str(size) + ' bytes'
        subprocess.call('rdfc "' + path + '" ' + str(size) + ' > nul', shell=True)
    elif os.name == 'posix':
        if size >= 1048576:
        #generate 1 MiB of random bytes
            subprocess.call('dd if=/dev/urandom of=temp.txt bs=1 count=1048576', shell=True)
        while size >= 1048576:
        #repeatedly concatenate the above generated data to generate a
        #larger file
            subprocess.call('cat temp.txt >> "' + path + '"', shell=True)
            size -= 1048576
        if size > 0:
            subprocess.call('dd if=/dev/urandom of=temp.txt bs=1 count=' + str(size), shell=True)
            subprocess.call('cat temp.txt >> "' + path + '"', shell=True)
        delete_file('temp.txt')

def generate_files(file_path, file_size, file_count):
    """Generate a number of files made up of random data."""
    initial_file_name = '.txt'.zfill(len(str(file_count)) + 4)
    start = time.clock()
    while True:
        try:
            generated_files = [initial_file_name]
            filegen(os.path.normpath(os.path.join(os.path.normpath(file_path), initial_file_name)), file_size, verbose=True)
            if file_count > 1:
                generated_files.append(duplicate_file(file_count, os.path.join(file_path, initial_file_name), verbose=True))
            break
        except IOError, e:
            print 'Generate failed!'
            print str(e)
    print 'Time to generate files: ' + str(int(time.clock() - start))+ ' seconds'
    return generated_files

def make_path(*args):
    """Given a series of strings, concatenate them and normalize them to a
    path.

    """
    path = ''
    for item in args:
        path = os.path.join(path, os.path.normpath(item))
    path = os.path.normpath(path)
    return path

@filesystemLock
def delete_file(path):
    """Delete the file at path."""
    if os.path.isfile(path):
        if os.name == 'nt':
            os.system('del /Q "' + path + '"')
        elif os.name == 'posix':
            os.system('rm -f "' + path + '"')
            delay(3)

@filesystemLock
def delete_dir(path):
    """Delete the directory at path."""
    delete_file(path)
    if os.path.isdir(path):
        try:
            shutil.rmtree(path)
        except Exception, e:
            print str(e)

                

@filesystemLock
def make_dir(path):
    """Make a new directory at path."""
    if not os.path.isdir(path):
        if os.name == 'nt':
            os.system('md "' + path + '"')
        elif os.name == 'posix':
            os.system('mkdir "' + path + '"')
            delay(3)

@filesystemLock
def make_all_dirs_in_path(path):
    #if the path doesn't already exist
    if not os.path.exists(path):
        #split it into the last part of the path and everything else
        (head, tail) = os.path.split(path)
        #if everything else doesn't exist, create it
        if not os.path.exists(head):
            make_all_dirs_in_path(head)
        #create the last part of the path
        make_dir(path)

def copy_files(sourcePath, targetPath):
    """Deprecated. Exists for backwards-compatibility. Use copy_dir or
    copy_file.

    """
    if targetPath[-4:] != '.txt':
        dir = True
    else:
        dir = False
    return copy(sourcePath, targetPath, is_dir=dir)

def copy(sourcePath, targetPath, is_dir=True, verbose=False, quiet=True, shell_copy=True):
    """Copy a file or directory from sourcePath to targetPath."""
    global OS
    global FILES_COPIED
    sourcePath = make_path(sourcePath)
    targetPath = make_path(targetPath)
    if verbose:
        print 'Copying ' + sourcePath + ' to ' + targetPath
    if is_dir:
        make_dir(targetPath)
    if os.name == 'nt':
        if shell_copy:
            #set flags for SHFileOperation
            flags = shellcon.FOF_NOCONFIRMATION |   \
            shellcon.FOF_NOERRORUI | shellcon.FOF_NOCONFIRMMKDIR
            if quiet:
                #don't pop up the transfer progress window
                flags = flags | shellcon.FOF_SILENT
            shfileopstruct = (0, shellcon.FO_COPY, sourcePath, targetPath,
                              flags,\
                              None, None)
            #start the file transfer
            r_int, r_boolean = shell.SHFileOperation(shfileopstruct)
            if r_int == 0 and not shfileopstruct[5]:
                #successful transfer
                return True
            else:
                #failed transfer
                return False
        else:
            try:
                FILES_COPIED = 0
                if not os.path.isdir(sourcePath):
                    #if it's just a single file, transfer it
                    win32file.CopyFileEx(sourcePath, targetPath)
                else:
                    #otherwise, walk the directory tree and add all the files in it
                    #to a list of files to copy.
                    files_to_copy = []
                    for root, dirs, files in os.walk(sourcePath):
                        root = os.path.normpath(root)
                        sub_root = root.split(sourcePath)[-1]
                        for name in files:
                            files_to_copy.append((os.path.join(root, name), os.path.join(targetPath, sub_root, name)))
                    #for each file in the list, copy the file.
                    for source, dest in files_to_copy:
                        win32file.CopyFileEx(source, dest, ProgressRoutine=copyprogress)
                    start = time.clock()
                    while FILES_COPIED < len(files_to_copy):
                        time.sleep(.1)
                    print 'Waited for ' + str(int(time.clock() - start)) + ' seconds after all file transfers were queued.'
            except pywintypes.error, e:
                print 'File transfer failed.'
                return False
            return True
    elif OS == 'mac':
        if not os.path.isdir(sourcePath):
            os.system('cp -Rf "' + sourcePath + '" "' + targetPath + '"')
        else:
            finder_copy_string = 'osascript finder_copy.scpt "' + make_path(sourcePath) +\
                      '" "' + make_path(targetPath) + '"'
            os.system(finder_copy_string)
        return True
    elif OS == 'posix':
        copy_string = 'cp -Rf "' + sourcePath + '" "' + targetPath + '"'
        subprocess.call(copy_string, shell=True)
        return True
    return False

def copyprogress(TotalFileSize, TotalBytesTransferred, StreamSize, StreamBytesTransferred, StreamNumber, CallbackReason, SourceFile, DestinationFile, Arg):
    global FILES_COPIED
    if TotalFileSize == TotalBytesTransferred:
        FILES_COPIED += 1
    return win32file.PROGRESS_CONTINUE

def copy_dir(sourcePath, targetPath, verbose=False, quiet=True, shell_copy=True):
    """Copy a directory from sourcePath to targetPath."""
    if os.name == 'nt' and shell_copy:
        sourcePath += '/*'
    return copy(sourcePath, targetPath, is_dir=True, verbose=verbose, quiet=quiet, shell_copy=shell_copy)

def copy_file(sourcePath, targetPath, verbose=False, quiet=True):
    """Copy a file from sourcePath to targetPath."""
    return copy(sourcePath, targetPath, False, verbose, quiet)

def duplicate_file(count, file_path, verbose=False):
    """Duplicate the file at file_path."""
    if verbose:
        print 'Duplicating ' + file_path + ' ' + str(count) + ' times.'
    import shutil
    generated_files = []
    for i in xrange(1, count):
        new_file_name = make_path(os.path.split(file_path)[0], (str(i) + '.txt').zfill(len(os.path.split(file_path)[1])))
        shutil.copyfile(os.path.normpath(file_path), new_file_name)
        generated_files.append(new_file_name)
    return generated_files

def files_differ(sourcePath, targetPath):
    """Run a diff on the files at sourcePath and targetPath and return True
    if they aren't the same.

    """
    if os.name == 'nt':
        p = subprocess.Popen('fc /b ' + sourcePath + ' ' + targetPath,
                             stdout=subprocess.PIPE)
        for line in p.stdout.readlines():
            if 'FC: no differences encountered' in line:
                return False
        return True

@filesystemLock
def os_disk_letter():
    """Windows only. Returns the drive letter of the OS drive."""
    if os.name == 'nt':
        p = subprocess.Popen(['echo', '%windir%'],
                             stdout=subprocess.PIPE, shell=True)
        for line in p.stdout.readlines():
            if ':/' in line:
                return line[0]
        return None

@filesystemLock
def non_os_disks():
    """Return a list of all non-system drives. Uses diskpart, so it runs
    relatively slowly. Will not return drives that diskpart can't see, such as
    removable disks. Results are a list of tuples, where each tuple follows this
    format:
    (drive number, drive name, drive type, drive size in GB, drive letter)

    """
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
    """Return the system drive. Uses diskpart, so it runs
    relatively slowly. Will not return drives that diskpart can't see, such as
    removable disks. Results are a list of tuples, where each tuple follows this
    format:
    (drive number, drive name, drive type, drive size in GB, drive letter)

    """
    all_disks = all_disk_details()
    os_letter = os_disk_letter()
    for disk in all_disks:
        for letter in disk[4]:
            if letter == os_letter:
                return disk
    return None

@filesystemLock
def all_disk_details():
    """Return all drives. Uses diskpart, so it runs
    relatively slowly. Will not return drives that diskpart can't see, such as
    removable disks. Results are a list of tuples, where each tuple follows this
    format:
    (drive number, drive name, drive type, drive size in GB, drive letter)

    """
    all_disk_numbers = disk_numbers()
    details = []
    for disk_number in all_disk_numbers:
        details.append(disk_details(disk_number))
    return details

@filesystemLock
def disk_details(disk_number):
    """Return the details of a given drive. Uses diskpart, so it runs
    relatively slowly. Will not return drives that diskpart can't see, such as
    removable disks. Results are tuples, where the tuple follows this
    format:
    (drive number, drive name, drive type, drive size in GB, drive letter)

    """
    if type(disk_number) == types.IntType:
        size = None
        disk_list = disk_numbers()
        for disk in disk_list:
            if disk[0] == disk_number:
                size = disk[1]
        disk_number = (disk_number, size)
    output = diskpart(['select disk ' + str(disk_number[0]), 'detail disk'])
    drive_letters = []
    for i, line in enumerate(output):
        if i == 8:
            device_name = line.strip()
        if 'Type   :' in line:
            disktype = line[8:].strip()
        letter = volume_match(line)
        if letter != None:
            drive_letters.append(letter)
    return (disk_number[0], device_name, disktype, disk_number[1],
            drive_letters)

@filesystemLock
def volume_match(line):
    """For a given line from diskpart's 'detail disk', return the drive letter.
    'detail disk' printouts look like this:
    '  Volume 4     F   New Volume   NTFS   Partition    466 GB  Healthy'

    """
    #txt='  Volume 4     F   New Volume   NTFS   Partition    466 GB  Healthy'

    re1 = '(/s+)'    # White Space 1
    re2 = '(Volume)'    # Word 1
    re3 = '(/s+)'    # White Space 2
    re4 = '(/d+)'    # Integer Number 1
    re5 = '(/s+)'    # White Space 3
    re6 = '(.)'    # Any Single Character 1
    re7 = '(/s+)'    # White Space 4

    rg = re.compile(re1 + re2 + re3 + re4 + re5 + re6 + re7,
                    re.IGNORECASE | re.DOTALL)
    m = rg.search(line)
    if m:
        ws1 = m.group(1)
        word1 = m.group(2)
        ws2 = m.group(3)
        int1 = m.group(4)
        ws3 = m.group(5)
        c1 = m.group(6)
        ws4 = m.group(7)
        return c1
    return None

@filesystemLock
def disk_numbers():
    """Return the disk numbers of all disks. Results are returned as a list
    of tuples, where each tuple is of the following format:
    (disk number, disk size in gigabytes)

    """
    disks = []
    if os.name == 'nt':
        output = diskpart(['list disk'])
        for line in output:
            number = disk_number_and_size(line)
            if number != None:
                disks.append(number)
    return disks

@filesystemLock
def disk_number_and_size(line):
    """Return the disk number and size for a given line from 'list disk'.
    'list disk' printouts look like this:
    '   Disk 0    Online        74 GB      0 B'
    
    """
    txt = '   Disk 0    Online        74 GB      0 B'

    re1 = '(/s+)'    # White Space 1
    re2 = '(Disk)'    # Word 1
    re3 = '(/s+)'    # White Space 2
    re4 = '(/d+)'    # Integer Number 1
    re5 = '(/s+)'    # White Space 3
    re6 = '(Online)'    # Word 2
    re7 = '(/s+)'    # White Space 4
    re8 = '(/d+)'    # Integer Number 2
    re9 = '(/s+)'    # White Space 5

    rg = re.compile(re1 + re2 + re3 + re4 + re5 + re6 + re7 + re8 + re9,
                    re.IGNORECASE | re.DOTALL)
    m = rg.search(line)
    if m:
        ws1 = m.group(1)
        word1 = m.group(2)
        ws2 = m.group(3)
        int1 = m.group(4)
        ws3 = m.group(5)
        word2 = m.group(6)
        ws4 = m.group(7)
        int2 = m.group(8)
        ws5 = m.group(9)
        return (int(int1), int(int2))
    return None

@filesystemLock
def clean_disk(number):
    """Clean the disk using diskpart."""
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
    """Convert the specified disk to MBR."""
    p = diskpart(['select disk ' + str(number), 'convert mbr'])

@filesystemLock
def convert_gpt(number):
    """Convert the specified disk to GPT."""
    p = diskpart(['select disk ' + str(number), 'convert gpt'])

@filesystemLock
def rescan():
    """Run a diskpart 'rescan', which forces Windows to rescan all attached
    drives.

    """
    p = diskpart(['rescan'])

@filesystemLock
def create_partition(number, size, offset=0, letter=None):
    """Create a partition on the drive and assign it a drive letter. Size in MB.
    Runs in diskpart, so it might be slow.

    """
    success = False
    if letter == None:
        letter = find_open_letter()
    start = time.clock()
    while not success:
        failstring = ''
        output = diskpart(['select disk ' + str(number),
                           'create partition primary size=' + str(int(size)),
                           'assign letter=' + str(letter)])
        for line in output:
            if 'DiskPart succeeded in creating the specified partition.'\
            in line:
                success = True
            elif 'DiskPart was unable to create the specified partition.'\
            in line:
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
    re1 = '(/s+)'    # White Space 1
    re2 = '(Volume)'    # Word 1
    re3 = '(/s+)'    # White Space 2
    re4 = '(/d+)'    # Integer Number 1
    re5 = '(/s+)'    # White Space 3
    re6 = '(.)'    # Any Single Character 1
    re7 = '(/s+)'    # White Space 4

    rg = re.compile(re1 + re2 + re3 + re4 + re5 + re6 + re7,
                    re.IGNORECASE | re.DOTALL)
    letters = []
    while letters == []:
        output = diskpart('list volume')
        time.sleep(5)
        for line in output:
            m = rg.search(line)
            if m:
                ws1 = m.group(1)
                word1 = m.group(2)
                ws2 = m.group(3)
                int1 = m.group(4)
                ws3 = m.group(5)
                c1 = m.group(6)
                ws4 = m.group(7)
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
    p = subprocess.Popen('format %s: /FS:%s /Q /X /V: < y.txt' % (drive_letter,
                                                                  fs),
                         stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         shell=True)
    time.sleep(1)
    delete_file('y.txt')

@filesystemLock
def create_formatted_partition(number, size, offset=0, letter=None, fs='NTFS'):
    """Create a partition on the drive and assign it a drive letter, then
    format it. Size in MB.

    """
    print 'creating formatted partition'
    letter = create_partition(number, size, offset, letter)
    time.sleep(20)
    if letter != None:
        format(letter, fs)
    return letter

@filesystemLock
def find_disk_number(disk_number):
    """Find the specified disk number, if it exists.
    Results are returned as a tuple, where the tuple is of the following format:
    (disk number, disk size in gigabytes)
    If the disk is not found, return None.

    """
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
            return None
    return result

@filesystemLock
def split_disk(disk_number, partitions=4, letters=None, fs='NTFS', table=None):
    """Split a disk into evenly sized partitions. Partitions cannot be set to
    more than 4. This can take a while to run.

    """
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

    disk_size = math.floor(details[3] - 1) * 1024
    # print 'disk size = ' + str(disk_size)

    disk_over_part = math.floor(float(disk_size) / float(partitions))
    # print 'disk over part = ' + str(disk_over_part)
    partition_size = int(disk_over_part) - 1
    # print 'part size = ' + str(partition_size)
    letters_created = []
    for i in xrange(partitions):
        if letters == None or len(letters) == 0:
            letter = find_open_letter()
        else:
            letter = letters.pop()
        letter = create_formatted_partition(disk_number, partition_size,
                                            letter=letter, fs=fs)
        time.sleep(10)
        if letter != None:
            letters_created.append(letter)
    return letters_created

@filesystemLock
def diskpart(commands=None, verbose=False):
    """Run a given set of diskpart commands. commands can either be a string or
    a list of strings.

    """
    if os.name == 'nt':
        if commands != None:
            script = 'temp.txt'
            temp = open(script, 'w')
            #check to see if it's a string
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

def reboot(seconds=1):
    """Tell the OS to reboot."""
    if os.name == 'nt':
        os.system('shutdown -r -f -t ' + str(seconds))
    else:
        os.system('reboot')

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

def get_process_percent_processor_time(procName, partial_match=False):
    #WMI query doesn't work if process name ends with .exe
    procName = procName.rstrip('.exe')
    list = []

    for i in c.Win32_PerfFormattedData_PerfProc_Process():
        if i.Name == procName or (partial_match and procName in i.Name):
            list.append((int(i.PercentProcessorTime), i.IDProcess, i.Name))

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

def set_clipboard_data(data=''):
    import win32clipboard

    win32clipboard.OpenClipboard()
    win32clipboard.EmptyClipboard()
    win32clipboard.SetClipboardData(win32clipboard.CF_TEXT, data)
    close_clipboard()

def get_clipboard_data():
    import win32clipboard

    win32clipboard.OpenClipboard()
    if win32clipboard.IsClipboardFormatAvailable(win32clipboard.CF_TEXT):
        try:
            data = win32clipboard.GetClipboardData()
            close_clipboard()
            return data
        except Exception, e:
            print e
            close_clipboard()
            return ''

    else:
        close_clipboard()
        return None

def close_clipboard():
    import win32clipboard

    try:
        win32clipboard.CloseClipboard()
    except Exception, e:
        print e

def get_mount_point(path, volume=True):
    path = os.path.abspath(path)
    while not os.path.ismount(path):
        path = os.path.dirname(path)
    p = subprocess.Popen('mount',
                         stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         shell=True)
    device = None
    for line in p.stdout.readlines():
        if path in line:
            device = line

    import re
    txt=device
    re1='.*?'	# Non-greedy match on filler
    re2='(?:[a-z][a-z]+)'	# Uninteresting: word
    re3='.*?'	# Non-greedy match on filler
    if not volume:
        re4='((?:[a-z][a-z]+))'	# Word 1
    else:
        re4='((?:[a-z][a-z]*[0-9]+[a-z0-9]*))'	# Word 1
    rg = re.compile(re1+re2+re3+re4,re.IGNORECASE|re.DOTALL)
    m = rg.search(txt)
    if m:
        device=m.group(1)
    return device

def disk_activity(disk):
    if OS == 'windows':
        c = wmi.WMI()
        for i in c.Win32_PerfFormattedData_PerfDisk_LogicalDisk():
            if disk in i.Name:
                return int(i.PercentDiskTime)
    elif OS == 'posix':
        p = subprocess.Popen('cat /sys/block/' + disk + '/stat',
                             stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                             shell=True)
        import re
        re1='.*?'	# Non-greedy match on filler
        re2='\\d+'	# Uninteresting: int
        re3='.*?'	# Non-greedy match on filler
        re4='\\d+'	# Uninteresting: int
        re5='.*?'	# Non-greedy match on filler
        re6='\\d+'	# Uninteresting: int
        re7='.*?'	# Non-greedy match on filler
        re8='\\d+'	# Uninteresting: int
        re9='.*?'	# Non-greedy match on filler
        re10='\\d+'	# Uninteresting: int
        re11='.*?'	# Non-greedy match on filler
        re12='\\d+'	# Uninteresting: int
        re13='.*?'	# Non-greedy match on filler
        re14='\\d+'	# Uninteresting: int
        re15='.*?'	# Non-greedy match on filler
        re16='\\d+'	# Uninteresting: int
        re17='.*?'	# Non-greedy match on filler
        re18='(\\d+)'	# Integer Number 1
        
        rg = re.compile(re1+re2+re3+re4+re5+re6+re7+re8+re9+re10+re11+re12+re13+re14+re15+re16+re17+re18,re.IGNORECASE|re.DOTALL)
        for line in p.stdout.readlines():
            m = rg.search(line)
            if m:
                int1=m.group(1)
                return int1

    elif OS == 'mac':
        p = subprocess.Popen('fs_usage',
                             stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                             shell=True)
        time.sleep(.1)
        p.terminate()
        for line in p.stdout.readlines():
            if 'Python' in line or 'Finder' in line or 'dd' in line:
                return 1
        
    return 0

def wait_for_dir_idle(dirs, verbose=False, idle_time=10):
    disks = []
    if os.name == 'posix':
        for dir in dirs:
            if OS == 'mac':
                volume = True
            else:
                volume = False
            device = get_mount_point(dir, volume=volume)
            disks.append(device)
    elif os.name == 'nt':
        for dir in dirs:
            disk = get_drive_letter(dir)[0].upper()
            disks.append(disk.upper())
    return wait_for_disk_idle(disks, verbose, idle_time)

def wait_for_disk_idle(disks, verbose=False, idle_time=10):
    disks = list(set(disks))
    if verbose:
        print 'Waiting for disks to be idle: ' + str(disks)
    seconds_idle = 0
    last_activity = get_time()
    while seconds_idle < idle_time:
        all_idle = True
        for disk in disks:
            activity = int(disk_activity(disk))
            if activity != 0:
                all_idle = False
                break
        if all_idle:
            seconds_idle += 1
            if verbose:
                print 'Disks have been idle for ' + str(seconds_idle) + ' seconds.'
        else:
            seconds_idle = 0
            last_activity = get_time()
            if verbose:
                print 'Disk activity detected. Resetting counter.'
        time.sleep(1)
    return last_activity