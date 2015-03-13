# Command line syntax #
Run Copymark2 using this syntax: `python copymark2.py <source dir> <target dir> <workload file> [options]`

# Command line options #
### Calibration mode ###
  * `-c` or `--calibrate`
  * **Boolean**
  * Automatically calibrate file counts. Defaults to False.
  * [More information about Calibration mode](Calibration.md).

### Calibration heuristic ###
  * `-H` or `-heuristic`
  * **String**
  * Specify an external calibration heuristic.
  * [More information about Calibration heuristics](Calibration.md).

### Log file ###
  * `-l` or `--logfile`
  * **String**
  * Specify a log file. Defaults to log.csv.
  * [More information about Copymark2 log files](Results.md).

### Trials ###
  * `-t` or `--trials`
  * **Integer**
  * Number of trials to run. Defaults to 1.

### Sweep mode ###
  * `-s` or `--sweep`
  * **Boolean**
  * Run full sweeps instead of running each file size _trials_ times. Defaults to False.

### Drive fill mode ###
  * `-f` or `--fill`
  * **Boolean**
  * Drive fill mode - gradually fill a drive while benchmarking. Defaults to False. If fill mode is enabled, calibration will be disabled.