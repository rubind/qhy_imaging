"""
   DWF Python Example
   Author:  Digilent, Inc.
   Revision:  2019-10-16

   Requires:                       
       Python 2.7, 3
   Generate a single given lenght pulse
"""

from ctypes import *
from dwfconstants import *
import sys
import time

if sys.platform.startswith("win"):
    dwf = cdll.dwf
elif sys.platform.startswith("darwin"):
    dwf = cdll.LoadLibrary("/Library/Frameworks/dwf.framework/dwf")
else:
    dwf = cdll.LoadLibrary("libdwf.so")

hdwf = c_int()
channel = c_int(0)
pulse = float(sys.argv[1])
sleeptime = float(sys.argv[2])

#time.sleep(sleeptime)

version = create_string_buffer(16)
dwf.FDwfGetVersion(version)
print("DWF Version: "+str(version.value))

dwf.FDwfParamSet(DwfParamOnClose, c_int(0)) # 0 = run, 1 = stop, 2 = shutdown

#open device
print("Opening first device...")
dwf.FDwfDeviceOpen(c_int(-1), byref(hdwf))


if hdwf.value == hdwfNone.value:
    print("failed to open device")
    quit()

# the device will be configured only when calling FDwfAnalogOutConfigure
dwf.FDwfDeviceAutoConfigureSet(hdwf, c_int(1))

dwf.FDwfAnalogOutNodeEnableSet(hdwf, channel, AnalogOutNodeCarrier, c_bool(True))
dwf.FDwfAnalogOutIdleSet(hdwf, channel, DwfAnalogOutIdleOffset)
dwf.FDwfAnalogOutNodeFunctionSet(hdwf, channel, AnalogOutNodeCarrier, funcSquare)
dwf.FDwfAnalogOutNodeFrequencySet(hdwf, channel, AnalogOutNodeCarrier, c_double(0)) # low frequency
dwf.FDwfAnalogOutNodeOffsetSet(hdwf, channel, AnalogOutNodeCarrier, c_double(0))
dwf.FDwfAnalogOutWaitSet(hdwf, channel, c_double(sleeptime)) # wait length
dwf.FDwfAnalogOutRepeatSet(hdwf, channel, c_int(1)) # repeat once

print("Generating pulse")
dwf.FDwfAnalogOutRunSet(hdwf, channel, c_double(pulse)) # pulse length
dwf.FDwfAnalogOutNodeAmplitudeSet(hdwf, channel, AnalogOutNodeCarrier, c_double(3.3))
dwf.FDwfAnalogOutConfigure(hdwf, channel, c_bool(True))

dwf.FDwfDeviceClose(hdwf)
