import ctypes
import time

import cv2
import numpy


qhyccd = ctypes.CDLL('/usr/local/lib/libqhyccd.so')
qhyccd.GetQHYCCDParam.restype = ctypes.c_double
qhyccd.OpenQHYCCD.restype = ctypes.POINTER(ctypes.c_uint32)

result = qhyccd.InitQHYCCDResource()
if result == 0:
    print("InitSDK success\n")
else:
    raise Exception('No SDK')

cameras_found = qhyccd.ScanQHYCCD()
if cameras_found > 0:
    print("found camera\n")
else:
    raise Exception('No Camera')

position_id = 0
type_char_array_32 = ctypes.c_char * 32
id_object = type_char_array_32()
result = qhyccd.GetQHYCCDId(position_id, id_object)

camera_handle = qhyccd.OpenQHYCCD(id_object)

qhyccd.SetQHYCCDStreamMode(camera_handle, ctypes.c_uint32(0))
qhyccd.InitQHYCCD(camera_handle)

chipWidthMM = ctypes.c_uint32(0)
chipHeightMM = ctypes.c_uint32(0)
maxImageSizeX = ctypes.c_uint32(0)
maxImageSizeY = ctypes.c_uint32(0)
pixelWidthUM = ctypes.c_uint32(0)
pixelHeightUM = ctypes.c_uint32(0)
bpp = ctypes.c_uint32(0)
camera_info = qhyccd.GetQHYCCDChipInfo(
    camera_handle, ctypes.byref(chipWidthMM), ctypes.byref(chipHeightMM), ctypes.byref(maxImageSizeX),
    ctypes.byref(maxImageSizeY), ctypes.byref(pixelWidthUM), ctypes.byref(pixelHeightUM),
    ctypes.byref(bpp),
)
print([
    chipWidthMM.value, chipHeightMM.value, maxImageSizeX.value, maxImageSizeY.value,
    pixelWidthUM.value, pixelHeightUM.value, bpp.value
])

GAIN = ctypes.c_int(8)
EXPOSURE_TIME = ctypes.c_int(8)
depth = ctypes.c_uint32(8)

qhyccd.SetQHYCCDBitsMode(camera_handle, depth)

qhyccd.SetQHYCCDParam.restype = ctypes.c_uint32
qhyccd.SetQHYCCDParam.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_double]

qhyccd.SetQHYCCDParam(camera_handle, GAIN, ctypes.c_double(100))
qhyccd.SetQHYCCDParam(camera_handle, EXPOSURE_TIME, ctypes.c_double(66666))
qhyccd.SetQHYCCDResolution(camera_handle, ctypes.c_uint32(0), ctypes.c_uint32(0), maxImageSizeX, maxImageSizeY)
qhyccd.SetQHYCCDBinMode(camera_handle, ctypes.c_uint32(1), ctypes.c_uint32(1))
qhyccd.ExpQHYCCDSingleFrame(camera_handle)

image_data = (ctypes.c_uint8 * maxImageSizeX.value * maxImageSizeY.value)()
channels = ctypes.c_uint32(1)

qhyccd.ExpQHYCCDSingleFrame(camera_handle)
time.sleep(1)


response = qhyccd.GetQHYCCDSingleFrame(
    camera_handle, ctypes.byref(maxImageSizeX), ctypes.byref(maxImageSizeY),
    ctypes.byref(depth), ctypes.byref(channels), image_data,
)

print('RESPONSE: %s' % response)
bytes_data = bytearray(image_data)
print(bytes_data[0], bytes_data[1])

raw_array = numpy.array(bytes_data)
mono_image = raw_array.reshape(maxImageSizeY.value, maxImageSizeX.value)
cv2.imwrite('frame.bmp', mono_image)


qhyccd.CancelQHYCCDExposingAndReadout(camera_handle)
qhyccd.CloseQHYCCD(camera_handle)
qhyccd.ReleaseQHYCCDResource()
