import ctypes
import time
from astropy.io import fits
import numpy
from gpiozero import LED
import numpy as np
import tqdm

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

GAIN = ctypes.c_int(6)
OFFSET = ctypes.c_int(7)
EXPOSURE_TIME = ctypes.c_int(8)
#depth = ctypes.c_short(10)

print("bpp", bpp.value)
qhyccd.SetQHYCCDBitsMode(camera_handle, bpp)

qhyccd.SetQHYCCDParam.restype = ctypes.c_uint32
qhyccd.SetQHYCCDParam.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_double]

qhyccd.SetQHYCCDParam(camera_handle, GAIN, ctypes.c_double(5))
qhyccd.SetQHYCCDParam(camera_handle, OFFSET, ctypes.c_double(100))
qhyccd.SetQHYCCDParam(camera_handle, EXPOSURE_TIME, ctypes.c_double(3000000))
#qhyccd.SetQHYCCDParam(camera_handle, depth, ctypes.c_double(16))

qhyccd.SetQHYCCDResolution(camera_handle, ctypes.c_uint32(0), ctypes.c_uint32(0), maxImageSizeX, maxImageSizeY)
qhyccd.SetQHYCCDBinMode(camera_handle, ctypes.c_uint32(1), ctypes.c_uint32(1))
qhyccd.ExpQHYCCDSingleFrame(camera_handle)

led = LED(21)


for iteration in tqdm.trange(100):
    print(time.asctime())
    for LED_on, suffix in zip([1,1,0,0], "ABCD"):
        time.sleep(3)
        
        if LED_on:
            led.on()
        else:
            led.off()
            
        time.sleep(3)
        image_data = (ctypes.c_uint16 * maxImageSizeX.value * maxImageSizeY.value)()
        channels = ctypes.c_uint32(1)
        
        qhyccd.ExpQHYCCDSingleFrame(camera_handle)
        time.sleep(1)
        print("Getting response")
        
        response = qhyccd.GetQHYCCDSingleFrame(
            camera_handle, ctypes.byref(maxImageSizeX), ctypes.byref(maxImageSizeY),
            ctypes.byref(bpp), ctypes.byref(channels), image_data,
        )
        
        print('RESPONSE: %s' % response)
        tmp_array = np.frombuffer(image_data, dtype=np.uint16)
        print("tmp_array", tmp_array, len(tmp_array))
        
        #bytes_data = bytearray(image_data)
        #print("hytes_data", bytes_data[0], bytes_data[1])
        
        #raw_array = numpy.array(bytes_data)
        #print("raw_array", raw_array)
        mono_image = tmp_array.reshape(maxImageSizeY.value, maxImageSizeX.value)
    
        #print("raw_array", raw_array)
        print("mono_image", mono_image)
        
        print("median", np.median(mono_image))
        print("NMAD", 1.4826*np.median(np.abs(mono_image - np.median(mono_image))))
    
        hdu = fits.PrimaryHDU(mono_image)
        hdul = fits.HDUList([hdu])
        hdul.writeto("img_%04i_%s.fits" % (iteration, suffix), clobber=True)
        hdul.close()

    
    

qhyccd.CancelQHYCCDExposingAndReadout(camera_handle)
qhyccd.CloseQHYCCD(camera_handle)
qhyccd.ReleaseQHYCCDResource()
