# Sample Data #
| reading from | writing to | I/O direction | MiB/s | MB/s | total bytes | file size | file count | duration | true\_duration | true\_MiB/s | start time | end time | trial | fill index | test | OS | CPU | start date | test duration | calibration method | notes|
|:-------------|:-----------|:--------------|:------|:-----|:------------|:----------|:-----------|:---------|:---------------|:------------|:-----------|:---------|:------|:-----------|:-----|:---|:----|:-----------|:--------------|:-------------------|:-----|
|g: |d: |S<-T |31.4819386521 |33.0112053041 |1310720000 |26214400 |50 |39.7053057568 |94.2625895256 |13.2608281429 |130.94077611 |170.646081867 |0 |0 |Copymark2 0.0.6 |Windows 7 Ultimate SP1 6.1.7601 |Intel64 Family 6 Model 26 Stepping 5 GenuineIntel |8/24/2011 |0:03:58 |not calibrated |  |

# Column Headings #
  * **reading from/writing to**: These are the source and target directories/drives.
  * **I/O direction**: The direction of the file transfer.
  * **MiB/s**: The user experience data rate in MiB/s (http://en.wikipedia.org/wiki/Mebibyte)
  * **MB/s**: The user experience data rate in MB/s (http://en.wikipedia.org/wiki/Megabyte)
  * **total bytes**: The total number of bytes transferred in the trial.
  * **file size**: The size of each file transferred.
  * **file count**: The number of files transferred.
  * **duration**: The duration in seconds of the file transfer, from the user's point of view.
  * **true\_duration**: The duration in seconds of the file transfer, based on disk activity.
  * **true\_MiB/s**: The data rate in MiB/s, based on true\_duration.
  * **start time**: The start time of the trial, in seconds since the start of the test.
  * **end time**: The end time of the trial (from the user's point of view), in seconds since the start of the test.
  * **trial**: The trial number. This is the number of times this particular combination of file size, file count, and I/O direction has been run so far.
  * **fill index**: This is used when running in fill mode, where the test will continue to copy data until the disk is full.
  * **test**: The current version of the test.
  * **OS**: The OS name and version as determined by the test.
  * **CPU**: The CPU type as determined by the test. This comes from Python's platform.processor() function.
  * **start date**: The date the test was started.
  * **test duration**: The duration of the test so far, formatted for easier reading.
  * **calibration method**: The type of calibration used (or "not calibrated", if no calibration was used).
  * **notes**: Notes are supplied by the user when the test is launched. 