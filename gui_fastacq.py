import sys

# Qt5/Qt4 compatibility
try: 
    import PyQt5.QtCore as QtCore
    import PyQt5.QtGui as QtGui 
    import PyQt5.QtWidgets as QtWidgets
    from PyQt5.QtWidgets import (QMainWindow, QApplication, QWidget, QPushButton, QListWidget,
                                 QHBoxLayout, QVBoxLayout)
    from matplotlib.backends.backend_qt5agg import (
            FigureCanvasQTAgg as FigureCanvas,
            NavigationToolbar2QT as NavigationToolbar)
except ImportError:    
    import PyQt4.QtCore as QtCore
    import PyQt4.QtGui as QtGui
    import PyQt4.QtGui as QtWidgets
    from PyQt4.QtGui import (QMainWindow, QApplication, QWidget, QPushButton, QListWidget,
                                 QHBoxLayout, QVBoxLayout)
    from matplotlib.backends.backend_qt4agg import (
            FigureCanvasQTAgg as FigureCanvas,
            NavigationToolbar2QT as NavigationToolbar)

import pyqtgraph as pg

import ICRH_FastData as fast
import ICRH_FileIO as io

# switch default plotting scheme to white
pg.setConfigOption('background', 'w')
pg.setConfigOption('foreground', 'k')

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
        # Plot button
        self.plot_button = QPushButton('Plot', parent=self.main_frame)
        self.plot_button.setFont(button_default_font)
        self.plot_button.clicked.connect(self.update_plot)                                   

        # Shots List
        self.shot_list_widget = QListWidget()
        self.shot_list_widget.setFont(item_default_font)
        self.shot_list_widget.itemClicked.connect(self.on_shot_list_clicked)

        # Layout construction
        vbox_shots = QVBoxLayout()
        vbox_shots.addWidget(self.refresh_button)
        vbox_shots.addWidget(self.shot_list_widget)
        vbox_shots.addWidget(self.plot_button)
        
        self.l = pg.GraphicsLayoutWidget(border=(100,100,100))
        # 1st row : RF power
        self.PowQ1 = self.l.addPlot(row=0, col=0, name='Pow1', title='Q1 Power (PiG, PrG, PiD, PrD)')
        self.PowQ2 = self.l.addPlot(row=0, col=1, name='Pow2', title='Q2 Power (PiG, PrG, PiD, PrD)')        
        self.PowQ4 = self.l.addPlot(row=0, col=2, name='Pow4', title='Q4 Power (PiG, PrG, PiD, PrD)')
        
        # 2nd row : RF voltages
        self.VolQ1 = self.l.addPlot(row=1, col=0, name='Vol1', title='Q1 Voltages (V1, V2, V3, V4)')        
        self.VolQ2 = self.l.addPlot(row=1, col=1, name='Vol2', title='Q2 Voltages (V1, V2, V3, V4)') 
        self.VolQ4 = self.l.addPlot(row=1, col=2, name='Vol4', title='Q4 Voltages (V1, V2, V3, V4)')
        self.VolQ1.setXLink(self.PowQ1)
        self.VolQ2.setXLink(self.PowQ2)
        self.VolQ4.setXLink(self.PowQ4)   
        
        # 3rd row : RF phase
        self.PhaQ1 = self.l.addPlot(row=2, col=0, name='Pha1', title='Q1 Phase (Ph4+Ph1-Ph6, Ph5+Ph1-Ph7)')
        self.PhaQ2 = self.l.addPlot(row=2, col=1, name='Pha2', title='Q2 Phase (Ph4+Ph1-Ph6, Ph5+Ph1-Ph7)')
        self.PhaQ4 = self.l.addPlot(row=2, col=2, name='Pha4', title='Q4 Phase (Ph4+Ph1-Ph6, Ph5+Ph1-Ph7)')
        self.PhaQ1.setXLink(self.PowQ1)
        self.PhaQ2.setXLink(self.PowQ2)
        self.PhaQ4.setXLink(self.PowQ4)        

        #self.l.nextRow()
        vbox_canvas = QVBoxLayout()                
        vbox_canvas.addWidget(self.l)

        hbox = QHBoxLayout()
        hbox.addLayout(vbox_shots, 1)
        hbox.addLayout(vbox_canvas, 15)

        self.main_frame.setLayout(hbox)
        self.setCentralWidget(self.main_frame)

    def get_local_file_list(self):
        return io.list_local_files(local_data_path = 'data/Fast_Data/')

    def get_remote_file_list(self):
        return io.list_remote_files(remote_path='/media/ssd/Fast_Data')

    def sync_files(self):
        '''Synchronize remote files to local directory'''
        self.remote_files = self.get_remote_file_list()
        io.copy_remote_files_to_local(self.remote_files,
                                      local_data_path = 'data/Fast_Data/',
                                      remote_data_path='/media/ssd/Fast_Data')
        self.local_files = self.get_local_file_list()

    def update_shot_list(self):
        '''Update the list widget '''
        self.shot_list = fast.get_shot_list(self.local_files)
        self.shot_list_widget.clear()
        for shot in self.shot_list:
            self.shot_list_widget.addItem(str(shot))
    
    def refresh(self):
        self.sync_files() 
        self.update_shot_list()
    
    def on_shot_list_clicked(self, item):
        ''' Convert into DF when user select a shot number, essentially to speed-up the later plot'''
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
                self.PowQ1.plot(pen='b', x=self.data[self.shot].Q1_amplitude['PiG'].index/1e6, 
                              y=self.data[self.shot].Q1_amplitude['PiG'].values, clear=True)
                self.PowQ1.plot(pen='r', x=self.data[self.shot].Q1_amplitude['PrG'].index/1e6, 
                              y=self.data[self.shot].Q1_amplitude['PrG'].values)
                self.PowQ1.plot(pen='g', x=self.data[self.shot].Q1_amplitude['PiD'].index/1e6, 
                              y=self.data[self.shot].Q1_amplitude['PiD'].values)
                self.PowQ1.plot(pen='m', x=self.data[self.shot].Q1_amplitude['PrD'].index/1e6, 
                              y=self.data[self.shot].Q1_amplitude['PrD'].values)
                
                self.VolQ1.plot(pen='b', x=self.data[self.shot].Q1_amplitude['V1'].index/1e6,
                               y=self.data[self.shot].Q1_amplitude['V1'].values/10, clear=True)
                self.VolQ1.plot(pen='r', x=self.data[self.shot].Q1_amplitude['V2'].index/1e6,
                               y=self.data[self.shot].Q1_amplitude['V2'].values/10)
                self.VolQ1.plot(pen='g', x=self.data[self.shot].Q1_amplitude['V3'].index/1e6,
                               y=self.data[self.shot].Q1_amplitude['V3'].values/10)
                self.VolQ1.plot(pen='m', x=self.data[self.shot].Q1_amplitude['V4'].index/1e6,
                               y=self.data[self.shot].Q1_amplitude['V4'].values/10)

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
                self.PowQ2.plot(pen='b', x=self.data[self.shot].Q2_amplitude['PiG'].index/1e6, 
                              y=self.data[self.shot].Q2_amplitude['PiG'].values, clear=True)
                self.PowQ2.plot(pen='r', x=self.data[self.shot].Q2_amplitude['PrG'].index/1e6, 
                              y=self.data[self.shot].Q2_amplitude['PrG'].values)
                self.PowQ2.plot(pen='g', x=self.data[self.shot].Q2_amplitude['PiD'].index/1e6, 
                              y=self.data[self.shot].Q2_amplitude['PiD'].values)
                self.PowQ2.plot(pen='m', x=self.data[self.shot].Q2_amplitude['PrD'].index/1e6, 
                              y=self.data[self.shot].Q2_amplitude['PrD'].values)
                
                self.VolQ2.plot(pen='b', x=self.data[self.shot].Q2_amplitude['V1'].index/1e6,
                               y=self.data[self.shot].Q2_amplitude['V1'].values/10, clear=True)
                self.VolQ2.plot(pen='r', x=self.data[self.shot].Q2_amplitude['V2'].index/1e6,
                               y=self.data[self.shot].Q2_amplitude['V2'].values/10)
                self.VolQ2.plot(pen='g', x=self.data[self.shot].Q2_amplitude['V3'].index/1e6,
                               y=self.data[self.shot].Q2_amplitude['V3'].values/10)
                self.VolQ2.plot(pen='m', x=self.data[self.shot].Q2_amplitude['V4'].index/1e6,
                               y=self.data[self.shot].Q2_amplitude['V4'].values/10)

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
                self.PowQ4.plot(pen='b', x=self.data[self.shot].Q4_amplitude['PiG'].index/1e6, 
                              y=self.data[self.shot].Q4_amplitude['PiG'].values, clear=True)
                self.PowQ4.plot(pen='r', x=self.data[self.shot].Q4_amplitude['PrG'].index/1e6, 
                              y=self.data[self.shot].Q4_amplitude['PrG'].values)
                self.PowQ4.plot(pen='g', x=self.data[self.shot].Q4_amplitude['PiD'].index/1e6, 
                              y=self.data[self.shot].Q4_amplitude['PiD'].values)
                self.PowQ4.plot(pen='m', x=self.data[self.shot].Q4_amplitude['PrD'].index/1e6, 
                              y=self.data[self.shot].Q4_amplitude['PrD'].values)
                
                self.VolQ4.plot(pen='b', x=self.data[self.shot].Q4_amplitude['V1'].index/1e6,
                               y=self.data[self.shot].Q4_amplitude['V1'].values/10, clear=True)
                self.VolQ4.plot(pen='r', x=self.data[self.shot].Q4_amplitude['V2'].index/1e6,
                               y=self.data[self.shot].Q4_amplitude['V2'].values/10)
                self.VolQ4.plot(pen='g', x=self.data[self.shot].Q4_amplitude['V3'].index/1e6,
                               y=self.data[self.shot].Q4_amplitude['V3'].values/10)
                self.VolQ4.plot(pen='m', x=self.data[self.shot].Q4_amplitude['V4'].index/1e6,
                               y=self.data[self.shot].Q4_amplitude['V4'].values/10)
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
            print('No data in the shot!')
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
