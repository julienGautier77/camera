# -*- coding: utf-8 -*-
"""
Phase retrieval of a focal spot from a focus scan (multi-plane
Gerchberg-Saxton type retrieval).

The focus motor takes one image (or the mean of several images) at nb steps
around the start position : z = (k - (nb-1)/2) * step. The scan must cover
several Rayleigh lengths (at least +-2 zR). Each image is recentered on its
center of mass (the spot can move when the focus moves).

Computation :
1. caustic : second moment (ISO 11146) width versus z gives the pupil
   radius, M², waist position and Rayleigh length
2. modal retrieval : Zernike phase + pupil amplitude fitted on all planes
   (avoids the stagnation of Gerchberg-Saxton started from a flat phase)
3. pixel retrieval : Gerchberg-Saxton error (measured amplitude in each
   plane, angular spectrum propagation) minimized pixel by pixel on the
   pupil field by L-BFGS, started from the modal result
4. Zernike decomposition (Noll) of the pupil phase, fitted on the phase
   gradients (no 2 pi ambiguity, no unwrapping needed)

Pixel size (um/pixel) comes from visu preferences (stepX, stepY) : use the
calibration window first. The motor displacement is assumed to be the
defocus in the same space as the pixel calibration.

@author: juliengautier
"""

from PyQt6 import QtCore
from PyQt6.QtWidgets import QApplication, QWidget, QFileDialog
from PyQt6.QtWidgets import QVBoxLayout, QHBoxLayout, QGridLayout, QGroupBox
from PyQt6.QtWidgets import QPushButton, QDoubleSpinBox, QSpinBox, QLineEdit
from PyQt6.QtWidgets import QLabel, QComboBox, QTabWidget, QProgressBar
from PyQt6.QtGui import QIcon, QFont
import sys
import time
import threading
import pathlib
import os
from math import factorial
import qdarkstyle
import numpy as np
import pyqtgraph as pg
from scipy import ndimage, fft
from scipy.optimize import minimize
import zmq_client_RSAI

ZERNIKE_NAMES = {1: 'Piston', 2: 'Tilt X', 3: 'Tilt Y', 4: 'Defocus',
                 5: 'Astig 45°', 6: 'Astig 0°', 7: 'Coma Y', 8: 'Coma X',
                 9: 'Trefoil Y', 10: 'Trefoil X', 11: 'Spherical',
                 12: '2nd Astig 0°', 13: '2nd Astig 45°',
                 14: 'Quadrafoil 0°', 15: 'Quadrafoil 45°'}
PRE_POINT = 0.5  # the motor goes 0.5 step before the first plane (hysteresis)
RHO_MAX_MODAL = 1.2  # modal phase frozen outside 1.2 pupil radius


# ---------------------------------------------------------------- Zernike

def nollToNM(j):
    '''
    Noll index j (1..) -> radial order n, azimuthal m (m < 0 : sin term)
    '''
    n = 0
    while j > (n + 1) * (n + 2) // 2:
        n += 1
    k = j - n * (n + 1) // 2 - 1
    m = n % 2 + 2 * ((k + (n + 1) % 2) // 2)
    if m != 0 and j % 2 == 1:
        m = -m
    return n, m


def zernike(j, rho, theta):
    '''
    Noll normalized Zernike polynomial (rms = 1 on the unit disk)
    '''
    n, m = nollToNM(j)
    ma = abs(m)
    R = np.zeros_like(rho)
    for s in range((n - ma) // 2 + 1):
        c = (-1)**s * factorial(n - s) / (factorial(s) * factorial((n + ma) // 2 - s) * factorial((n - ma) // 2 - s))
        R += c * rho**(n - 2 * s)
    if m == 0:
        return np.sqrt(n + 1) * R
    if m > 0:
        return np.sqrt(2 * (n + 1)) * R * np.cos(ma * theta)
    return np.sqrt(2 * (n + 1)) * R * np.sin(ma * theta)


def zernikeName(j):
    return ZERNIKE_NAMES.get(j, 'Z%d (n=%d m=%d)' % ((j,) + nollToNM(j)))


def zernikeFit(P, FX, FY, fc, nbZer):
    '''
    Fit the phase of the pupil field P on Zernike 1..nbZer.
    FX, FY : spatial frequency (um-1) of each pixel of P, fc : pupil radius (um-1)
    The fit is done on the wrapped phase differences between neighbour pixels
    (weighted by the amplitude) so no unwrapping is needed.
    Return coefficients (radian rms), pupil mask, fitted phase, measured wrapped phase
    '''
    u, v = FX / fc, FY / fc
    rho = np.hypot(u, v)
    theta = np.arctan2(v, u)
    mask = rho <= 1
    if np.count_nonzero(mask) < 3 * nbZer:
        raise ValueError('pupil too small (%d pixels) : increase the crop size' % np.count_nonzero(mask))
    Z = np.array([np.where(mask, zernike(j, rho, theta), 0) for j in range(1, nbZer + 1)])
    amp = np.abs(P)
    rows, rhs, wts = [], [], []
    for axis in (0, 1):
        sl1 = [slice(None)] * 2
        sl0 = [slice(None)] * 2
        sl1[axis] = slice(1, None)
        sl0[axis] = slice(None, -1)
        sl1, sl0 = tuple(sl1), tuple(sl0)
        valid = mask[sl1] & mask[sl0]
        g = np.angle(P[sl1] * np.conj(P[sl0]))[valid]  # wrapped phase difference
        dZ = (Z[(slice(None),) + sl1] - Z[(slice(None),) + sl0])[:, valid]
        rows.append(dZ[1:].T)  # piston has no gradient
        rhs.append(g)
        wts.append(np.sqrt(amp[sl1] * amp[sl0])[valid])
    A = np.concatenate(rows)
    b = np.concatenate(rhs)
    w = np.concatenate(wts)
    c = np.linalg.lstsq(A * w[:, None], b * w, rcond=None)[0]
    coeffs = np.concatenate([[0.], c])
    phaseFit = np.tensordot(coeffs, Z, axes=1)
    # piston : mean phase difference between the field and the fit
    piston = np.angle(np.sum((P * np.exp(-1j * phaseFit))[mask]))
    coeffs[0] = piston
    phaseFit = phaseFit + piston * mask
    wrapped = np.where(mask, np.angle(P), np.nan)
    phaseFit = np.where(mask, phaseFit, np.nan)
    return coeffs, mask, phaseFit, wrapped


# ---------------------------------------------------------- propagation

def freqGrid(N, dx, dy):
    '''
    spatial frequencies (um-1) of a N x N grid in fft order,
    axis 0 = X (dx um), axis 1 = Y (dy um)
    '''
    return np.meshgrid(np.fft.fftfreq(N, dx), np.fft.fftfreq(N, dy), indexing='ij')


def kzGrid(N, dx, dy, lam):
    '''
    angular spectrum propagation : field(z) = ifft2(A * exp(2i pi z kz))
    (piston 1/lam removed, evanescent waves set to kz = 0)
    '''
    FX, FY = freqGrid(N, dx, dy)
    arg = 1 / lam**2 - FX**2 - FY**2
    return np.where(arg > 0, np.sqrt(np.maximum(arg, 0)) - 1 / lam, 0)


def lossGrad(A, amps, Hs):
    '''
    Gerchberg-Saxton error : sum over planes of || |ifft2(A Hk)| - ak ||²
    and its gradient g = dL/dRe(A) + i dL/dIm(A)
    '''
    L = 0
    g = 0
    for a, Hk in zip(amps, Hs):
        E = fft.ifft2(A * Hk, workers=-1)
        m = np.abs(E)
        r = m - a
        L += np.sum(r**2)
        g = g + fft.fft2(r * E / np.maximum(m, 1e-15), workers=-1) * np.conj(Hk) / E.size
    return L, 2 * g


class Stopped(Exception):
    pass


def retrieve(amps, zs, lam, dx, dy, fc, nbZer, nIter, stop=None, progress=None):
    '''
    amps : measured amplitudes (fft order : spot center at pixel 0, sum a² = 1)
    zs : planes (um), fc : pupil radius (um-1) used for the modal step
    Return A the angular spectrum (fft order) of the field at z = 0,
    the modal coefficients and the error of each evaluation
    '''
    N = amps[0].shape[0]
    kz = kzGrid(N, dx, dy, lam)
    Hs = [np.exp(2j * np.pi * z * kz) for z in zs]
    FX, FY = freqGrid(N, dx, dy)
    rho = np.hypot(FX, FY) / fc
    theta = np.arctan2(FY, FX)
    Z = np.array([zernike(j, np.minimum(rho, RHO_MAX_MODAL), theta) for j in range(2, nbZer + 1)])
    nZ = len(Z)
    errors = []

    def check(L):
        errors.append(L / len(amps))
        if progress is not None:
            progress(len(errors), errors[-1])
        if stop is not None and stop():
            raise Stopped()

    # modal : Zernike phase + pixel amplitude, gaussian amplitude to start
    a0 = np.exp(-rho**2)
    a0 = a0 / np.sqrt(np.sum(a0**2) / a0.size)  # field energy = 1

    def fModal(x):
        e = np.exp(1j * np.tensordot(x[:nZ], Z, axes=1))
        amp = x[nZ:].reshape(a0.shape)
        A = amp * e
        L, g = lossGrad(A, amps, Hs)
        check(L)
        gAmp = np.real(np.conj(g) * e)
        gPhase = np.real(np.conj(g) * 1j * A)
        return L, np.concatenate([np.tensordot(Z, gPhase, axes=([1, 2], [0, 1])), gAmp.ravel()])

    opt = {'maxiter': nIter, 'maxfun': 2 * nIter, 'ftol': 1e-16, 'gtol': 1e-16}
    r = minimize(fModal, np.concatenate([np.zeros(nZ), a0.ravel()]), jac=True, method='L-BFGS-B', options=opt)
    cModal = r.x[:nZ]
    A = r.x[nZ:].reshape(a0.shape) * np.exp(1j * np.tensordot(cModal, Z, axes=1))

    # pixel : the complex pupil field is free
    def fPixel(x):
        A = (x[:x.size // 2] + 1j * x[x.size // 2:]).reshape(a0.shape)
        L, g = lossGrad(A, amps, Hs)
        check(L)
        return L, np.concatenate([g.real.ravel(), g.imag.ravel()])

    r = minimize(fPixel, np.concatenate([A.real.ravel(), A.imag.ravel()]), jac=True, method='L-BFGS-B', options=opt)
    A = (r.x[:r.x.size // 2] + 1j * r.x[r.x.size // 2:]).reshape(a0.shape)
    return A, np.concatenate([[0.], cModal]), errors


# ---------------------------------------------------------- images

def noiseLevel(img):
    '''
    background and noise rms (median, MAD) : the spot must be small in the image
    '''
    bg = np.median(img)
    return bg, 1.4826 * np.median(np.abs(img - bg))


def centerOfMass(img):
    '''
    center of mass of the spot (connected region above the noise)
    '''
    bg, sig = noiseLevel(img)
    d = spotOnly(img - bg, sig)
    if d.sum() <= 0:
        raise ValueError('no spot found')
    return ndimage.center_of_mass(d)


def spotOnly(d, sig):
    '''
    keep only the spot : smoothed image above noise, connected region
    containing the max, dilated. Other pixels (noise) set to 0
    '''
    sm = ndimage.gaussian_filter(d, 2)
    # noise of the smoothed image ~ sig/7 ; low floor to keep the wings (second moments)
    thr = max(3 * sig / 7, 0.002 * sm.max())
    labels, _ = ndimage.label(sm > thr)
    lab = labels[np.unravel_index(np.argmax(sm), sm.shape)]
    if lab == 0:
        return np.zeros_like(d)
    mask = ndimage.binary_dilation(labels == lab, iterations=3)
    return np.where(mask, np.clip(d, 0, None), 0)


def spotImage(img):
    '''
    full image with background removed and only the spot kept (noise = 0)
    '''
    bg, sig = noiseLevel(img)
    return spotOnly(img - bg, sig)


def binImage(d, b):
    '''
    sum of b x b pixels (the image is cut to a multiple of b)
    '''
    if b == 1:
        return d
    n0, n1 = d.shape[0] // b * b, d.shape[1] // b * b
    return d[:n0, :n1].reshape(n0 // b, b, n1 // b, b).sum(axis=(1, 3))


def intensityBandwidth(d):
    '''
    highest spatial frequency (cycle/pixel) of the spot image : radial mean of
    the power spectrum > 1e-4 of the DC and > 10 x the noise floor (measured
    near the Nyquist frequency). The intensity bandwidth is twice the pupil
    edge (1.5 x the 1/e² radius for a gaussian pupil, the edge for a flat top).
    Not changed by the aberration halo or clipped wings
    '''
    F = np.abs(fft.fft2(d, workers=-1))**2
    f0, f1 = np.meshgrid(np.fft.fftfreq(d.shape[0]), np.fft.fftfreq(d.shape[1]), indexing='ij')
    r = np.hypot(f0, f1)
    nb = min(d.shape) // 2  # one bin per frequency sample
    idx = np.minimum((r / 0.5 * nb).astype(int), nb)
    prof = ndimage.mean(F, labels=idx, index=np.arange(nb))
    floor = np.median(prof[int(0.8 * nb):])
    above = np.where(prof > max(10 * floor, 1e-4 * prof[0]))[0]
    return (above.max() + 1) / nb * 0.5 if len(above) else 0.5


def spotExtent(d):
    '''
    size (pixels) of the spot region (non zero pixels of spotOnly) and True if it
    touches the border of the camera (clipped spot)
    '''
    nz = np.argwhere(d > 0)
    if len(nz) == 0:
        return 0, False
    lo, hi = nz.min(axis=0), nz.max(axis=0)
    clipped = lo.min() <= 1 or hi[0] >= d.shape[0] - 2 or hi[1] >= d.shape[1] - 2
    return int((hi - lo).max()) + 1, clipped


def autoSampling(spots, zs, bin=0, N=0, pupilPx=30, nMax=1024):
    '''
    binning and crop size for the retrieval (spots : full resolution spot images)
    - binning : the binned intensity must stay above Nyquist : binned pixel
      <= 1/(3 fI) (fI : intensity bandwidth of the smallest spot).
      Big spots are strongly oversampled
    - crop : pupil edge fmax = fI/2 at about pupilPx pixels (pupil pixel =
      1/(N dx)), and 1.3 x the biggest spot (no wrap around). Outside the
      camera the crop is zero padded (no light there)
    bin or N = 0 : auto. Return bin, N, warning
    '''
    warn = []
    ext = [spotExtent(d) for d in spots]
    clipped = [z for (e, c), z in zip(ext, zs) if c]
    if clipped:
        warn.append('WARNING : spot clipped by the camera at z = %s um : reduce the scan range'
                    % ', '.join('%+.0f' % z for z in clipped))
    fI = intensityBandwidth(spots[int(np.argmin([e for e, c in ext]))])
    fmax = fI / 2  # pupil edge (cycle/pixel)
    if bin == 0:
        bin = max(1, int(1 / (3 * fI)))
    biggest = max(e for e, c in ext) / bin
    if N == 0:
        n1 = pupilPx / (fmax * bin)
        N = 64
        while N < max(n1, 1.3 * biggest) and N < nMax:
            N *= 2
    if biggest > N:
        warn.append('WARNING : spot (%d px binned) bigger than the crop (%d) : increase binning or crop' % (biggest, N))
    if fI * bin > 0.5:
        warn.append('WARNING : images undersampled after binning %d : reduce binning' % bin)
    return bin, N, '\n'.join(warn)


def cropCentered(d, com, N):
    '''
    N x N crop of d centered (sub pixel) on com (com at the pixel N//2),
    zero padded if the crop goes outside the image
    '''
    i0, i1 = int(np.floor(com[0])), int(np.floor(com[1]))
    h = N // 2 + 2
    big = np.zeros((2 * h, 2 * h))
    a0, a1 = max(i0 - h, 0), max(i1 - h, 0)
    b0, b1 = min(i0 + h, d.shape[0]), min(i1 + h, d.shape[1])
    big[a0 - (i0 - h):b0 - (i0 - h), a1 - (i1 - h):b1 - (i1 - h)] = d[a0:b0, a1:b1]
    # sub pixel shift so that com is at the center pixel N//2
    big = ndimage.shift(big, (-(com[0] - i0), -(com[1] - i1)), order=1)
    return np.clip(big[2:2 + N, 2:2 + N], 0, None)


def caustic(crops, zs, lam, dx, dy):
    '''
    second moment widths (ISO 11146) versus z for X and Y :
    sigma²(z) = a + b z + c z²  ->  waist, waist position, divergence, M², zR
    pupil radius (second moment, = 1/e² radius for a gaussian) :
    fc = sqrt(2 (cx + cy)) / lam
    '''
    res = {'z': np.array(zs)}
    fits = []
    for axis, step in ((0, dx), (1, dy)):
        s2 = []
        for I in crops:
            p = I.sum(axis=1 - axis)
            x = np.arange(len(p)) * step
            m = (p * x).sum() / p.sum()
            s2.append((p * (x - m)**2).sum() / p.sum())
        s2 = np.array(s2)
        a, b, c = np.polyfit(zs, s2, 2)[::-1]
        name = 'XY'[axis]
        res['w' + name] = 2 * np.sqrt(s2)  # second moment radius (um)
        res['fit' + name] = (a, b, c)
        if c > 0 and a - b**2 / (4 * c) > 0:
            w0 = 2 * np.sqrt(a - b**2 / (4 * c))
            theta = 2 * np.sqrt(c)
            res['w0' + name] = w0
            res['z0' + name] = -b / (2 * c)
            res['M2' + name] = np.pi * w0 * theta / lam  # w0 radius, theta half angle
            res['zR' + name] = w0 / theta
        fits.append(c)
    if min(fits) <= 0:
        raise ValueError('caustic fit failed (the spot size does not increase with defocus) : increase the scan range')
    res['fc'] = np.sqrt(2 * (fits[0] + fits[1])) / lam
    return res


def pupilRadius(P, FX, FY):
    '''
    second moment radius sqrt(2 <f²>) of the retrieved pupil intensity
    (= 1/e² radius for a gaussian, = radius for a flat top), computed on
    the pupil region only (connected region above 1% of the max)
    '''
    I = np.abs(P)**2
    labels, _ = ndimage.label(ndimage.gaussian_filter(I, 1) > 0.01 * I.max())
    region = labels == labels[np.unravel_index(np.argmax(I), I.shape)]
    I = np.where(ndimage.binary_dilation(region, iterations=2), I, 0)
    E = I.sum()
    mx, my = (I * FX).sum() / E, (I * FY).sum() / E
    return np.sqrt(2 * ((I * ((FX - mx)**2 + (FY - my)**2)).sum() / E))


# ---------------------------------------------------------- widget

class PHASE(QWidget):
    '''
    Phase retrieval widget
    CAM : CAMERA widget (camera.py), IpAdress, NoMotor : focus motor
    '''
    acqMain = QtCore.pyqtSignal()  # ask one image to the camera

    def __init__(self, CAM=None, IpAdress='', NoMotor=1, parent=None):
        super(PHASE, self).__init__()
        self.isWinOpen = False
        self.parent = parent
        self.CAM = CAM
        self.MOTs = {}
        self.setStyleSheet(qdarkstyle.load_stylesheet(qt_api='pyqt6'))
        p = pathlib.Path(__file__)
        self.setWindowIcon(QIcon(str(p.parent) + os.sep + 'icons' + os.sep + 'LOA.png'))
        self.setWindowTitle('Phase retrieval')
        self.imageEvent = threading.Event()
        self.lastImage = None
        self.images = []  # (z um, averaged image, center of mass)
        self.result = None
        self.setup(IpAdress, NoMotor)
        self.actionButton()
        self.threadAcq = ThreadAcqPhase(self)
        self.threadAcq.acq.connect(self.acqMain.emit)
        self.threadAcq.info.connect(self.infoLabel.setText)
        self.threadAcq.stepDone.connect(self.stepDone)
        self.threadAcq.finished.connect(self.acqDone)
        self.threadCompute = ThreadCompute(self)
        self.threadCompute.progress.connect(self.computeProgress)
        self.threadCompute.info.connect(lambda t: self.infoLabel.setText(self.causticInfo + t))
        self.causticInfo = ''  # waist and M² kept above the progress messages
        self.threadCompute.causticDone.connect(self.causticReady)
        self.threadCompute.cropsDone.connect(self.showCrops)
        self.threadCompute.done.connect(self.computeDone)
        self.threadCompute.finished.connect(lambda: self.setRunning(False))
        self.resize(1300, 800)

    # ----- parameters saved in the camera ini file
    def confValue(self, key, default):
        try:
            v = self.CAM.conf.value(self.CAM.nbcam + '/phase' + key)
            return default if v is None else v
        except Exception:
            return default

    def confSave(self):
        if self.CAM is None:
            return
        for key, w in self.params.items():
            if isinstance(w, QLineEdit):
                v = w.text()
            elif isinstance(w, QComboBox):
                v = w.currentText()
            else:
                v = w.value()
            self.CAM.conf.setValue(self.CAM.nbcam + '/phase' + key, v)

    def spin(self, key, default, mini, maxi, decimals=0, suffix=''):
        if decimals == 0:
            w = QSpinBox()
            w.setRange(int(mini), int(maxi))
            w.setValue(int(float(self.confValue(key, default))))
        else:
            w = QDoubleSpinBox()
            w.setDecimals(decimals)
            w.setRange(mini, maxi)
            w.setValue(float(self.confValue(key, default)))
        w.setSuffix(suffix)
        self.params[key] = w
        return w

    def setup(self, IpAdress, NoMotor):
        self.params = {}
        hMain = QHBoxLayout(self)

        # ---- left : parameters
        left = QWidget()
        left.setFixedWidth(300)
        vLeft = QVBoxLayout(left)
        vLeft.setContentsMargins(0, 0, 0, 0)

        groupMot = QGroupBox('Focus scan')
        g = QGridLayout(groupMot)
        self.ipBox = QLineEdit(str(self.confValue('Ip', IpAdress)))
        self.params['Ip'] = self.ipBox
        g.addWidget(QLabel('Rack IP'), 0, 0)
        g.addWidget(self.ipBox, 0, 1)
        g.addWidget(QLabel('Motor n°'), 1, 0)
        g.addWidget(self.spin('Mot', NoMotor, 1, 100), 1, 1)
        g.addWidget(QLabel('Nb of steps'), 2, 0)
        g.addWidget(self.spin('NbStep', 9, 4, 51), 2, 1)
        g.addWidget(QLabel('Step'), 3, 0)
        g.addWidget(self.spin('Step', 500, 0.1, 100000, 1, ' um'), 3, 1)
        self.rangeLabel = QLabel('')
        g.addWidget(self.rangeLabel, 4, 0, 1, 2)
        g.addWidget(QLabel('Images / step'), 5, 0)
        g.addWidget(self.spin('NbAvg', 1, 1, 100), 5, 1)
        g.addWidget(QLabel('Wait after move'), 6, 0)
        g.addWidget(self.spin('Wait', 0.5, 0, 10, 1, ' s'), 6, 1)
        vLeft.addWidget(groupMot)

        groupOpt = QGroupBox('Optics')
        g = QGridLayout(groupOpt)
        g.addWidget(QLabel('Wavelength'), 0, 0)
        g.addWidget(self.spin('Lambda', 800, 100, 20000, 1, ' nm'), 0, 1, 1, 2)
        g.addWidget(QLabel('Pixel X'), 1, 0)
        self.pixX = QDoubleSpinBox()
        self.pixY = QDoubleSpinBox()
        for w in (self.pixX, self.pixY):
            w.setDecimals(4)
            w.setRange(0.0001, 10000)
            w.setSuffix(' um')
        g.addWidget(self.pixX, 1, 1)
        g.addWidget(QLabel('Pixel Y'), 2, 0)
        g.addWidget(self.pixY, 2, 1)
        self.pixButton = QPushButton('visu')
        self.pixButton.setToolTip('read the calibration (stepX, stepY) of visu preferences')
        g.addWidget(self.pixButton, 1, 2, 2, 1)
        g.addWidget(QLabel('Zernike radius'), 3, 0)
        na = self.spin('NA', 0, 0, 1, 4, ' NA')
        na.setSpecialValueText('auto (pupil)')
        na.setToolTip('pupil radius of the Zernike decomposition\n'
                      'auto : second moment radius of the retrieved pupil intensity (1/e² for a gaussian beam)')
        g.addWidget(na, 3, 1, 1, 2)
        vLeft.addWidget(groupOpt)
        self.readPixelSize()

        groupGS = QGroupBox('Computation')
        g = QGridLayout(groupGS)
        g.addWidget(QLabel('Crop size'), 0, 0)
        self.cropBox = QComboBox()
        self.cropBox.addItems(['auto', '64', '128', '256', '512', '1024'])
        self.cropBox.setCurrentText(str(self.confValue('Crop', 'auto')))
        self.cropBox.setToolTip('crop size (binned pixels) used for the computation\n'
                                'auto : pupil sampled with about 15 pixels of radius')
        self.params['Crop'] = self.cropBox
        g.addWidget(self.cropBox, 0, 1)
        g.addWidget(QLabel('Binning'), 0, 2)
        self.binBox = QComboBox()
        self.binBox.addItems(['auto', '1', '2', '4', '8', '16', '32', '64'])
        self.binBox.setCurrentText(str(self.confValue('Bin', 'auto')))
        self.binBox.setToolTip('binning of the images before the computation\n'
                               'auto : binned pixel = 1/(4 pupil radius) (from the divergence)')
        self.params['Bin'] = self.binBox
        g.addWidget(self.binBox, 0, 3)
        g.addWidget(QLabel('Iterations'), 1, 0)
        it = self.spin('Iter', 150, 10, 5000)
        it.setToolTip('iterations of each step (modal then pixel)')
        g.addWidget(it, 1, 1)
        g.addWidget(QLabel('Nb of Zernike'), 2, 0)
        g.addWidget(self.spin('NbZer', 15, 4, 66), 2, 1)
        vLeft.addWidget(groupGS)

        self.playButton = QPushButton('Acquire and compute')
        self.playButton.setMinimumHeight(32)
        self.stopButton = QPushButton('STOP')
        self.stopButton.setMinimumHeight(32)
        self.stopButton.setStyleSheet('background-color: #d32f2f; color: white; font: bold 11pt; border-radius: 4px')
        self.stopButton.setEnabled(False)
        self.computeButton = QPushButton('Compute again')
        self.computeButton.setToolTip('compute with the last images (after changing computation parameters)')
        self.computeButton.setEnabled(False)
        self.saveButton = QPushButton('Save')
        self.saveButton.setEnabled(False)
        vLeft.addWidget(self.playButton)
        vLeft.addWidget(self.stopButton)
        hb = QHBoxLayout()
        hb.addWidget(self.computeButton)
        hb.addWidget(self.saveButton)
        vLeft.addLayout(hb)
        self.progress = QProgressBar()
        self.progress.setTextVisible(False)
        self.progress.setMaximumHeight(8)
        vLeft.addWidget(self.progress)
        self.infoLabel = QLabel('')
        self.infoLabel.setWordWrap(True)
        vLeft.addWidget(self.infoLabel)
        vLeft.addStretch(1)
        hMain.addWidget(left)

        # ---- right : tabs
        self.tabs = QTabWidget()
        self.imagesWidget = pg.GraphicsLayoutWidget()
        self.tabs.addTab(self.imagesWidget, 'Images')
        self.cropsWidget = pg.GraphicsLayoutWidget()
        self.tabs.addTab(self.cropsWidget, 'Crops (computation)')

        phaseTab = QWidget()
        vPhase = QVBoxLayout(phaseTab)
        self.phaseWidget = pg.GraphicsLayoutWidget()
        vPhase.addWidget(self.phaseWidget, 3)
        hPlots = QHBoxLayout()
        self.causticPlot = pg.PlotWidget(title='Caustic (second moment radius)')
        self.causticPlot.setLabel('bottom', 'z', units='um')
        self.causticPlot.setLabel('left', 'w (um)')
        self.causticPlot.showGrid(x=True, y=True)
        self.causticPlot.addLegend()
        hPlots.addWidget(self.causticPlot)
        self.errorPlot = pg.PlotWidget(title='Retrieval error (modal then pixel)')
        self.errorPlot.setLabel('bottom', 'evaluation')
        self.errorPlot.setLogMode(y=True)
        self.errorPlot.showGrid(x=True, y=True)
        self.errorCurve = self.errorPlot.plot(pen=pg.mkPen('y', width=2))
        hPlots.addWidget(self.errorPlot)
        vPhase.addLayout(hPlots, 2)
        self.tabs.addTab(phaseTab, 'Phase')
        self.setupPhaseTab()

        zerTab = QWidget()
        hZer = QHBoxLayout(zerTab)
        self.zerPlot = pg.PlotWidget()
        self.zerPlot.setLabel('bottom', 'Zernike (Noll)')
        self.zerPlot.setLabel('left', 'rms (wave)')
        self.zerPlot.showGrid(y=True)
        hZer.addWidget(self.zerPlot, 3)
        self.zerLabel = QLabel('')
        self.zerLabel.setFont(QFont('Consolas', 9))
        self.zerLabel.setAlignment(QtCore.Qt.AlignmentFlag.AlignTop)
        self.zerLabel.setTextInteractionFlags(QtCore.Qt.TextInteractionFlag.TextSelectableByMouse)
        hZer.addWidget(self.zerLabel, 2)
        self.tabs.addTab(zerTab, 'Zernike')
        hMain.addWidget(self.tabs, 1)
        self.tabs.currentChanged.connect(self.tabChanged)
        self.updateRange()

    def setupPhaseTab(self):
        self.phaseImages = {}
        titles = (('amp', 'Pupil intensity', 'inferno'),
                  ('wrapped', 'Measured phase, no tilt/defocus (rad)', 'CET-C6'),
                  ('fit', 'Zernike fit j>=5 (wave)', 'CET-D1'),
                  ('focus', 'Retrieved spot (z = 0)', 'inferno'))
        for i, (key, title, cmap) in enumerate(titles):
            p = self.phaseWidget.addPlot(row=0, col=2 * i, title=title)
            p.setAspectLocked(True)
            p.hideAxis('left')
            p.hideAxis('bottom')
            img = pg.ImageItem()
            p.addItem(img)
            bar = pg.ColorBarItem(colorMap=pg.colormap.get(cmap), interactive=False, width=12)
            bar.setImageItem(img)
            self.phaseWidget.addItem(bar, row=0, col=2 * i + 1)
            self.phaseImages[key] = (img, bar)

    def actionButton(self):
        self.playButton.clicked.connect(self.startAcq)
        self.stopButton.clicked.connect(self.stopAll)
        self.computeButton.clicked.connect(self.startCompute)
        self.saveButton.clicked.connect(self.save)
        self.pixButton.clicked.connect(self.readPixelSize)
        self.params['NbStep'].valueChanged.connect(self.updateRange)
        self.params['Step'].valueChanged.connect(self.updateRange)
        if self.CAM is not None:
            self.CAM.signalData.connect(self.imageReceived)

    def updateRange(self):
        nb = self.params['NbStep'].value()
        half = (nb - 1) / 2 * self.params['Step'].value()
        txt = 'scan : -%.0f .. +%.0f um' % (half, half)
        zR = getattr(self, 'lastZR', None)
        if zR:
            txt += '  (+-%.1f zR)' % (half / zR)
        self.rangeLabel.setText(txt)

    def winPref(self):
        try:
            return self.CAM.visualisation.winPref
        except Exception:
            return None

    def readPixelSize(self):
        pref = self.winPref()
        if pref is not None:
            self.pixX.setValue(pref.stepX)
            self.pixY.setValue(pref.stepY)
        elif self.pixX.value() == 0:
            self.pixX.setValue(1)
            self.pixY.setValue(1)

    def imageReceived(self, data):
        if self.threadAcq.isRunning():
            # same rotation as visu display so that X and Y match the pixel calibration
            pref = self.winPref()
            rot = pref.rotateValue if pref is not None else 0
            self.lastImage = np.rot90(np.array(data, dtype=np.float32), rot)
            self.imageEvent.set()

    def getMotor(self):
        ip = self.ipBox.text().strip()
        no = self.params['Mot'].value()
        if (ip, no) not in self.MOTs:
            self.MOTs[(ip, no)] = zmq_client_RSAI.MOTORRSAI(ip, no)
        return self.MOTs[(ip, no)]

    def setRunning(self, state):
        for w in list(self.params.values()) + [self.pixX, self.pixY, self.pixButton, self.playButton]:
            w.setEnabled(not state)
        self.stopButton.setEnabled(state)
        self.computeButton.setEnabled(not state and len(self.images) >= 3)
        self.saveButton.setEnabled(not state and self.result is not None)

    # ----- acquisition
    def stopCamera(self):
        '''
        stop the continuous acquisition of the camera (the images are then
        taken one by one) : acquiring while running makes the camera crash
        '''
        if self.CAM is None:
            return
        stopButton = getattr(self.CAM, 'stopButton', None)
        running = (stopButton is not None and stopButton.isEnabled()) or \
            getattr(getattr(self.CAM, 'CAM', None), 'camIsRunning', False)
        if running:
            self.infoLabel.setText('stop camera ...')
            self.CAM.stopAcq()
            t0 = time.time()
            while time.time() - t0 < 0.5:  # let the camera thread finish
                QApplication.processEvents()

    def startAcq(self):
        self.stopCamera()
        self.confSave()
        self.infoLabel.setText('connecting motor ...')
        QApplication.processEvents()
        self.threadAcq.MOT = self.getMotor()
        nb = self.params['NbStep'].value()
        step = self.params['Step'].value()
        self.threadAcq.zs = [(k - (nb - 1) / 2) * step for k in range(nb)]
        self.threadAcq.nbAvg = self.params['NbAvg'].value()
        self.threadAcq.waitTime = self.params['Wait'].value()
        self.images = []
        self.result = None
        self.imagesWidget.clear()
        self.viewCenter = None
        self.progress.setRange(0, nb)
        self.progress.setValue(0)
        self.tabs.setCurrentIndex(0)
        self.setRunning(True)
        self.threadAcq.start()

    def stepDone(self, k, z, img):
        try:
            com = centerOfMass(img)
        except ValueError:
            com = (img.shape[0] / 2, img.shape[1] / 2)
            self.infoLabel.setText('no spot found at z = %.1f um' % z)
        self.images.append((z, img, com))
        self.progress.setValue(k + 1)
        self.showStep(k, z, img, com)

    def showStep(self, k, z, img, com):
        '''
        image of the step with a cross on the center of mass. The full image
        is displayed (zoom with the mouse), the views of all the steps are
        linked. Initial zoom : the whole spot of the first step (region above
        the noise, halo included) + 50 %, the same for all steps so the walk
        of the spot is visible. sqrt of the intensity to see the wings
        '''
        if self.viewCenter is None:
            d = spotImage(img)
            nz = np.argwhere(d > 0)
            if len(nz):
                lo, hi = nz.min(axis=0), nz.max(axis=0)
                self.viewCenter = ((lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2)
                self.viewSize = max(1.5 * (hi - lo).max(), 64)
            else:
                self.viewCenter = (com[0], com[1])
                self.viewSize = max(img.shape)
        nbCol = min(max(int(np.ceil(np.sqrt(len(self.threadAcq.zs) * 1.5))), 3), 6)
        row, col = 2 * (k // nbCol), k % nbCol
        self.imagesWidget.addLabel('z = %+.1f um   com (%.1f, %.1f)' % (z, com[0], com[1]), row=row, col=col, size='9pt')
        vb = self.imagesWidget.addViewBox(row=row + 1, col=col)
        vb.setAspectLocked(True)
        im = pg.ImageItem(np.sqrt(np.clip(img - np.median(img), 0, None)), autoDownsample=True)
        im.setColorMap(pg.colormap.get('inferno'))
        vb.addItem(im)
        cross = pg.ScatterPlotItem([com[0] + 0.5], [com[1] + 0.5], symbol='+', size=22,
                                   pen=pg.mkPen('c', width=2), brush=None)
        vb.addItem(cross)
        if k == 0:
            self.firstView = vb
        else:
            vb.setXLink(self.firstView)
            vb.setYLink(self.firstView)
        c0, c1 = self.viewCenter
        h = self.viewSize / 2
        vb.setRange(xRange=(c0 - h, c0 + h), yRange=(c1 - h, c1 + h), padding=0)

    def acqDone(self):
        if self.threadAcq.stop or len(self.images) != len(self.threadAcq.zs):
            self.setRunning(False)
            if not self.threadAcq.error:
                self.infoLabel.setText('acquisition stopped')
            return
        self.startCompute()

    # ----- computation
    def startCompute(self):
        self.confSave()
        if len(self.images) < 3:
            return
        self.threadCompute.stop = False
        nIter = self.params['Iter'].value()
        self.threadCompute.args = dict(
            images=self.images,
            N=0 if self.cropBox.currentText() == 'auto' else int(self.cropBox.currentText()),
            bin=0 if self.binBox.currentText() == 'auto' else int(self.binBox.currentText()),
            lam=self.params['Lambda'].value() / 1000, dx=self.pixX.value(), dy=self.pixY.value(),
            nIter=nIter, NA=self.params['NA'].value(), nbZer=self.params['NbZer'].value())
        self.progress.setRange(0, 2 * nIter)
        self.progress.setValue(0)
        self.errors = []
        self.errorCurve.setData([], [])
        self.causticInfo = ''
        self.cropWarn = ''
        self.cropsWidget.clear()
        self.setRunning(True)
        self.threadCompute.start()

    def computeProgress(self, it, err):
        self.errors.append(err)
        self.progress.setValue(it)
        if it % 10 == 0:
            self.errorCurve.setData(np.arange(1, len(self.errors) + 1), self.errors)

    def computeDone(self, res):
        if 'error' in res:
            self.infoLabel.setText('error : %s' % res['error'])
            return
        self.result = res
        self.errorCurve.setData(np.arange(1, len(res['errors']) + 1), res['errors'])
        self.showCaustic(res['caustic'])
        self.showPhase(res)
        self.showZernike(res)
        self.infoLabel.setText(self.causticText(res))
        self.tabs.setCurrentIndex(3)  # Zernike

    def causticText(self, res):
        c = res['caustic']
        txt = 'binning %d, crop %d, pupil radius %.0f px\n' % (res['bin'], res['N'], res['pupilPx'])
        if res['warn']:
            txt += res['warn'] + '\n'
        if getattr(self, 'cropWarn', ''):
            txt += self.cropWarn + '\n'
        txt += 'Zernike radius NA %.4f%s\n' % (res['NA'], ' (auto)' if res['NAauto'] else '')
        for a in 'XY':
            if 'M2' + a in c:
                txt += '%s : w0 %.1f um  z0 %+.0f um  M² %.2f  zR %.0f um\n' % (
                    a, c['w0' + a], c['z0' + a], c['M2' + a], c['zR' + a])
        # phase diversity : Rayleigh length of the pupil (diffraction limited beam
        # with this NA), not the one of the caustic which increases with the aberrations
        zR = res['lam'] / (np.pi * res['NA']**2)
        self.lastZR = zR
        self.updateRange()
        half = (np.max(c['z']) - np.min(c['z'])) / 2
        txt += 'scan +-%.1f zR (zR = lambda/(pi NA²) = %.0f um), defocus at the edge %.2f wave PV' % (
            half / zR, zR, half * res['NA']**2 / (2 * res['lam']))
        if half < 3 * zR:
            txt += '\nWARNING : scan at least +-3 zR (step %.0f um)' % (6 * zR / (len(c['z']) - 1))
        return txt

    def showCaustic(self, c):
        '''
        second moment radius versus z, fit w²(z) (ISO 11146), waist position
        (dashed line) ; w0, z0, M² of each axis in the legend and the title
        '''
        self.causticPlot.clear()
        zf = np.linspace(c['z'].min(), c['z'].max(), 200)
        title = []
        for a, col in (('X', 'r'), ('Y', 'c')):
            if 'M2' + a in c:
                name = '%s : w0 %.1f um, M² %.2f' % (a, c['w0' + a], c['M2' + a])
                title.append('%s w0 %.1f um  z0 %+.0f um  M² %.2f' % (a, c['w0' + a], c['z0' + a], c['M2' + a]))
                self.causticPlot.addItem(pg.InfiniteLine(c['z0' + a], angle=90,
                                                         pen=pg.mkPen(col, width=1, style=QtCore.Qt.PenStyle.DashLine)))
            else:
                name = '%s : no waist in the fit' % a
            self.causticPlot.plot(c['z'], c['w' + a], pen=None, symbol='o', symbolBrush=col, name=name)
            aa, bb, cc = c['fit' + a]
            self.causticPlot.plot(zf, 2 * np.sqrt(np.clip(aa + bb * zf + cc * zf**2, 0, None)), pen=pg.mkPen(col, width=2))
        self.causticPlot.setTitle('<br>'.join(title) if title else 'Caustic (second moment radius)', size='9pt')

    def causticReady(self, c):
        '''
        caustic computed (before the phase retrieval) : display it
        '''
        self.showCaustic(c)
        self.tabs.setCurrentIndex(2)  # Phase
        txt = ''
        for a in 'XY':
            if 'M2' + a in c:
                txt += '%s : w0 %.1f um  z0 %+.0f um  M² %.2f  zR %.0f um\n' % (
                    a, c['w0' + a], c['z0' + a], c['M2' + a], c['zR' + a])
        self.causticInfo = txt
        self.infoLabel.setText(txt + 'phase retrieval ...')

    def showCrops(self, c):
        '''
        binned and cropped images used by the retrieval (log scale, 4 decades),
        with the fraction of the energy on the border of the crop : if the spot
        touches the border it is cut (red title)
        '''
        self.cropsWidget.clear()
        self.cropViews = []
        nbCol = min(max(int(np.ceil(np.sqrt(len(c['crops']) * 1.5))), 3), 6)
        cut = []
        first = None
        for k, (z, I) in enumerate(zip(c['z'], c['crops'])):
            e = 3  # border width (pixels)
            inner = I[e:-e, e:-e].sum()
            edge = max((I.sum() - inner) / max(I.sum(), 1e-12), 0)
            color = '#ff5252' if edge > 1e-3 else '#dddddd'
            if edge > 1e-3:
                cut.append('%+.0f' % z)
            row, col = 2 * (k // nbCol), k % nbCol
            self.cropsWidget.addLabel('z = %+.0f um   border %.2f %%' % (z, 100 * edge),
                                      row=row, col=col, size='9pt', color=color)
            vb = self.cropsWidget.addViewBox(row=row + 1, col=col)
            vb.setAspectLocked(True)
            # log scale over 4 decades : the faint wings near the border are visible
            m = max(I.max(), 1e-30)
            im = pg.ImageItem(np.log10(np.clip(I, m * 1e-4, None) / m), levels=(-4, 0))
            im.setColorMap(pg.colormap.get('inferno'))
            vb.addItem(im)
            frame = pg.QtWidgets.QGraphicsRectItem(0, 0, I.shape[0], I.shape[1])  # crop border
            frame.setPen(pg.mkPen(color, width=2, cosmetic=True))
            vb.addItem(frame)
            vb.addItem(pg.ScatterPlotItem([I.shape[0] // 2 + 0.5], [I.shape[1] // 2 + 0.5], symbol='+',
                                          size=14, pen=pg.mkPen('c', width=1), brush=None))
            if first is None:
                first = vb
            else:
                vb.setXLink(first)
                vb.setYLink(first)
            self.cropViews.append((vb, I.shape))
        self.fitCropViews()
        txt = 'binning %d, crop %d x %d (= %d x %d camera pixels)' % (c['bin'], c['N'], c['N'], c['N'] * c['bin'], c['N'] * c['bin'])
        self.cropWarn = ''
        if cut:
            self.cropWarn = 'WARNING : spot cut by the crop at z = %s um : increase the crop or the binning' % ', '.join(cut)
            txt += '\n' + self.cropWarn
        self.causticInfo += txt + '\n'
        self.infoLabel.setText(self.causticInfo)

    def fitCropViews(self):
        '''
        zoom on the whole crop. Done again when the tab is shown : the views
        created in a hidden tab have no size and ignore the range
        '''
        for vb, shape in getattr(self, 'cropViews', []):
            vb.setRange(xRange=(0, shape[0]), yRange=(0, shape[1]), padding=0.02)

    def tabChanged(self, i):
        if self.tabs.widget(i) is self.cropsWidget:
            QtCore.QTimer.singleShot(0, self.fitCropViews)

    def showPhase(self, res):
        # display the pupil region only (+-1.5 pupil radius)
        u = res['FX'] / res['fc']
        v = res['FY'] / res['fc']
        rows = np.where(np.abs(u[:, 0]) <= 1.5)[0]
        cols = np.where(np.abs(v[0, :]) <= 1.5)[0]
        sl = (slice(rows.min(), rows.max() + 1), slice(cols.min(), cols.max() + 1))
        amp = np.abs(res['P'][sl])**2
        data = {'amp': (amp, (0, amp.max())),
                'wrapped': (res['wrapped'][sl], (-np.pi, np.pi)),
                'fit': (res['phaseFit'][sl] / (2 * np.pi), None),
                'focus': (np.abs(res['E0'])**2, None)}
        for key, (d, levels) in data.items():
            img, bar = self.phaseImages[key]
            img.setImage(d)
            if levels is None:
                m = np.nanmax(np.abs(d)) if key == 'fit' else np.nanmax(d)
                levels = (-m, m) if key == 'fit' else (0, m)
            if not np.all(np.isfinite(levels)) or levels[0] == levels[1]:
                levels = (0, 1)
            bar.setLevels(levels)

    def showZernike(self, res):
        '''
        Zernike j >= 5 only : tilts are meaningless (recentered images) and
        the defocus is relative to the start position
        '''
        c = res['coeffs'] / (2 * np.pi)  # wave rms
        lamNm = res['lam'] * 1000
        js = np.arange(5, len(c) + 1)
        self.zerPlot.clear()
        self.zerPlot.addItem(pg.BarGraphItem(x=js, height=c[js - 1], width=0.7, brush='#29b6f6'))
        self.zerPlot.getAxis('bottom').setTicks([[(int(j), str(j)) for j in js]])
        txt = ' j  %-16s %9s %9s\n' % ('', 'wave rms', 'nm rms')
        for j in js:
            txt += '%2d  %-16s %9.4f %9.1f\n' % (j, zernikeName(j), c[j - 1], c[j - 1] * lamNm)
        rmsAb = np.sqrt(np.sum(c[4:]**2))
        txt += '\nrms (j>=5)                 %9.4f %9.1f\n' % (rmsAb, rmsAb * lamNm)
        txt += 'Strehl (Marechal)          %9.3f\n' % np.exp(-(2 * np.pi * rmsAb)**2)
        txt += '\nZernike radius NA %.4f (%s)\n' % (res['NA'], 'auto' if res['NAauto'] else 'manual')
        txt += 'Tilts and defocus not shown (recentered images,\n'
        txt += 'defocus relative to the start position).'
        self.zerLabel.setText(txt)

    def stopAll(self):
        self.threadAcq.stopThread()
        self.threadCompute.stop = True
        for MOT in self.MOTs.values():
            MOT.stopMotor()

    def save(self):
        if self.result is None:
            return
        try:
            path = str(self.CAM.conf.value(self.CAM.nbcam + '/path'))
        except Exception:
            path = ''
        fname, _ = QFileDialog.getSaveFileName(self, 'Save phase retrieval', path + '/phase_' + time.strftime('%Y%m%d_%H%M%S'), 'numpy (*.npz)')
        if not fname:
            return
        fname = os.path.splitext(fname)[0]
        res = self.result
        np.savez_compressed(fname + '.npz', z=[i[0] for i in self.images], images=np.array([i[1] for i in self.images]),
                            com=[i[2] for i in self.images], field=res['E0'], pupil=res['P'], zernikeRad=res['coeffs'],
                            wavelength_um=res['lam'], pixel_um=(res['dx'], res['dy']), NA=res['NA'], errors=res['errors'])
        with open(fname + '_zernike.txt', 'w', encoding='utf-8') as f:
            f.write(self.infoLabel.text() + '\n\n' + self.zerLabel.text())
        self.infoLabel.setText('saved : ' + fname + '.npz')

    def closeEvent(self, event):
        self.stopAll()
        self.threadAcq.wait(2000)
        self.threadCompute.wait(2000)
        self.isWinOpen = False
        event.accept()


class ThreadAcqPhase(QtCore.QThread):
    '''
    move the focus motor on each plane (always in the same direction) and
    take the mean of nbAvg images on each plane, go back to start at the end
    '''
    acq = QtCore.pyqtSignal()
    info = QtCore.pyqtSignal(str)
    stepDone = QtCore.pyqtSignal(int, float, object)

    def __init__(self, parent=None):
        super(ThreadAcqPhase, self).__init__(parent)
        self.parent = parent
        self.stop = False
        self.error = False
        self.MOT = None
        self.zs = []
        self.nbAvg = 1
        self.waitTime = 0  # not 'wait' : QThread.wait()

    def moveAndWait(self, pos, tol=10, timeout=60):
        self.MOT.move(pos)
        t0 = time.time()
        while not self.stop:
            b = self.MOT.position()
            if abs(b - pos) <= tol:
                return True
            if time.time() - t0 > timeout:
                raise TimeoutError('motor did not reach %d (pos %s)' % (pos, b))
            time.sleep(0.1)
        return False

    def takeImage(self, timeout=30):
        self.parent.imageEvent.clear()
        self.acq.emit()
        t0 = time.time()
        while not self.stop:
            if self.parent.imageEvent.wait(0.1):
                return self.parent.lastImage
            if time.time() - t0 > timeout:
                raise TimeoutError('no image received from camera')
        return None

    def run(self):
        self.stop = False
        self.error = False
        stepPerUm = self.MOT.getStepValue()
        p0 = int(self.MOT.position())
        step = self.zs[1] - self.zs[0]
        try:
            pre = int(round(p0 + (self.zs[0] - PRE_POINT * step) * stepPerUm))
            self.info.emit('pre-position ...')
            if not self.moveAndWait(pre):
                return
            for k, z in enumerate(self.zs):
                if self.stop:
                    break
                pos = int(round(p0 + z * stepPerUm))
                self.info.emit('step %d/%d : moving to %+.1f um ...' % (k + 1, len(self.zs), z))
                if not self.moveAndWait(pos):
                    break
                time.sleep(self.waitTime)
                acc = None
                for n in range(self.nbAvg):
                    self.info.emit('step %d/%d : image %d/%d' % (k + 1, len(self.zs), n + 1, self.nbAvg))
                    data = self.takeImage()
                    if data is None:
                        break
                    acc = data.astype(np.float64) if acc is None else acc + data
                if self.stop or acc is None:
                    break
                self.stepDone.emit(k, float(z), (acc / self.nbAvg).astype(np.float32))
        except Exception as e:
            self.error = True
            print('phase acquisition error :', e)
            self.info.emit('error : %s' % e)
        finally:
            self.MOT.move(p0)

    def stopThread(self):
        self.stop = True


class ThreadCompute(QtCore.QThread):
    '''
    recenter the images, caustic, retrieval, pupil and Zernike fit
    '''
    progress = QtCore.pyqtSignal(int, float)
    info = QtCore.pyqtSignal(str)
    causticDone = QtCore.pyqtSignal(object)  # caustic available before the retrieval
    cropsDone = QtCore.pyqtSignal(object)  # binned and cropped images used by the retrieval
    done = QtCore.pyqtSignal(object)

    def __init__(self, parent=None):
        super(ThreadCompute, self).__init__(parent)
        self.stop = False
        self.args = {}

    def run(self):
        try:
            self.done.emit(self.compute(**self.args))
        except Stopped:
            self.done.emit({'error': 'computation stopped'})
        except Exception as e:
            print('phase computation error :', e)
            self.done.emit({'error': str(e)})

    def compute(self, images, N, bin, lam, dx, dy, nIter, NA, nbZer):
        '''
        N, bin : crop size and binning, 0 = auto
        '''
        zs = np.array([i[0] for i in images])
        self.info.emit('caustic ...')
        spots = [spotImage(img) for z, img, com in images]  # full resolution
        caus = caustic(spots, zs, lam, dx, dy)
        self.causticDone.emit(caus)
        bin, N, warn = autoSampling(spots, zs, bin, N)
        self.info.emit('binning %d, crop %d ...' % (bin, N))
        crops = []
        for d, (z, img, com) in zip(spots, images):
            # binned pixel i covers [i b, i b + b[ : its center is i b + (b-1)/2
            comB = ((com[0] - (bin - 1) / 2) / bin, (com[1] - (bin - 1) / 2) / bin)
            crops.append(cropCentered(binImage(d, bin), comB, N))
        self.cropsDone.emit(dict(crops=crops, z=zs, bin=bin, N=N))
        dx, dy = dx * bin, dy * bin
        # amplitudes in fft order (spot center at pixel 0), same energy in each plane
        amps = [fft.ifftshift(np.sqrt(I / I.sum())) for I in crops]
        self.info.emit('retrieval (binning %d, crop %d) ...' % (bin, N))
        A, cModal, errors = retrieve(amps, zs, lam, dx, dy, caus['fc'], nbZer, nIter,
                                     stop=lambda: self.stop, progress=self.progress.emit)
        P = fft.fftshift(A)  # pupil = angular spectrum of the field at z = 0
        E0 = fft.fftshift(fft.ifft2(A))
        FX, FY = [fft.fftshift(f) for f in freqGrid(N, dx, dy)]
        NAauto = NA == 0
        fc = pupilRadius(P, FX, FY) if NAauto else NA / lam
        self.info.emit('Zernike fit ...')
        coeffs, mask, phaseFit, wrapped = zernikeFit(P, FX, FY, fc, nbZer)
        # displayed phases without piston, tilts and defocus (meaningless :
        # recentered images, defocus relative to the start position)
        rho, theta = np.hypot(FX, FY) / fc, np.arctan2(FY, FX)
        low = sum(coeffs[j - 1] * zernike(j, rho, theta) for j in range(1, 5))
        wrapped = np.where(mask, np.angle(P * np.exp(-1j * low)), np.nan)
        phaseFit = phaseFit - low
        return dict(E0=E0, P=P, FX=FX, FY=FY, fc=fc, NA=fc * lam, NAauto=NAauto, coeffs=coeffs,
                    mask=mask, phaseFit=phaseFit, wrapped=wrapped, errors=errors,
                    caustic=caus, lam=lam, dx=dx, dy=dy, bin=bin, N=N, warn=warn,
                    pupilPx=fc * N * np.sqrt(dx * dy))


if __name__ == '__main__':
    appli = QApplication(sys.argv)
    s = PHASE(IpAdress="10.0.1.31", NoMotor=10)
    s.show()
    appli.exec()
