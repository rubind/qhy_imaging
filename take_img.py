import ctypes
import time
import tqdm
import numpy as np
from astropy.io import fits
import sys

#**** do these before InitQHYCCD  (you can Only set them ONCE after open) ***
#GetQHYCCDNumberOfReadModes(camhandle, numModes);
#// Use GetQHYCCDReadModeName if you need more detail
#SetQHYCCDReadMode(camhandle, modeNumber);
#[DllImport("qhyccd.dll", EntryPoint = "ControlQHYCCDTemp",
#         CharSet = CharSet.Ansi, CallingConvention = CallingConvention.StdCall)]
#        public unsafe static extern UInt32 ControlQHYCCDTemp(IntPtr handle, double targettemp);

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
depth = ctypes.c_uint(16)

sys.argv[1]
sys.argv[2]

if sys.argv[1].count("-") > 0:
    parsed = sys.argv[1].split("-")
    exp_times = np.array(np.around(10**np.linspace(np.log10(float(parsed[0])) + 3, np.log10(float(parsed[1])) + 3, int(parsed[2]))), dtype=np.int32)*1000
    np.random.shuffle(exp_times)
else:
    exp_times = [float(sys.argv[1])*1e6]
print(exp_times)

im_count = 1

for exp_time in tqdm.tqdm(exp_times):
    qhyccd.SetQHYCCDBitsMode(camera_handle, depth)
    
    qhyccd.SetQHYCCDParam.restype = ctypes.c_uint32
    qhyccd.SetQHYCCDParam.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_double]
    
    qhyccd.SetQHYCCDParam(camera_handle, GAIN, ctypes.c_double(60))
    qhyccd.SetQHYCCDParam(camera_handle, EXPOSURE_TIME, ctypes.c_double(exp_time))
    qhyccd.SetQHYCCDResolution(camera_handle, ctypes.c_uint32(0), ctypes.c_uint32(0), maxImageSizeX, maxImageSizeY)
    qhyccd.SetQHYCCDBinMode(camera_handle, ctypes.c_uint32(1), ctypes.c_uint32(1))
    qhyccd.ExpQHYCCDSingleFrame(camera_handle)
    
    image_data = (ctypes.c_uint16 * maxImageSizeX.value * maxImageSizeY.value)()
    channels = ctypes.c_uint32(1)

    t = time.time()
    qhyccd.ExpQHYCCDSingleFrame(camera_handle)
    t2 = time.time()


    response = qhyccd.GetQHYCCDSingleFrame(
        camera_handle, ctypes.byref(maxImageSizeX), ctypes.byref(maxImageSizeY),
        ctypes.byref(depth), ctypes.byref(channels), image_data,
    )
    t3 = time.time()

    print("exp_time", exp_time, t2 - t, t3 - t2)

    
    print("image_data", image_data)
    mono_image = np.array(image_data)
    print("mono_image", mono_image)
    print("mono_image.shape", mono_image.shape)
    
    print('RESPONSE: %s' % response)
    

    hdu = fits.PrimaryHDU(mono_image)
    hdu.header["EXPTIME"] = exp_time/1e6
    hdu.header["EPTIME"] = time.time()
    hdul = fits.HDUList([hdu])
    hdul.writeto("img_%04i_exp_%.4g_%s.fits" % (im_count, exp_time/1e6, sys.argv[2]), clobber = True)
    time.sleep(1)


    qhyccd.CancelQHYCCDExposingAndReadout(camera_handle)
    im_count += 1
qhyccd.CloseQHYCCD(camera_handle)
qhyccd.ReleaseQHYCCDResource()
