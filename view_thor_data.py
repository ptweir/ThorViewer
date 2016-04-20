#based in part on https://github.com/goldsborough/Writer-Tutorial
# and DataSlicing.py example in pyqtgraph

#########notes:
# TODO: I think index is off because frame data is zero-based, but frame counter is 1-based!
# TODO: updateROI sync in both windows
# 2016/03/28 now prompts to move (and rename) files from ThorSync

import sys
from PyQt4 import QtGui, QtCore
from PyQt4.QtCore import Qt

import numpy as np
#from pyqtgraph.Qt import QtCore, QtGui
import pyqtgraph as pg
import h5py, os, shutil
import parse_thor_xml
import pandas as pd

from libtiff import TIFF

class Main(QtGui.QMainWindow):

    def __init__(self, parent = None):
        QtGui.QMainWindow.__init__(self,parent)

        self.inDirName = ""

        self.initUI()

    def initToolbar(self):

        self.newAction = QtGui.QAction(QtGui.QIcon("icons/new.png"),"New viewer",self)
        self.newAction.setShortcut("Ctrl+N")
        self.newAction.setStatusTip("Create a viewer winder.")
        self.newAction.triggered.connect(self.new)

        self.openAction = QtGui.QAction(QtGui.QIcon("icons/open.png"),"Open file",self)
        self.openAction.setStatusTip("Open data set")
        self.openAction.setShortcut("Ctrl+O")
        self.openAction.triggered.connect(self.open)

        self.toolbar = self.addToolBar("Options")

        self.toolbar.addAction(self.newAction)
        self.toolbar.addAction(self.openAction)


    def initMenubar(self):
    
        menubar = self.menuBar()

        file = menubar.addMenu("File")

        file.addAction(self.newAction)
        file.addAction(self.openAction)
        
    def initUI(self):

        #self.text = QtGui.QTextEdit(self)

        self.initToolbar()
        self.initMenubar()
        
        cw = QtGui.QWidget()
        self.setCentralWidget(cw)
        self.layout = QtGui.QGridLayout()
        cw.setLayout(self.layout)
        self.imv1 = pg.ImageView()
        self.imv2 = pg.ImageView()
        self.layout.addWidget(self.imv1, 0, 0, 1, 10)
        self.layout.addWidget(self.imv2, 1, 0, 1, 10)

        self.p1 = pg.PlotWidget()
        self.p1.setMaximumHeight(150)
        self.layout.addWidget(self.p1, 2, 0, 1, 10)

        # Initialize a statusbar for the window
        self.statusbar = self.statusBar()

        # x and y coordinates on the screen, width, height
        self.setGeometry(100,100,800,900)

        self.setWindowTitle("Viewer")

        self.setWindowIcon(QtGui.QIcon("icons/image.png"))

    def new(self):

        spawn = Main(self)
        spawn.show()
        
    def update(self, ch=None):
        if ch is None or ch==1:
            currentSliderTime = self.imv1.currentIndex
        elif ch==2:
            currentSliderTime = self.imv2.currentIndex
        elif ch==3:
            currentSliderTime = self.timeLine.value()
            
        self.imv1.setCurrentIndex(currentSliderTime)
        self.imv2.setCurrentIndex(currentSliderTime)
        self.timeLine.setX(currentSliderTime)

    def updateROI(self):
        self.imv2.roi.setState(self.imv1.roi.getState())
        
    def checkUpdate(self):
        for keyInd in range(len(self.lines)):
            if self.checks[keyInd].isChecked():
                self.lines[keyInd].setPen(keyInd, len(self.lines))
            else:
                self.lines[keyInd].setPen(None)
        """
        if self.check0.isChecked():
            self.lines[0].setPen(0, len(self.lines))
        else:
            self.lines[0].setPen(None)
        if self.check1.isChecked():
            self.lines[1].setPen(1, len(self.lines))
        else:
            self.lines[1].setPen(None)
        """
    def convert_tifs(self):
        fileNames = os.listdir(self.inDirName)
        fileNames.sort()

        chanAFileNames = [os.path.join(self.inDirName, f) for f in fileNames if f[:5]=='ChanA' and f[-4:]=='.tif' and f.find('Preview')==-1]
        chanBFileNames = [os.path.join(self.inDirName, f) for f in fileNames if f[:5]=='ChanB' and f[-4:]=='.tif' and f.find('Preview')==-1]

        tifA = TIFF.open(chanAFileNames[0], mode='r')
        imageA = tifA.read_image()
        tifA.close()

        imageStack = np.zeros((imageA.shape[0], imageA.shape[1], len(chanAFileNames), 2), dtype='uint16')

        for frameInd, fileNameA in enumerate(chanAFileNames):
            tifA = TIFF.open(fileNameA, mode='r')
            imageA = tifA.read_image()
            tifA.close()
            if len(chanBFileNames) > 0:
                fileNameB = chanBFileNames[frameInd]            
                tifB = TIFF.open(fileNameB, mode='r')
                imageB = tifB.read_image()
                tifB.close()
            
            imageStack[:, :, frameInd, 0] = imageA
            if len(chanBFileNames) > 0:
                imageStack[:, :, frameInd, 1] = imageB
            
        imageStack = np.flipud(imageStack)

        outFileName = 't_series.hdf5'
        outFilePath = os.path.join(self.inDirName, outFileName)
        
        f = h5py.File(outFilePath, 'w')
        f.create_dataset('frames', data=imageStack, compression='gzip')
        f.flush()
        f.close()
        
        return outFileName
        
    def copy_thorsync_files(self):
        
        thorsyncDirName = str(QtGui.QFileDialog.getExistingDirectory(self, "Select ThorSync Directory containing data for images in "+self.inDirName.rsplit(os.sep, 1)[1], self.inDirName.rsplit(os.sep, 1)[0]))
        if thorsyncDirName[-3:] != self.inDirName[-3:]:
            QtGui.QMessageBox.warning(self, 'Warning', 'ThorSync directory suffix ('+thorsyncDirName[-3:]+') does not match suffix of images directory ('+self.inDirName[-3:]+')', 'copy anyway')
        inFiles = os.listdir(thorsyncDirName)
        inH5Files = [inFile for inFile in inFiles if inFile[-3:]=='.h5']
        inXmlFiles = [inFile for inFile in inFiles if inFile[-12:]=='Settings.xml']
        
        outH5Files, outXmlFiles = [], []
        
        for inH5File in inH5Files:
            outH5File = thorsyncDirName.rsplit(os.sep, 1)[1]+'_'+inH5File
            shutil.copyfile(os.path.join(thorsyncDirName, inH5File), os.path.join(self.inDirName, outH5File))
            outH5Files.append(outH5File)
        for inXmlFile in inXmlFiles:   
            outXmlFile = thorsyncDirName.rsplit(os.sep, 1)[1]+'_'+inXmlFile
            shutil.copyfile(os.path.join(thorsyncDirName, inXmlFile), os.path.join(self.inDirName, outXmlFile))
            outXmlFiles.append(outXmlFile)
        return outH5Files, outXmlFiles
        
    def open(self):

        self.inDirName = str(QtGui.QFileDialog.getExistingDirectory(self, "Select Directory", "D:\\peter"))
        if self.inDirName:
            self.setWindowTitle("Viewing "+self.inDirName)
            inFiles = os.listdir(self.inDirName)

            inHdf5Files = [inFile for inFile in inFiles if inFile[-5:]=='.hdf5']
            while len(inHdf5Files) < 1:
                reply = QtGui.QMessageBox.question(self, 'No imaging file', "Unable to find converted imaging file, convert tifs?", QtGui.QMessageBox.Yes | QtGui.QMessageBox.No, QtGui.QMessageBox.Yes)
                doConversion = (reply == QtGui.QMessageBox.Yes)
                if doConversion:
                    inHdf5Files = [self.convert_tifs()]
                else:
                    return
                
            inFileName = os.path.join(self.inDirName,inHdf5Files[0])
            f = h5py.File(inFileName, 'r')

            allFrames = np.copy(f['frames']) # this takes a long time (reading all data into memory)

            inH5Files = [inFile for inFile in inFiles if inFile[-3:]=='.h5']
            inXmlFiles = [inFile for inFile in inFiles if inFile[-12:]=='Settings.xml']
            while (len(inH5Files) < 1) or (len(inXmlFiles) < 1):
                cpReply = QtGui.QMessageBox.question(self, 'No ThorSync files', "Unable to find ThorSync files, copy them?", QtGui.QMessageBox.Yes | QtGui.QMessageBox.No, QtGui.QMessageBox.Yes)
                doCopy = (cpReply == QtGui.QMessageBox.Yes)
                if doCopy:
                    inH5Files, inXmlFiles = self.copy_thorsync_files()
                else:
                    return
                
            
            sampleRateHz = parse_thor_xml.get_sample_rate(os.path.join(self.inDirName,inXmlFiles[0]))

            inFile = h5py.File(os.path.join(self.inDirName,inH5Files[0]), 'r')

            frameCntr = inFile['CI']['Frame Counter'][:].squeeze()
            timeSec = np.arange(len(frameCntr))/sampleRateHz

            AIDict = {}
            for key in inFile['AI'].keys():
                AIDict[key] = inFile['AI'][key][:].squeeze()
                
            AIDataFrame = pd.DataFrame(data=AIDict, index=frameCntr)
            AIMeanFrames = AIDataFrame.groupby(AIDataFrame.index).mean()

            data = np.rollaxis(allFrames, 2, 0)
            data = np.rollaxis(data, 2, 1)
            data = np.concatenate((data[:,:,:,::-1], np.zeros_like(data[:,:,:,:1])), axis=3)

            self.p1.clear()
            self.imv1.clear()
            self.imv2.clear()
            self.lines = [[] for i in range(len(AIMeanFrames.keys()))]
            self.checks = [[] for i in range(len(AIMeanFrames.keys()))]
            self.aiLabels = [[] for i in range(len(AIMeanFrames.keys()))]
            for keyInd, key in enumerate(AIMeanFrames.keys()):
                self.lines[keyInd] = self.p1.plot(AIMeanFrames.index, AIMeanFrames[key].values, pen=(keyInd, len(AIMeanFrames.keys())))
                self.checks[keyInd] = QtGui.QCheckBox(key)
                self.checks[keyInd].setChecked(True)
                self.aiLabels = key
                self.layout.addWidget(self.checks[keyInd], 3, keyInd, 1, 1)
                self.checks[keyInd].stateChanged.connect(self.checkUpdate)


            self.timeLine = pg.InfiniteLine(0, movable=True)
            self.timeLine.setX(0)
            self.p1.addItem(self.timeLine)
            
            self.imv1.sigTimeChanged.connect(lambda: self.update(1))
            self.imv2.sigTimeChanged.connect(lambda: self.update(2))
            self.timeLine.sigPositionChanged.connect(lambda: self.update(3))

            self.imv1.roi.sigRegionChanged.connect(self.updateROI)

            self.imv1.setImage(data[:,:,:,:])
            self.imv2.setImage(data[:,:,:,1]) #peter
            self.imv1.ui.roiPlot.setXLink(self.p1)
            self.imv2.ui.roiPlot.setXLink(self.p1)
            
            self.update()
            inFile.close()

def main():

    app = QtGui.QApplication(sys.argv)

    main = Main()
    main.show()

    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
