import numpy as np
from scipy.ndimage import fourier_shift
import scipy.optimize

def integer_pixel_shift(a, shift):
    aOut = np.copy(a)
    aOut[1::2,...] = np.roll(a[1::2,...], shift=int(shift), axis=1)
    return aOut
    
def closest_pixel(a, plot=False):
    
    shifts = np.arange(-a[:,::2,...].shape[1], a[:,::2,...].shape[1])
    corrs = np.zeros(shifts.shape, dtype='float')
    for i, shift in enumerate(shifts):
        corrs[i] = -(a[::2,...]*np.roll(a[1::2,...], shift, axis=1)).sum() - (a[2::2,...]*np.roll(a[1:-1:2,...], shift, axis=1)).sum()
    
    optimalIntegerShift = shifts[np.argmin(corrs)]
    aOut = integer_pixel_shift(a, optimalIntegerShift)
    
    if plot:
        import matplotlib.pyplot as plt
        plt.ion()
        plt.plot(shifts, corrs, 'ko')
        plt.plot(optimalIntegerShift, np.min(corrs), 'ro')

    return optimalIntegerShift, aOut
    
def subpixel(a, plot=False):

    optIntShift, aTemp = closest_pixel(a, plot=plot)
    
    def func(x):
        return -(a[::2,...]*np.fft.ifftn(fourier_shift(np.fft.fftn(a[1::2,...]), [0, x[0]])).real).sum() - (a[2::2,...]*np.fft.ifftn(fourier_shift(np.fft.fftn(a[1:-1:2,...]), [0, x[0]])).real).sum()
    
    res = scipy.optimize.minimize(func, x0=[optIntShift], method='Nelder-Mead')
    if res['success']:
        optimalShift = res['x'][0]
        aOut = np.copy(a)
        aOut[1::2,...] = np.fft.ifftn(fourier_shift(np.fft.fftn(aOut[1::2,...]), [0, optimalShift])).real        
        
        if plot:
            upsample_factor=20
            shifts = np.arange(optIntShift-1, optIntShift+1, 1./upsample_factor)
            corrs = np.zeros(shifts.shape, dtype='float')
            for i, shift in enumerate(shifts):
                corrs[i] = func([shift])
                plt.plot(optimalShift, corrs.max(), 'rx')
                plt.plot(shifts, corrs, 'g.')
    
    return optimalShift, aOut

def shift_stack(a, shift):
    aOut = np.copy(a)
    shiftVector = np.zeros(a.ndim, dtype='float')
    shiftVector[1] = shift
    aOut[1::2,...] = np.fft.ifftn(fourier_shift(np.fft.fftn(aOut[1::2,...]), shiftVector)).real
    return aOut
    
