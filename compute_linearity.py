import glob
import numpy as np
import matplotlib.pyplot as plt
from astropy.io import fits
import tqdm

xs = []
ys = []

for fl in tqdm.tqdm(glob.glob("img*fits")):
    f = fits.open(fl)
    dat = f[0].data
    exptime = f[0].header["EXPTIME"]
    #exptime = np.around(exptime*1000)/1000.

    in_ap = []
    out_ap = []


    print(exptime)
    for i in range(4500, 5000):
        for j in range(2500, 3000):
            dist2 = (i - 4744)**2 + (j - 2765)**2
            if dist2 < 30**2:
                in_ap.append(dat[j,i])
            elif dist2 < 45**2:
                out_ap.append(dat[j,i])
                
    f.close()

    print(exptime, np.median(in_ap), np.median(out_ap))

    plt.plot(exptime, (np.mean(in_ap) - np.mean(out_ap))/exptime, '.', color = 'b')
    xs.append(exptime)
    ys.append((np.mean(in_ap) - np.mean(out_ap))/exptime)
    
plt.xscale('log')
plt.xlabel("Exposure Time (s)")
plt.ylabel("Background-Subtracted Average LED (ADU/second)")
plt.savefig("counts_vs_time.pdf")
plt.close()

xs = np.array(xs)
ys = np.array(ys)

inds = np.argsort(xs)
xs = xs[inds]
ys = ys[inds]

f = open("linearity.txt", 'w')
for i in range(len(xs)):
    f.write(str(xs[i]) + " " + str(ys[i]) + '\n')
f.close()
