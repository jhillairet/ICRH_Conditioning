import sys
import os
import numpy as np

# Qt5/Qt4 compatibility
try:
    import PyQt5.QtCore as QtCore
    import PyQt5.QtGui as QtGui
    import PyQt5.QtWidgets as QtWidgets
    from PyQt5.QtWidgets import (QMainWindow, QApplication, QWidget, QPushButton, 
                                 QHBoxLayout, QVBoxLayout, QTableWidget, QTableWidgetItem)
    from matplotlib.backends.backend_qt5agg import (
            FigureCanvasQTAgg as FigureCanvas,
            NavigationToolbar2QT as NavigationToolbar)

except ImportError:    
    import PyQt4.QtCore as QtCore
    import PyQt4.QtGui as QtGui
    import PyQt4.QtGui as QtWidgets
    from PyQt4.QtGui import (QMainWindow, QApplication, QWidget, QPushButton, 
                                 QHBoxLayout, QVBoxLayout, QTableWidget, QTableWidgetItem)
    from matplotlib.backends.backend_qt4agg import (
            FigureCanvasQTAgg as FigureCanvas,
            NavigationToolbar2QT as NavigationToolbar)

import pyqtgraph as pg

import ICRH_Conditioning as condi
import ICRH_FileIO as io

# switch default plotting scheme to white
pg.setConfigOption('background', 'w')
pg.setConfigOption('foreground', 'k')

class AppForm(QMainWindow):
    def __init__(self, parent=None):
        QMainWindow.__init__(self, parent)        
        self.create_main_frame()
        self.setGeometry(0, 0, 1600, 600)
        self.setWindowTitle("WEST ICRH Conditoning Data Analysis")
        # sync remote files to local
        self.sync_files()
        # fill the shot table with the date of the last shots
        self.update_shot_table()
        # default plotted data are from last shot file
        self.data = self.get_conditioning_data(0)
        self.update_metadata_table()
        self.update_plot()

    def create_main_frame(self):
        self.main_frame = QWidget()
        # pyqtgraph Figures
        self.l = pg.GraphicsLayoutWidget(border=(100, 100, 100))
        self.PG = self.l.addPlot(row=0, col=0, title='Pi,Pr Gauche')
        self.PD = self.l.addPlot(row=0, col=1, title='Pi,Pr Droite')
        self.PhG = self.l.addPlot(row=1, col=0, title='Phase V1-V3 Gauche')
        self.PhD = self.l.addPlot(row=1, col=1, title='Phase V2-V4 Droite')
        self.VG = self.l.addPlot(row=2, col=0, title='Tensions V1,V2 Gauche')
        self.VD = self.l.addPlot(row=2, col=1, title='Tensions V3,V4 Droite')
        self.pTransG = self.l.addPlot(row=3, col=0, title='Pression Gauche')
        self.pTransD = self.l.addPlot(row=3, col=1, title='Pression Droit')
        # Connect Y axis on left and right subplots
        self.PhG.setXLink(self.PG)
        self.VG.setXLink(self.PG)
        self.pTransG.setXLink(self.PG)
        
        self.PhD.setXLink(self.PD)
        self.VD.setXLink(self.PD)
        self.pTransD.setXLink(self.PD)
        
#        # add legends
#        self.PG.addLegend()
#        self.PD.addLegend()
#        self.VG.addLegend()
#        self.VD.addLegend()
                    
        # Default Fonts
        button_default_font = QtGui.QFont('SansSerif', 16)
        item_default_font = QtGui.QFont('SansSerif', 12)
        # Update Button
        self.refresh_button = QPushButton('Refresh', parent=self.main_frame)
        self.refresh_button.setFont(button_default_font)
        self.refresh_button.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_BrowserReload))
        self.refresh_button.clicked.connect(self.refresh)
        # Conditioning Shots Table
        self.shot_table = QTableWidget(10, 1, parent=self.main_frame)
        self.shot_table.setFont(item_default_font)
        self.shot_table.setHorizontalHeaderLabels(('Conditioning Shot#',))
        self.shot_table.cellClicked.connect(self.on_shot_table_clicked)
        self.shot_table.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.shot_table.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.shot_table.horizontalHeader().setStretchLastSection(True)
        # Conditioning Metadata Table
        self.metadata_table = QTableWidget(10, 2, parent=self.main_frame)
        self.metadata_table.setFont(item_default_font)
        self.metadata_table.setHorizontalHeaderLabels(('Parameter', 'Value'))
        self.metadata_table.horizontalHeader().setStretchLastSection(True)

        # Layout construction
        vbox_shots = QVBoxLayout()
        vbox_shots.addWidget(self.refresh_button)
        vbox_shots.addWidget(self.shot_table)

        vbox_metadata = QVBoxLayout()
        vbox_metadata.addWidget(self.metadata_table)

        vbox_canvas = QVBoxLayout()
        vbox_canvas.addWidget(self.l)

        hbox = QHBoxLayout()
        hbox.addLayout(vbox_shots)
        hbox.addLayout(vbox_metadata)
        hbox.addLayout(vbox_canvas, 2) # canvas is twice bigger than all others

        self.main_frame.setLayout(hbox)
        self.setCentralWidget(self.main_frame)

    def get_local_file_list(self):
        return io.list_local_files(local_data_path='data/Cond_Data/')

    def get_remote_file_list(self):
        return io.list_remote_files()

    def sync_files(self):
        self.remote_files = self.get_remote_file_list()
        io.copy_remote_files_to_local(self.remote_files,
                                      local_data_path='data/Cond_Data/')
        self.local_files = self.get_local_file_list()

    def update_shot_table(self):
        # reduce the number of rows to the current number of local files
        self.shot_table.setRowCount(len(self.local_files))

        for row, filename in enumerate(self.local_files):
            self.shot_table.setItem(row, 0, QTableWidgetItem(filename))

    def update_metadata_table(self, idx=-1):
        self.metadata = condi.read_conditioning_metadata(
            os.path.join('data', 'Cond_Data', self.local_files[idx]))
        # reduce the number of rows to the actual metadata number
        self.metadata_table.setRowCount(len(self.metadata))

        for row, key in enumerate(self.metadata):
            self.metadata_table.setItem(row, 0, QTableWidgetItem(key))
            self.metadata_table.setItem(row, 1, QTableWidgetItem(self.metadata[key]))
        #self.metadata_table.horizontalHeader().setSectionResizeMode(0,QtWidgets.QHeaderView.Stretch)

    def refresh(self):
        self.sync_files()
        # select the first row (most recent) and display its associated data
        self.shot_table.selectRow(0)
        self.update_shot_table()
        self.data = self.get_conditioning_data(0)
        self.update_metadata_table(0)
        self.update_plot()

    def on_shot_table_clicked(self, row, col):
        self.data = self.get_conditioning_data(row)
        self.metadata = self.update_metadata_table(row)
        self.update_plot()

    def get_conditioning_data(self, idx=-1):
        print(self.local_files[idx])
        self.data = condi.read_conditoning_data(
                os.path.join('data', 'Cond_Data', self.local_files[idx]))
        return self.data

    def update_plot(self):
        data = self.data
        if data.empty:
            print('Empty data!')
        else:
            # NB: pandas -> np arrays for pyqtgraph compatibility
            time = data.index.values/1e3  # display time in ms
            
            # Pi,Pr Gauche
            self.PG.plot(pen=pg.mkPen('k', width=2, style=QtCore.Qt.DashLine),
                         clear=True, name='Consigne',
                         x=time, y=data.Consigne_mes.values/2) # kW
            self.PG.plot(pen=pg.mkPen('b', width=2), clear=False, name='Pi_G',
                         x=time, y=data.PiG.values/10) # kW
            self.PG.plot(pen=pg.mkPen('r', width=2), clear=False, name='Pr_G',
                         x=time, y=data.PrG.values/10) # kW
            self.PG.setLabel('left', 'Power', units='kW')
            
            # Pi,Pr Droite
            self.PD.plot(pen=pg.mkPen('k', width=2, style=QtCore.Qt.DashLine),
                         clear=True, name='Consigne',
                         x=time, y=data.Consigne_mes.values/2) # k
            self.PD.plot(pen=pg.mkPen('b', width=2), 
                         clear=False, name='Pi_D',
                         x=time, y=data.PiD.values/10) # kW
            self.PD.plot(pen=pg.mkPen('r', width=2), 
                         clear=False, name='Pr_D',
                         x=time, y=data.PrD.values/10) # kW
            self.PD.setLabel('left', 'Power', units='kW')
            
            # Phase Gauche
            self.PhG.plot(pen='b', clear=True, 
                          x=time, y=data['Ph(V1-V3)'].values/100) # degres
            self.PhG.setLabel('left', 'Phase [left]', units='deg')
            
            # Phase Droite
            self.PhD.plot(pen='b', clear=True, 
                          x=time, y=data['Ph(V2-V4)'].values/100) # degres
            self.PhD.setLabel('left', 'Phase [right]', units='deg')
            
            # Tensions Gauche
            self.VG.plot(pen=pg.mkPen('b', width=2), 
                         clear=True, name='V1',
                         x=time, y=data.V1.values/1000) # kV
            self.VG.plot(pen=pg.mkPen('r', width=2), 
                         clear=False, name='V2',
                         x=time, y=data.V2.values/1000) # kV
            self.VG.setLabel('left','Probe Voltage', units='V')
            
            # Tensions Droite
            self.VD.plot(pen=pg.mkPen('b', width=2), 
                         clear=True, name='V3', 
                         x=time, y=data.V3.values/1000) # kV
            self.VD.plot(pen=pg.mkPen('r', width=2), 
                         clear=False, name='V4',
                         x=time, y=data.V4.values/1000) # kV
            self.VD.setLabel('left','Probe Voltage', units='V')
            
            # Pression dans le transfo gauche et droit
            self.pTransG.plot(pen='b', x=time, y=np.power(10, 1.667*data.Vide_gauche.values*1e-3-9.33), clear=True)
            self.pTransG.setLogMode(y=True)
            self.pTransG.showGrid(y=True)
            self.pTransG.setLabel('bottom','time', units='ms')
            self.pTransG.setLabel('left', 'Pressure [left]', units='Pa')
            self.pTransD.plot(pen='b', x=time, y=np.power(10, 1.667*data.Vide_droit.values*1e-3-9.33), clear=True)
            self.pTransD.setLogMode(y=True)
            self.pTransD.showGrid(y=True)
            self.pTransD.setLabel('bottom','time', units='ms')
            self.pTransD.setLabel('left', 'Pressure [right]', units='Pa')

def main():
    # Hack to be able to run the code from spyder
    # taken from http://stackoverflow.com/questions/19459299/running-a-pyqt-application-twice-from-one-prompt-in-spyder
    if QtCore.QCoreApplication.instance() is not None:
        app = QtCore.QCoreApplication.instance()
    else:
        app = QApplication(sys.argv)
    form = AppForm()
    form.show()
    app.exec_()

if __name__ == "__main__":
    main()
