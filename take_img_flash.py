import ctypes
import time
import tqdm
import numpy as np
from astropy.io import fits
import sys
import subprocess
import random
 
def send_notification(notify):
    print(
        subprocess.getoutput('mail -s "QHY" ' + notify + ' < /dev/null')
        )

def do_it(cmd):
    print(cmd)
    print(subprocess.getoutput(cmd))
    #subprocess.run([cmd], capture_output=False)
    #subprocess.Popen(cmd,
    #                 stdout=subprocess.PIPE)
    subprocess.Popen(cmd, shell=True)

#def open_connection():


#def close_connection():
    

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

#print(qhyccd.GetQHYCCDNumberOfReadModes(camera_handle))

#print("numModes", numModes)
#print(qhyccd.GetQHYCCDReadModeName(camera_handle))


qhyccd.SetQHYCCDReadMode(camera_handle, ctypes.c_uint32(1))
qhyccd.SetQHYCCDStreamMode(camera_handle, ctypes.c_uint32(0))
qhyccd.InitQHYCCD(camera_handle)

chipWidthMM = ctypes.c_uint32(0)
chipHeightMM = ctypes.c_uint32(0)
maxImageSizeX = ctypes.c_uint32(0)
maxImageSizeY = ctypes.c_uint32(0)
pixelWidthUM = ctypes.c_uint32(0)
pixelHeightUM = ctypes.c_uint32(0)
bpp = ctypes.c_uint32(0)

Camera_info = qhyccd.GetQHYCCDChipInfo(
    camera_handle, ctypes.byref(chipWidthMM), ctypes.byref(chipHeightMM), ctypes.byref(maxImageSizeX),
    ctypes.byref(maxImageSizeY), ctypes.byref(pixelWidthUM), ctypes.byref(pixelHeightUM),
    ctypes.byref(bpp),)


print("chipWidthMM.value, chipHeightMM.value, maxImageSizeX.value, maxImageSizeY.value, pixelWidthUM.value, pixelHeightUM.value, bpp.value", [
    chipWidthMM.value, chipHeightMM.value, maxImageSizeX.value, maxImageSizeY.value,
    pixelWidthUM.value, pixelHeightUM.value, bpp.value
])


before_after = 5
min_time = 5e3
max_time = 20e6

if 0:
    exp_times = list(np.array(np.around(
        10**np.linspace(np.log10(min_time), np.log10(max_time), int(sys.argv[1])) + before_after*2e6,
        -3), dtype=np.int32))
else:
    exp_times = list(np.array(np.around(
        10**(np.random.random(size = int(sys.argv[1]))*np.log10(max_time/min_time) + np.log10(min_time)) + before_after*2e6,
        -3), dtype=np.int32))
    
n_darks = int(float(sys.argv[1])/5.)

assert int(sys.argv[1]) < 16

mac_to_use = sys.argv[2]
suffix = sys.argv[3]

print("n_darks", n_darks)

is_darks = [0]*len(exp_times) + [1]*n_darks
exp_times += [int(max_time)]*n_darks

exp_dark = list(zip(exp_times, is_darks))

random.shuffle(exp_dark)

exp_times = [item[0] for item in exp_dark]
is_darks = [item[1] for item in exp_dark]

print("exp_times", exp_times)
print("is_darks", is_darks)


            

im_count = 1

the_gain = 56



if len(exp_times) < 2:
    print("You're clearly testing, no need to wait")
else:
    print("Waiting 30s for you to leave")
    time.sleep(30)




CONTROL_GAIN = ctypes.c_int(6)
EXPOSURE_TIME = ctypes.c_int(8)
#depth = ctypes.c_uint32(8)
CONTROL_COOLER = ctypes.c_int(0)
CONTROL_OFFSET = ctypes.c_int(7)
CONTROL_CURTEMP = ctypes.c_short(14)

print("CONTROL_OFFSET", CONTROL_OFFSET)
#print("depth", depth)
print("bpp", bpp)

all_med_string = ""

for exp_time, is_dark in tqdm.tqdm(exp_dark):
    qhyccd.SetQHYCCDBitsMode(camera_handle, bpp)

    qhyccd.SetQHYCCDParam.restype = ctypes.c_uint32
    qhyccd.SetQHYCCDParam.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_double]

    qhyccd.SetQHYCCDParam(camera_handle, CONTROL_GAIN, ctypes.c_double(the_gain))
    qhyccd.SetQHYCCDParam(camera_handle, CONTROL_COOLER, ctypes.c_double(0))
    qhyccd.SetQHYCCDParam(camera_handle, EXPOSURE_TIME, ctypes.c_double(exp_time))
    
    qhyccd.SetQHYCCDParam(camera_handle, CONTROL_OFFSET, ctypes.c_double(10))
    qhyccd.SetQHYCCDResolution(camera_handle, ctypes.c_uint32(0), ctypes.c_uint32(0), maxImageSizeX, maxImageSizeY)
    qhyccd.SetQHYCCDBinMode(camera_handle, ctypes.c_uint32(1), ctypes.c_uint32(1))
    qhyccd.ExpQHYCCDSingleFrame(camera_handle)

    image_data = (ctypes.c_uint16 * maxImageSizeX.value * maxImageSizeY.value)()
    channels = ctypes.c_uint32(1)
    if not is_dark:
        do_it("ssh " + mac_to_use + " 'cd /Users/rubind/Dropbox/Hawaii/qhy_imaging;python drive_AD2.py %f %f &'" % (exp_time*1e-6 - 2.*before_after, before_after))
        
    print("Ready to expose")
    t = time.time()
    qhyccd.ExpQHYCCDSingleFrame(camera_handle)
    t2 = time.time()


    response = qhyccd.GetQHYCCDSingleFrame(
        camera_handle, ctypes.byref(maxImageSizeX), ctypes.byref(maxImageSizeY),
        ctypes.byref(bpp), ctypes.byref(channels), image_data,
    )
    t3 = time.time()

    print("Done. exp_time", exp_time, t2 - t, t3 - t2)

    #print("image_data", image_data, len(image_data))

    #print(image_data[0])
    #print(image_data[0][0])
    
    tmp_array = np.frombuffer(image_data, dtype=np.uint16)
    print("tmp_array", tmp_array, len(tmp_array))
    
    #bytes_data = bytearray(image_data)
    #print("hytes_data", bytes_data[0], bytes_data[1])
    
    #raw_array = numpy.array(bytes_data)
    #print("raw_array", raw_array)
    mono_image = tmp_array.reshape(maxImageSizeY.value, maxImageSizeX.value)


    mono_image = np.array(image_data)
    print("mono_image", mono_image)
    print("mono_image.shape", mono_image.shape)

    print('RESPONSE: %s' % response)


    hdu = fits.PrimaryHDU(mono_image)
    hdu.header["EXPTIME"] = exp_time/1e6
    hdu.header["EPTIME"] = time.time()
    hdu.header["GAIN"] = the_gain
    hdu.header["TIME"] = time.time()
    hdu.header["ASCTIME"] = time.asctime()
    hdu.header["CCDTEMP"] = qhyccd.GetQHYCCDParam(camera_handle, CONTROL_CURTEMP)
    hdul = fits.HDUList([hdu])
    hdul.writeto("img_%04i_flash_%s_exp_%.4g_gain_%03i_dark=%i.fits" % (im_count, suffix, exp_time/1e6, the_gain, is_dark), clobber = True)
    time.sleep(1)

    the_med = np.median(mono_image)
    print("Median", the_med)
    all_med_string += str(the_med) + "_"
    
    qhyccd.CancelQHYCCDExposingAndReadout(camera_handle)
    im_count += 1


            
qhyccd.CloseQHYCCD(camera_handle)
qhyccd.ReleaseQHYCCDResource()

do_it("ssh " + mac_to_use + " 'cd /Users/rubind/Dropbox/Hawaii/qhy_imaging;bash done.sh %s'" % all_med_string) 
