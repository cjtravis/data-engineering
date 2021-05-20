#!/bin/bash

for pid in $(ps -ef | grep -v "grep" | grep "Python app.py" | awk '{print $2}') ; do echo -e "Killing process PID $pid\n"; kill -9 $pid; done