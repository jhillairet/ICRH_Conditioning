import sys

# Qt5/Qt4 compatibility
try: 
    import PyQt5.QtCore as QtCore
    import PyQt5.QtGui as QtGui 
    import PyQt5.QtWidgets as QtWidgets
    from PyQt5.QtWidgets import (QMainWindow, QApplication, QWidget, QPushButton, QListWidget,
                                 QHBoxLayout, QVBoxLayout, QStatusBar, QMessageBox)
    from matplotlib.backends.backend_qt5agg import (
            FigureCanvasQTAgg as FigureCanvas,
            NavigationToolbar2QT as NavigationToolbar)
except ImportError:    
    import PyQt4.QtCore as QtCore
    import PyQt4.QtGui as QtGui
    import PyQt4.QtGui as QtWidgets
    from PyQt4.QtGui import (QMainWindow, QApplication, QWidget, QPushButton, QListWidget,
                                 QHBoxLayout, QVBoxLayout, QStatusBar, QMessageBox)
    from matplotlib.backends.backend_qt4agg import (
            FigureCanvasQTAgg as FigureCanvas,
            NavigationToolbar2QT as NavigationToolbar)

import pyqtgraph as pg

import ICRH_FastData as fast
import ICRH_FileIO as io

import numpy as np

# Remote (on dfci) and local (linux) absolute path
REMOTE_PATH = '/home/dfci/media/ssd/Fast_Data/'
LOCAL_PATH = '/Home/dfci/DATA_DFCI/Acqui_Cond_and_Fast/data/Fast_Data'

# switch default plotting scheme to white
pg.setConfigOption('background', 'w')
pg.setConfigOption('foreground', 'k')

class CrossHairManager(object):
    def __init__(self):
        self.vLine = pg.InfiniteLine(angle=90, movable=False, pen=pg.mkPen('k', width=1))
        self.hLine = pg.InfiniteLine(angle=0, movable=False, pen=pg.mkPen('k', width=1), 
                                        label='{value:0.1f}',
                                        labelOpts={'position':0.98, 'color': (200,0,0), 'movable': True, 'fill': (0, 0, 200, 100)})

    def linkWithPlotItem(self, plt_it):
        self.plt = plt_it
        self.plt.addItem(self.vLine, ignoreBounds=True)
        self.plt.addItem(self.hLine, ignoreBounds=True)
        self.plt.scene().sigMouseMoved.connect(self.mouseMoved)
        
    def mouseMoved(self, evt):
        if self.plt.sceneBoundingRect().contains(evt):
            mousePoint = self.plt.vb.mapSceneToView(evt)
            #self.statusBar.showMessage(f"x={mousePoint.x()},\t   y={mousePoint.y()}" )
            self.vLine.setPos(mousePoint.x())
            self.hLine.setPos(mousePoint.y())
              

class AppForm(QMainWindow):
    def __init__(self, parent=None):
        QMainWindow.__init__(self, parent)        
        self.create_main_frame()
        self.setGeometry(0, 0, 2000, 600)
        self.setWindowTitle("WEST ICRH Fast Data Acquisition Analysis")
        # Fast data dictionnary
        self.data = dict()
        # sync remote files to local
        self.sync_files() 
        # fill the shot list with the list of available shots
        self.update_shot_list()        
        # default plotted data are from last shot file
        self.update_plot()

    def create_main_frame(self):
        self.main_frame = QWidget()
        # Default Fonts
        button_default_font = QtGui.QFont('SansSerif', 16)
        item_default_font = QtGui.QFont('SansSerif', 12)
        # Update Button
        self.refresh_button = QPushButton('Refresh', parent=self.main_frame)
        self.refresh_button.setFont(button_default_font)
        self.refresh_button.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_BrowserReload))
        self.refresh_button.clicked.connect(self.refresh)
        # Delete button
        self.delete_button = QPushButton('Delete', parent=self.main_frame)
        self.delete_button.setFont(button_default_font)
        self.delete_button.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_TrashIcon))
        self.delete_button.clicked.connect(self.delete_selected_shot)    
        # Plot button
        self.plot_button = QPushButton('Plot', parent=self.main_frame)
        self.plot_button.setFont(button_default_font)
        self.plot_button.clicked.connect(self.update_plot)
        self.plot_button.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_MediaPlay))                                  

        # Shots List
        self.shot_list_widget = QListWidget()
        self.shot_list_widget.setFont(item_default_font)
        self.shot_list_widget.itemClicked.connect(self.on_shot_list_clicked)

        # Layout construction
        vbox_shots = QVBoxLayout()
        vbox_shots.addWidget(self.refresh_button)
        vbox_shots.addWidget(self.delete_button)
        vbox_shots.addWidget(self.shot_list_widget)
        vbox_shots.addWidget(self.plot_button)
        
        self.l = pg.GraphicsLayoutWidget(border=(100,100,100))
        # 1st row : RF power
        self.PowQ1 = self.l.addPlot(row=0, col=0, name='Pow1', title='Q1 Power (<font color="blue">PiG</font>, <font color="red">PrG</font>, <font color="green">PiD</font>, <font color="magenta">PrD</font>)') #plotItem
        self.PowQ2 = self.l.addPlot(row=0, col=1, name='Pow2', title='Q2 Power (<font color="blue">PiG</font>, <font color="red">PrG</font>, <font color="green">PiD</font>, <font color="magenta">PrD</font>)')        
        self.PowQ4 = self.l.addPlot(row=0, col=2, name='Pow4', title='Q4 Power (<font color="blue">PiG</font>, <font color="red">PrG</font>, <font color="green">PiD</font>, <font color="magenta">PrD</font>)')
        
        # 2nd row : VSWR
        self.VSWRQ1 = self.l.addPlot(row=1, col=0, name='VSWRQ1', title='Q1 VSWR (<font color="blue">Gauche</font>, <font color="red">Droite</font>)')
        self.VSWRQ2 = self.l.addPlot(row=1, col=1, name='VSWRQ2', title='Q2 VSWR (<font color="blue">gauche</font>, <font color="red">Droite</font>)')
        self.VSWRQ4 = self.l.addPlot(row=1, col=2, name='VSWRQ4', title='Q4 VSWR (<font color="blue">Gauche</font>, <font color="red">Droite</font>)')
        self.VSWRQ1.setXLink(self.PowQ1)
        self.VSWRQ2.setXLink(self.PowQ2)
        self.VSWRQ4.setXLink(self.PowQ4)
        
        # 3nd row : RF voltages
        self.VolQ1 = self.l.addPlot(row=2, col=0, name='Vol1', title='Q1 Voltages (<font color="blue">V1</font>, <font color="red">V2</font>, <font color="green">V3</font>, <font color="magenta">V4</font>)')        
        self.VolQ2 = self.l.addPlot(row=2, col=1, name='Vol2', title='Q2 Voltages (<font color="blue">V1</font>, <font color="red">V2</font>, <font color="green">V3</font>, <font color="magenta">V4</font>)') 
        self.VolQ4 = self.l.addPlot(row=2, col=2, name='Vol4', title='Q4 Voltages (<font color="blue">V1</font>, <font color="red">V2</font>, <font color="green">V3</font>, <font color="magenta">V4</font>)')
        self.VolQ1.setXLink(self.PowQ1)
        self.VolQ2.setXLink(self.PowQ2)
        self.VolQ4.setXLink(self.PowQ4)   
        
        # 4rd row : RF phase
        self.PhaQ1 = self.l.addPlot(row=3, col=0, name='Pha1', title='Q1 Phase (Ph4+Ph1-Ph6, Ph5+Ph1-Ph7)')
        self.PhaQ2 = self.l.addPlot(row=3, col=1, name='Pha2', title='Q2 Phase (Ph4+Ph1-Ph6, Ph5+Ph1-Ph7)')
        self.PhaQ4 = self.l.addPlot(row=3, col=2, name='Pha4', title='Q4 Phase (Ph4+Ph1-Ph6, Ph5+Ph1-Ph7)')
        self.PhaQ1.setXLink(self.PowQ1)
        self.PhaQ2.setXLink(self.PowQ2)
        self.PhaQ4.setXLink(self.PowQ4)        

        # Layout assembly
        vbox_canvas = QVBoxLayout()            
        vbox_canvas.addWidget(self.l)

        hbox = QHBoxLayout()
        hbox.addLayout(vbox_shots, 1)
        hbox.addLayout(vbox_canvas, 15)

        self.main_frame.setLayout(hbox)
        self.setCentralWidget(self.main_frame)

        # Status bar
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        
        self.cross = CrossHairManager()
        self.cross.linkWithPlotItem(self.PowQ2)
        self.cross.linkWithPlotItem(self.VolQ2)
        self.cross.linkWithPlotItem(self.PhaQ2)
        
    def get_local_file_list(self):
        return io.list_local_files(local_data_path=LOCAL_PATH)

    def get_remote_file_list(self):
        return io.list_remote_files(remote_path=REMOTE_PATH)

    def sync_files(self):
        '''Synchronize remote files to local directory'''
        self.remote_files = self.get_remote_file_list()
        io.copy_remote_files_to_local(self.remote_files,
                                      local_data_path = LOCAL_PATH,
                                      remote_data_path= REMOTE_PATH)
        self.local_files = self.get_local_file_list()

    def update_shot_list(self):
        '''Update the list widget '''
        self.shot_list = fast.get_shot_list(self.local_files)
        self.shot_list_widget.clear()
        for shot in self.shot_list:
            self.shot_list_widget.addItem(str(shot))
        # look for empty shots
        self.empty_shots = self.list_empty_shots()
        
    def refresh(self):
        """ Refresh the shot list """
        # change the mouse cursor to indicate the user should wait until the file is processed
        QtGui.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
        # refresh files and update the shot list
        self.sync_files() 
        self.update_shot_list()
        # back the cursor to normal
        QtGui.QApplication.restoreOverrideCursor()
        
        
    def delete_selected_shot(self):
        """ Delete the shot which is currently selected in the shot list """
        # get the selected shot numbers
        for item in self.shot_list_widget.selectedItems():
            selected_shot = item.text()
            
            msgBox = QMessageBox()
            msgBox.setText(f'Voulez-vous supprimer les donnees associees au choc {selected_shot}')
            msgBox.setInformativeText('Les fichiers seront supprimees localement ET sur le serveur dfci')
            msgBox.setStandardButtons(QMessageBox.No | QMessageBox.Yes)
            msgBox.setDefaultButton(QMessageBox.No)
            reply = msgBox.exec_()
            if reply == QMessageBox.Yes:
                # change the mouse cursor to indicate the user should wait until the file are deleted
                QtGui.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
                # delete the files
                self.delete_shot_files(selected_shot)
                # back the cursor to normal
                QtGui.QApplication.restoreOverrideCursor()
            
    def delete_shot_files(self, shot=None):
        """ Delete the local and remote files associated to the given shot number """
        if shot:
            print(f'Suppression du choc {shot}!!')
            shot_filenames = fast.get_shot_filenames(shot, path='data/Fast_Data')
            # remove the relative path of the filenames   
            shot_filenames = [file.replace('data/Fast_Data/', '') for file in shot_filenames]
            print(f'Les fichiers suivant vont etre supprimes: {shot_filenames}')
            io.delete_remote_files(shot_filenames, remote_data_path=REMOTE_PATH)
            io.delete_local_files(shot_filenames, local_data_path=LOCAL_PATH)
            # update the shot list in order to supress the shot number we just had removed
            self.refresh()

    def color_shot(self, shot=None, color=QtGui.QColor('gray')):
        """ Change the shot number font color """
        if shot:
            res_list = self.shot_list_widget.findItems(str(shot), QtCore.Qt.MatchRegExp)
            res_list[0].setForeground(color)

    def list_empty_shots(self):
        ''' List the shot numbers which (at least one of the) associated files are empty '''
        empty_shots = []
        
        for shot in self.shot_list:
            shot_filenames = fast.get_shot_filenames(shot)
            for file in shot_filenames:
                if io.is_empty(file, local_data_path=''):
                    self.color_shot(shot)
                    empty_shots.append(shot)       

        return set(empty_shots)  # convert the list into a set to get unique values

    def on_shot_list_clicked(self, item):
        ''' Convert into DF when user select a shot number, essentially to speed-up the later plot'''
        # change the mouse cursor to indicate the user should wait until the file is processed
        QtGui.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
        
        # Convert the shot item label into shot number
        selected_shot = item.text()
        try:
            self.shot = int(selected_shot)
            print('Shot #{}'.format(self.shot))
        except ValueError:
            print('Bad shot number ! Something went wrong somewhere !!')     
     
        # Then convert the data into DF
        try:
            self.convert_to_DF(self.shot)
            print(f'Shot {self.shot} converted into DataFrame')
            
        except Exception as ex:
            template = "An exception of type {0} occurred. Arguments:\n{1!r}"
            message = template.format(type(ex).__name__, ex.args)
            print(message)
        # back the cursor to normal
        QtGui.QApplication.restoreOverrideCursor()
    
    def convert_to_DF(self, shot):
        ''' Convert a shot Fast Data into Pandas DataFrame '''
        # convert only if not been made before
        if not self.data.get(shot):
            print(f'Converting data of shot {shot}')
            self.data[shot] = fast.FastData(shot)

    def update_plot(self):
        # Update the graph with the data. 
        # Check first if the data are not empty before plotting
        try:
            # Q1
            if not self.data[self.shot].Q1_amplitude.empty:
                tG = self.data[self.shot].Q1_amplitude['PiG'].index/1e6
                tD = self.data[self.shot].Q1_amplitude['PiD'].index/1e6
                PiG = self.data[self.shot].Q1_amplitude['PiG'].values/10
                PiD = self.data[self.shot].Q1_amplitude['PiD'].values/10
                PrG = self.data[self.shot].Q1_amplitude['PrG'].values/10
                PrD = self.data[self.shot].Q1_amplitude['PrD'].values/10
                try:
                    # filter unphysical values
                    VSWR_Q1_G = np.abs((1 + np.sqrt(PrG/PiG))/(1 - np.sqrt(PrG/PiG)))
                    VSWR_Q1_G = np.where(VSWR_Q1_G<40, VSWR_Q1_G, 0)
                    VSWR_Q1_D = np.abs((1 + np.sqrt(PrD/PiD))/(1 - np.sqrt(PrD/PiD)))
                    VSWR_Q1_D = np.where(VSWR_Q1_D<40, VSWR_Q1_D, 0)
                except ValueError as e:
                    VSWR_Q1_G = np.zeros_like(PiG)
                    VSWR_Q1_D = np.zeros_like(PiD)
                               
                self.PowQ1.plot(pen='b', x=tG, y=PiG, clear=True)
                self.PowQ1.plot(pen='r', x=tG, y=PrG)
                self.PowQ1.plot(pen='g', x=tD, y=PiD)
                self.PowQ1.plot(pen='m', x=tD, y=PrD)
                self.PowQ1.plot(pen='k', x=self.data[self.shot].Q1_amplitude['Consigne'].index/1e6, 
                              y=self.data[self.shot].Q1_amplitude['Consigne'].values/10/2) 
                
                self.VSWRQ1.plot(pen='b', x=tG, y=VSWR_Q1_G, clear=True)
                self.VSWRQ1.plot(pen='r', x=tD, y=VSWR_Q1_D)
                self.VSWRQ1.setYRange(1, 5)
                
                self.VolQ1.plot(pen='b', x=self.data[self.shot].Q1_amplitude['V1'].index/1e6,
                               y=self.data[self.shot].Q1_amplitude['V1'].values, clear=True)
                self.VolQ1.plot(pen='r', x=self.data[self.shot].Q1_amplitude['V2'].index/1e6,
                               y=self.data[self.shot].Q1_amplitude['V2'].values)
                self.VolQ1.plot(pen='g', x=self.data[self.shot].Q1_amplitude['V3'].index/1e6,
                               y=self.data[self.shot].Q1_amplitude['V3'].values)
                self.VolQ1.plot(pen='m', x=self.data[self.shot].Q1_amplitude['V4'].index/1e6,
                               y=self.data[self.shot].Q1_amplitude['V4'].values)

            if not self.data[self.shot].Q1_phase.empty:               
                self.PhaQ1.plot(pen='b', x=self.data[self.shot].Q1_phase['Ph1'].index/1e6, 
                              y=(self.data[self.shot].Q1_phase['Ph4'].values/100 +
                                 self.data[self.shot].Q1_phase['Ph1'].values/100 -
                                 self.data[self.shot].Q1_phase['Ph6'].values/100) % 360, clear=True)
                self.PhaQ1.plot(pen='r', x=self.data[self.shot].Q1_phase['Ph2'].index/1e6, 
                              y=(self.data[self.shot].Q1_phase['Ph5'].values/100 +
                                 self.data[self.shot].Q1_phase['Ph1'].values/100 -  
                                 self.data[self.shot].Q1_phase['Ph7'].values/100) % 360)

            # Q2 
            if not self.data[self.shot].Q2_amplitude.empty:
                tG = self.data[self.shot].Q2_amplitude['PiG'].index/1e6
                tD = self.data[self.shot].Q2_amplitude['PiD'].index/1e6
                PiG = self.data[self.shot].Q2_amplitude['PiG'].values/10
                PiD = self.data[self.shot].Q2_amplitude['PiD'].values/10
                PrG = self.data[self.shot].Q2_amplitude['PrG'].values/10
                PrD = self.data[self.shot].Q2_amplitude['PrD'].values/10
                try:
                    # filter unphysical values
                    VSWR_Q2_G = np.abs((1 + np.sqrt(PrG/PiG))/(1 - np.sqrt(PrG/PiG)))
                    VSWR_Q2_G = np.where(VSWR_Q2_G<40, VSWR_Q2_G, 0)
                    VSWR_Q2_D = np.abs((1 + np.sqrt(PrD/PiD))/(1 - np.sqrt(PrD/PiD)))
                    VSWR_Q2_D = np.where(VSWR_Q2_D<40, VSWR_Q2_D, 0)
                except ValueError as e:
                    VSWR_Q2_G = np.zeros_like(PiG)
                    VSWR_Q2_D = np.zeros_like(PiD)
                               
                self.PowQ2.plot(pen='b', x=tG, y=PiG, clear=True)
                self.PowQ2.plot(pen='r', x=tG, y=PrG)
                self.PowQ2.plot(pen='g', x=tD, y=PiD)
                self.PowQ2.plot(pen='m', x=tD, y=PrD)
                self.PowQ2.plot(pen='k', x=self.data[self.shot].Q2_amplitude['Consigne'].index/1e6, 
                              y=self.data[self.shot].Q2_amplitude['Consigne'].values/10/2) 
                
                self.VSWRQ2.plot(pen='b', x=tG, y=VSWR_Q2_G, clear=True)
                self.VSWRQ2.plot(pen='r', x=tD, y=VSWR_Q2_D)
                self.VSWRQ2.setYRange(1, 5)
                
                self.VolQ2.plot(pen='b', x=self.data[self.shot].Q2_amplitude['V1'].index/1e6,
                               y=self.data[self.shot].Q2_amplitude['V1'].values, clear=True)
                self.VolQ2.plot(pen='r', x=self.data[self.shot].Q2_amplitude['V2'].index/1e6,
                               y=self.data[self.shot].Q2_amplitude['V2'].values)
                self.VolQ2.plot(pen='g', x=self.data[self.shot].Q2_amplitude['V3'].index/1e6,
                               y=self.data[self.shot].Q2_amplitude['V3'].values)
                self.VolQ2.plot(pen='m', x=self.data[self.shot].Q2_amplitude['V4'].index/1e6,
                               y=self.data[self.shot].Q2_amplitude['V4'].values)

            if not self.data[self.shot].Q2_phase.empty:               
                self.PhaQ2.plot(pen='b', x=self.data[self.shot].Q2_phase['Ph1'].index/1e6, 
                              y=(self.data[self.shot].Q2_phase['Ph4'].values/100 +
                                 self.data[self.shot].Q2_phase['Ph1'].values/100 -
                                 self.data[self.shot].Q2_phase['Ph6'].values/100) % 360, clear=True)
                self.PhaQ2.plot(pen='r', x=self.data[self.shot].Q2_phase['Ph2'].index/1e6, 
                              y=(self.data[self.shot].Q2_phase['Ph5'].values/100 +
                                 self.data[self.shot].Q2_phase['Ph1'].values/100 -  
                                 self.data[self.shot].Q2_phase['Ph7'].values/100) % 360)

            # Q4
            if not self.data[self.shot].Q4_amplitude.empty:
                tG = self.data[self.shot].Q4_amplitude['PiG'].index/1e6
                tD = self.data[self.shot].Q4_amplitude['PiD'].index/1e6
                PiG = self.data[self.shot].Q4_amplitude['PiG'].values/10
                PiD = self.data[self.shot].Q4_amplitude['PiD'].values/10
                PrG = self.data[self.shot].Q4_amplitude['PrG'].values/10
                PrD = self.data[self.shot].Q4_amplitude['PrD'].values/10
                #try:
                    #VSWR_Q4_G = (1 + np.sqrt(PrG/PiG))/(1 - np.sqrt(PrG/PiG))
                    #VSWR_Q4_D = (1 + np.sqrt(PrD/PiD))/(1 - np.sqrt(PrD/PiD))

                #except Exception as e:
                VSWR_Q4_G = np.zeros_like(PiG)
                VSWR_Q4_D = np.zeros_like(PiD)
 
                self.PowQ4.plot(pen='b', x=tG, y=PiG, clear=True)
                self.PowQ4.plot(pen='r', x=tG, y=PrG)
                self.PowQ4.plot(pen='g', x=tD, y=PiD)
                self.PowQ4.plot(pen='m', x=tD, y=PrD)               
                
                self.PowQ4.plot(pen='k', x=self.data[self.shot].Q4_amplitude['Consigne'].index/1e6, 
                              y=self.data[self.shot].Q4_amplitude['Consigne'].values/10/2)
                              
                self.VSWRQ4.plot(pen='b', x=tG, y=VSWR_Q4_G)
                self.VSWRQ4.plot(pen='r', x=tD, y=VSWR_Q4_D)
                self.VSWRQ4.setYRange(1, 5)
                                                             
                self.VolQ4.plot(pen='b', x=self.data[self.shot].Q4_amplitude['V1'].index/1e6,
                               y=self.data[self.shot].Q4_amplitude['V1'].values, clear=True)
                self.VolQ4.plot(pen='r', x=self.data[self.shot].Q4_amplitude['V2'].index/1e6,
                               y=self.data[self.shot].Q4_amplitude['V2'].values)
                self.VolQ4.plot(pen='g', x=self.data[self.shot].Q4_amplitude['V3'].index/1e6,
                               y=self.data[self.shot].Q4_amplitude['V3'].values)
                self.VolQ4.plot(pen='m', x=self.data[self.shot].Q4_amplitude['V4'].index/1e6,
                               y=self.data[self.shot].Q4_amplitude['V4'].values)
            if not self.data[self.shot].Q4_phase.empty:               
                self.PhaQ4.plot(pen='b', x=self.data[self.shot].Q4_phase['Ph1'].index/1e6, 
                              y=(self.data[self.shot].Q4_phase['Ph4'].values/100 +
                                 self.data[self.shot].Q4_phase['Ph1'].values/100 -
                                 self.data[self.shot].Q4_phase['Ph6'].values/100) % 360, clear=True)
                self.PhaQ4.plot(pen='r', x=self.data[self.shot].Q4_phase['Ph2'].index/1e6, 
                              y=(self.data[self.shot].Q4_phase['Ph5'].values/100 +
                                 self.data[self.shot].Q4_phase['Ph1'].values/100 -  
                                 self.data[self.shot].Q4_phase['Ph7'].values/100) % 360)
                    
        except AttributeError as e:
            print('No data or error in data in the shot!')
            print(e)

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
