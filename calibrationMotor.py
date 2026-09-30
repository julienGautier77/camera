# -*- coding: utf-8 -*-
"""
Calibration pixel/micron of the camera along X and Y using lateral motors.

For each axis five images are taken : start - 2*step, start - step, start,
start + step, start + 2*step (step in um). To avoid hysteresis the motor goes
first to start - 2.5*step so all points are reached in the same direction.
The spot center is
found on each image and a linear fit center(px) = f(position(um)) gives the
calibration pixel/um. The curve displacement(px) versus position(um) is plotted.
The result (um/pixel) is written in visu winPref (stepX, stepY).

@author: juliengautier
"""

from PyQt6 import QtCore
from PyQt6.QtWidgets import QApplication, QWidget
from PyQt6.QtWidgets import QVBoxLayout, QHBoxLayout, QGridLayout
from PyQt6.QtWidgets import QPushButton, QDoubleSpinBox, QSpinBox, QLineEdit
from PyQt6.QtWidgets import QCheckBox, QLabel, QComboBox
from PyQt6.QtGui import QIcon
import sys
import time
import threading
import pathlib
import os
import qdarkstyle
import numpy as np
import pyqtgraph as pg
from scipy import ndimage
from scipy.optimize import curve_fit
import zmq_client_RSAI

AXES = ('X', 'Y')
COLORS = {'X': 'r', 'Y': 'c'}
POINTS = (-2, -1, 0, 1, 2)  # positions in step unit (order of acquisition)
PRE_POINT = -2.5  # position reached before the first point (no image)


METHODS = ('Centroid', 'Gauss fit 2D', 'Gauss fit 1D (cuts)')


def gauss1D(x, a, x0, s, b):
    return a * np.exp(-(x - x0)**2 / (2 * s**2)) + b


def gauss2D(xy, a, x0, y0, sx, sy, b):
    x, y = xy
    return (a * np.exp(-(x - x0)**2 / (2 * sx**2) - (y - y0)**2 / (2 * sy**2)) + b).ravel()


def spotCenter(data, method=METHODS[0]):
    '''
    Return the center (axis 0 = X, axis 1 = Y) in pixel of the brightest spot.
    Centroid : background (median) removed, smoothed, thresholded at half max,
    centroid of the connected region containing the max.
    Gauss fit 2D : 2D gaussian fit on a window around the centroid.
    Gauss fit 1D (cuts) : 1D gaussian fits on the X and Y cuts through the centroid.
    '''
    raw = np.asarray(data, dtype=float)
    if raw.ndim == 3:  # color image
        raw = raw.sum(axis=2)
    raw = raw - np.median(raw)
    d = ndimage.gaussian_filter(raw, 2)
    dmax = d.max()
    if dmax <= 0:
        raise ValueError('no spot found')
    labels, _ = ndimage.label(d > 0.5 * dmax)
    idxMax = np.unravel_index(np.argmax(d), d.shape)
    region = labels == labels[idxMax]
    c0, c1 = ndimage.center_of_mass(np.where(region, d, 0))
    if method == METHODS[0]:
        return c0, c1

    # initial guess of sigma from the half max area (FWHM = 2.355 sigma)
    sig = max(2 * np.sqrt(region.sum() / np.pi) / 2.355, 1.)
    # fit window : +-4 sigma around the centroid
    h = int(max(4 * sig, 10))
    i0, i1 = int(round(c0)), int(round(c1))
    x0min, x0max = max(i0 - h, 0), min(i0 + h + 1, raw.shape[0])
    x1min, x1max = max(i1 - h, 0), min(i1 + h + 1, raw.shape[1])
    win = raw[x0min:x0max, x1min:x1max]
    amp = win.max()
    try:
        if method == METHODS[1]:
            x, y = np.meshgrid(np.arange(x0min, x0max), np.arange(x1min, x1max), indexing='ij')
            p, _ = curve_fit(gauss2D, (x, y), win.ravel(),
                             p0=(amp, c0, c1, sig, sig, 0), maxfev=5000)
            return p[1], p[2]
        # cuts through the centroid (mean of 3 lines to reduce noise)
        cut0 = raw[x0min:x0max, max(i1 - 1, 0):i1 + 2].mean(axis=1)
        cut1 = raw[max(i0 - 1, 0):i0 + 2, x1min:x1max].mean(axis=0)
        p0, _ = curve_fit(gauss1D, np.arange(x0min, x0max), cut0,
                          p0=(amp, c0, sig, 0), maxfev=5000)
        p1, _ = curve_fit(gauss1D, np.arange(x1min, x1max), cut1,
                          p0=(amp, c1, sig, 0), maxfev=5000)
        return p0[1], p1[1]
    except RuntimeError as e:
        raise ValueError('gaussian fit failed : %s' % e)


class CALIBRATION(QWidget):
    '''
    Calibration widget
    CAM : CAMERA widget (camera.py) used to take the images
    IpAdress, NoMotor : default motor
    '''
    acqMain = QtCore.pyqtSignal()  # ask one image to the camera

    def __init__(self, CAM=None, IpAdress='', NoMotor=1, parent=None):

        super(CALIBRATION, self).__init__()
        self.isWinOpen = False
        self.parent = parent
        self.CAM = CAM
        self.MOTs = {}  # (ip, noMotor) : MOTORRSAI
        self.setStyleSheet(qdarkstyle.load_stylesheet(qt_api='pyqt6'))
        p = pathlib.Path(__file__)
        sepa = os.sep
        self.icon = str(p.parent) + sepa + 'icons' + sepa
        self.setWindowIcon(QIcon(self.icon + 'LOA.png'))
        self.setWindowTitle('Calibration pixel/um')
        self.imageEvent = threading.Event()
        self.lastImage = None
        self.setup(IpAdress, NoMotor)
        self.actionButton()
        self.threadCalib = ThreadCalib(self)
        self.threadCalib.acqCalib.connect(self.acquireOneImage)
        self.threadCalib.info.connect(self.infoLabel.setText)
        self.threadCalib.finished.connect(self.calibDone)

    def confValue(self, key, default):
        # last motors used are saved in the camera ini file
        try:
            v = self.CAM.conf.value(self.CAM.nbcam + '/' + key)
            return default if v is None else v
        except Exception:
            return default

    def setup(self, IpAdress, NoMotor):
        vbox = QVBoxLayout()
        grid = QGridLayout()
        grid.addWidget(QLabel('Rack IP'), 0, 1)
        grid.addWidget(QLabel('Motor n°'), 0, 2)
        grid.addWidget(QLabel('Step'), 0, 3)
        self.axisCheck = {}
        self.ipBox = {}
        self.noMotorBox = {}
        self.stepBox = {}
        for i, ax in enumerate(AXES):
            self.axisCheck[ax] = QCheckBox(ax)
            self.axisCheck[ax].setChecked(True)
            grid.addWidget(self.axisCheck[ax], i + 1, 0)
            self.ipBox[ax] = QLineEdit(str(self.confValue('calibIp' + ax, IpAdress)))
            grid.addWidget(self.ipBox[ax], i + 1, 1)
            self.noMotorBox[ax] = QSpinBox()
            self.noMotorBox[ax].setRange(1, 100)
            self.noMotorBox[ax].setValue(int(self.confValue('calibMot' + ax, NoMotor)))
            grid.addWidget(self.noMotorBox[ax], i + 1, 2)
            self.stepBox[ax] = QDoubleSpinBox()
            self.stepBox[ax].setDecimals(1)
            self.stepBox[ax].setRange(0.1, 100000)
            self.stepBox[ax].setValue(float(self.confValue('calibStep' + ax, 100)))
            self.stepBox[ax].setSuffix(' um')
            grid.addWidget(self.stepBox[ax], i + 1, 3)

        grid.addWidget(QLabel('Wait after move'), 3, 0)
        self.waitBox = QDoubleSpinBox()
        self.waitBox.setRange(0, 10)
        self.waitBox.setValue(0.5)
        self.waitBox.setSuffix(' s')
        grid.addWidget(self.waitBox, 3, 1)
        self.squareCheck = QCheckBox('Square pixel (one axis -> X and Y)')
        self.squareCheck.setChecked(True)
        grid.addWidget(self.squareCheck, 3, 2, 1, 2)
        grid.addWidget(QLabel('Spot center'), 4, 0)
        self.methodBox = QComboBox()
        self.methodBox.addItems(METHODS)
        self.methodBox.setCurrentText(str(self.confValue('calibMethod', METHODS[0])))
        grid.addWidget(self.methodBox, 4, 1)
        vbox.addLayout(grid)

        hbox = QHBoxLayout()
        self.playButton = QPushButton('Play')
        self.stopButton = QPushButton('STOP')
        self.stopButton.setStyleSheet("background-color: red")
        self.stopButton.setEnabled(False)
        hbox.addWidget(self.playButton)
        hbox.addWidget(self.stopButton)
        vbox.addLayout(hbox)

        self.infoLabel = QLabel('')
        vbox.addWidget(self.infoLabel)
        self.resultLabel = QLabel('')
        self.resultLabel.setStyleSheet('font: bold 11pt')
        vbox.addWidget(self.resultLabel)
        self.plot = pg.PlotWidget()
        self.plot.setLabel('bottom', 'motor position', units='um')
        self.plot.setLabel('left', 'spot displacement (px)')
        self.plot.showGrid(x=True, y=True)
        self.plot.addLegend()
        self.plot.setMinimumHeight(250)
        vbox.addWidget(self.plot)
        self.setLayout(vbox)

    def plotAxis(self, ax, pos, disp, slope, intercept):
        '''
        points : spot displacement along the axis versus motor position
        line : linear fit
        '''
        self.plot.plot(pos, disp, pen=None, symbol='o', symbolBrush=COLORS[ax], name=ax)
        if slope is not None:
            xf = np.array([pos.min(), pos.max()])
            self.plot.plot(xf, slope * xf + intercept, pen=pg.mkPen(COLORS[ax], width=2))

    def actionButton(self):
        self.playButton.clicked.connect(self.startCalib)
        self.stopButton.clicked.connect(self.stopCalib)
        if self.CAM is not None:
            self.CAM.signalData.connect(self.imageReceived)

    def winPref(self):
        try:
            return self.CAM.visualisation.winPref
        except Exception:
            return None

    def acquireOneImage(self):
        self.acqMain.emit()

    def imageReceived(self, data):
        if self.threadCalib.isRunning():
            # same rotation as visu display so that X and Y match the screen
            pref = self.winPref()
            rot = pref.rotateValue if pref is not None else 0
            self.lastImage = np.rot90(np.array(data, copy=True), rot)
            self.imageEvent.set()

    def getMotor(self, ax):
        ip = self.ipBox[ax].text().strip()
        no = self.noMotorBox[ax].value()
        if (ip, no) not in self.MOTs:
            self.MOTs[(ip, no)] = zmq_client_RSAI.MOTORRSAI(ip, no)
        return self.MOTs[(ip, no)]

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

    def startCalib(self):
        self.stopCamera()
        self.resultLabel.setText('')
        tasks = []
        self.infoLabel.setText('connecting motor ...')
        QApplication.processEvents()
        for ax in AXES:
            if self.axisCheck[ax].isChecked():
                tasks.append((ax, self.getMotor(ax), self.stepBox[ax].value()))
                if self.CAM is not None:
                    self.CAM.conf.setValue(self.CAM.nbcam + '/calibIp' + ax, self.ipBox[ax].text().strip())
                    self.CAM.conf.setValue(self.CAM.nbcam + '/calibMot' + ax, self.noMotorBox[ax].value())
                    self.CAM.conf.setValue(self.CAM.nbcam + '/calibStep' + ax, self.stepBox[ax].value())
        if not tasks:
            self.infoLabel.setText('select X and/or Y')
            return
        self.threadCalib.tasks = tasks
        self.threadCalib.method = self.methodBox.currentText()
        if self.CAM is not None:
            self.CAM.conf.setValue(self.CAM.nbcam + '/calibMethod', self.threadCalib.method)
        self.setEnabledInputs(False)
        self.threadCalib.start()

    def stopCalib(self):
        self.threadCalib.stopThread()
        for MOT in self.MOTs.values():
            MOT.stopMotor()

    def setEnabledInputs(self, state):
        widgets = [self.waitBox, self.squareCheck, self.methodBox, self.playButton]
        for ax in AXES:
            widgets += [self.axisCheck[ax], self.ipBox[ax], self.noMotorBox[ax], self.stepBox[ax]]
        for w in widgets:
            w.setEnabled(state)
        self.stopButton.setEnabled(not state)

    def calibDone(self):
        self.setEnabledInputs(True)
        txt = 'spot center : %s\n' % self.threadCalib.method
        newStep = {}
        self.plot.clear()
        for ax, res in self.threadCalib.results.items():
            txt += 'Motor %s :\n' % ax
            res = sorted(res)  # by position
            for r in res:
                txt += '   pos %+.1f um (motor %d step) : center X=%.2f Y=%.2f px\n' % (r[0], r[3], r[1], r[2])
            i = AXES.index(ax)
            pos = np.array([r[0] for r in res])  # um relative to start
            centers = np.array([[r[1], r[2]] for r in res])
            if len(res) == 0:
                txt += '   no image\n'
                continue
            iStart = int(np.argmin(abs(pos)))
            disp = centers[:, i] - centers[iStart, i]  # displacement along the axis
            if ax in self.threadCalib.errors or len(res) != len(POINTS):
                self.plotAxis(ax, pos, disp, None, None)
                txt += '   error : %s\n' % self.threadCalib.errors.get(ax, 'stopped')
                continue
            fits = [np.polyfit(pos, centers[:, k], 1) for k in range(2)]
            slopes = [f[0] for f in fits]
            pxPerUm = abs(slopes[i])
            self.plotAxis(ax, pos, disp, slopes[i], fits[i][1] - centers[iStart, i])
            if pxPerUm == 0 or abs(slopes[1 - i]) > pxPerUm:
                txt += '   spot does not move along %s : no calibration\n' % ax
                continue
            rms = np.std(centers[:, i] - np.polyval(fits[i], pos))
            newStep[ax] = 1 / pxPerUm
            txt += '   %.4f pixel/um   %.4f um/pixel   (angle %.1f°, fit rms %.2f px)\n' % (
                pxPerUm, 1 / pxPerUm, np.degrees(np.arctan2(slopes[1 - i], slopes[i])), rms)
        requested = [t[0] for t in self.threadCalib.tasks]
        if len(requested) == 1 and len(newStep) == 1 and self.squareCheck.isChecked():
            # only one axis asked : same value for the other axis
            (ax, v), = newStep.items()
            other = AXES[1 - AXES.index(ax)]
            newStep[other] = v
            txt += '   square pixel : %s = %s\n' % (other, ax)
        if newStep:
            txt += self.updateVisu(newStep)
            if self.threadCalib.error:
                self.infoLabel.setText('calibration done with error : see below')
            else:
                self.infoLabel.setText('calibration done')
        elif not self.threadCalib.error:
            self.infoLabel.setText('calibration stopped')
        self.resultLabel.setText(txt)

    def updateVisu(self, newStep):
        '''
        write um/pixel in visu preferences (stepX, stepY) : saved in the ini
        file by winPref and axis scale refreshed
        '''
        pref = self.winPref()
        if pref is None:
            return 'visu preferences not found : not updated'
        txt = 'visu updated :'
        if 'X' in newStep:
            txt += '  stepX %.4f -> %.4f' % (pref.stepX, newStep['X'])
            pref.stepXBox.setValue(newStep['X'])
        if 'Y' in newStep:
            txt += '  stepY %.4f -> %.4f' % (pref.stepY, newStep['Y'])
            pref.stepYBox.setValue(newStep['Y'])
        pref.conf.sync()
        try:
            self.CAM.visualisation.ScaleImg()
        except Exception as e:
            print('visu scale refresh', e)
        return txt

    def closeEvent(self, event):
        self.stopCalib()
        self.threadCalib.wait(2000)
        self.isWinOpen = False
        time.sleep(0.1)
        event.accept()


class ThreadCalib(QtCore.QThread):
    '''
    For each axis : move to start, start - step, start + step, take one
    image at each position, compute the spot center and go back to start
    '''
    acqCalib = QtCore.pyqtSignal()
    info = QtCore.pyqtSignal(str)

    def __init__(self, parent=None):
        super(ThreadCalib, self).__init__(parent)
        self.parent = parent
        self.stop = False
        self.error = False
        self.tasks = []  # (axis, MOT, step um)
        self.method = METHODS[0]  # spot center method
        self.results = {}  # axis : [(um, cX, cY, motor position), ...]
        self.errors = {}

    def moveAndWait(self, MOT, pos, tol=10, timeout=60):
        MOT.move(pos)
        t0 = time.time()
        while not self.stop:
            b = MOT.position()
            if abs(b - pos) <= tol:
                return True
            if time.time() - t0 > timeout:
                raise TimeoutError('motor did not reach %d (pos %s)' % (pos, b))
            time.sleep(0.1)
        return False

    def takeImage(self, timeout=30):
        # clear before asking the image, in this thread, so that an old image
        # already received can not be taken for the new one
        self.parent.imageEvent.clear()
        self.acqCalib.emit()
        t0 = time.time()
        while not self.stop:
            if self.parent.imageEvent.wait(0.1):
                return self.parent.lastImage
            if time.time() - t0 > timeout:
                raise TimeoutError('no image received from camera')
        return None

    def calibAxis(self, ax, MOT, stepUm, wait):
        res = []
        self.results[ax] = res
        stepPerUm = MOT.getStepValue()  # motor calibration step/um
        p0 = int(MOT.position())
        try:
            # hysteresis : go below the first point, then all points are
            # reached in the same direction (increasing position)
            pre = int(round(p0 + PRE_POINT * stepUm * stepPerUm))
            self.info.emit('%s : pre-position %+.1f um (%d step) ...' % (ax, PRE_POINT * stepUm, pre))
            if not self.moveAndWait(MOT, pre):
                return
            for um in np.array(POINTS) * stepUm:
                if self.stop:
                    break
                pos = int(round(p0 + um * stepPerUm))
                self.info.emit('%s : moving to %+.1f um (%d step) ...' % (ax, um, pos))
                if not self.moveAndWait(MOT, pos):
                    break
                time.sleep(wait)
                self.info.emit('%s : acquisition at %+.1f um ...' % (ax, um))
                data = self.takeImage()
                if data is None:
                    break
                c0, c1 = spotCenter(data, self.method)
                res.append((um, c0, c1, MOT.position()))
        finally:
            self.info.emit('%s : back to start position %d' % (ax, p0))
            MOT.move(p0)
            if not self.stop:
                self.moveAndWait(MOT, p0)

    def run(self):
        self.stop = False
        self.error = False
        self.results = {}
        self.errors = {}  # axis : error message
        wait = self.parent.waitBox.value()
        for ax, MOT, stepUm in self.tasks:
            if self.stop:
                break
            # an error on one axis does not prevent the other axis calibration
            try:
                self.calibAxis(ax, MOT, stepUm, wait)
            except Exception as e:
                self.error = True
                self.errors[ax] = str(e)
                print('calibration %s error :' % ax, e)
                self.info.emit('%s error : %s' % (ax, e))

    def stopThread(self):
        self.stop = True


if __name__ == '__main__':
    appli = QApplication(sys.argv)
    s = CALIBRATION(IpAdress="10.0.1.31", NoMotor=1)
    s.show()
    appli.exec()
