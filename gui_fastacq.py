import sys
from matplotlib.figure import Figure
import ICRH_FastData as fast
import ICRH_FileIO as io
import matplotlib

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
    matplotlib.use('Qt5Agg')
except ImportError:    
    import PyQt4.QtCore as QtCore
    import PyQt4.QtGui as QtGui
    import PyQt4.QtGui as QtWidgets
    from PyQt4.QtGui import (QMainWindow, QApplication, QWidget, QPushButton, QListWidget,
                                 QHBoxLayout, QVBoxLayout)
    from matplotlib.backends.backend_qt4agg import (
            FigureCanvasQTAgg as FigureCanvas,
            NavigationToolbar2QT as NavigationToolbar)
    matplotlib.use('Qt4Agg')

import pyqtgraph as pg
# switch default plotting scheme to white
pg.setConfigOption('background', 'w')
pg.setConfigOption('foreground', 'k')


class AppForm(QMainWindow):
    def __init__(self, parent=None):
        QMainWindow.__init__(self, parent)        
        self.create_main_frame()
        self.setGeometry(0, 0, 1600, 600)
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
        # Figure and toolbar
        self.fig = Figure((20.0, 6.0), dpi=100)
        self.canvas = FigureCanvas(self.fig)
        self.mpl_toolbar = NavigationToolbar(self.canvas, self.main_frame)
        self.canvas.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.canvas.setFocus()
        # Embedding in Qt4
        self.canvas.setParent(self.main_frame)
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

        # Conditioning Shots List
        self.shot_list_widget = QListWidget()
        self.shot_list_widget.setFont(item_default_font)
        self.shot_list_widget.itemClicked.connect(self.on_shot_list_clicked)

        # Layout construction
        vbox_shots = QVBoxLayout()
        vbox_shots.addWidget(self.refresh_button)
        vbox_shots.addWidget(self.shot_list_widget)
        vbox_shots.addWidget(self.plot_button)
        
        vbox_canvas = QVBoxLayout()
        #vbox_canvas.addWidget(self.canvas)  # the matplotlib canvas
        #vbox_canvas.addWidget(self.mpl_toolbar)
        self.l = pg.GraphicsLayoutWidget(border=(100,100,100))
        self.PowQ1 = self.l.addPlot(row=0, col=0, name='Pow')
        self.PhaQ1 = self.l.addPlot(row=0, col=1, name='Pha')
        #self.l.nextRow()
        self.PowQ2 = self.l.addPlot(row=1, col=0, name='Pow')
        self.PowQ2.setXLink(self.PowQ1)
        self.PhaQ2 = self.l.addPlot(row=1, col=1, name='Pha')
        self.PhaQ2.setXLink(self.PhaQ1)
        #self.l.nextRow()
        self.PowQ4 = self.l.addPlot(row=2, col=0, name='Pow')
        self.PowQ4.setXLink(self.PowQ1)
        self.PhaQ4 = self.l.addPlot(row=2, col=1, name='Pha')
        self.PhaQ4.setXLink(self.PhaQ1)
                
        vbox_canvas.addWidget(self.l)



        hbox = QHBoxLayout()
        hbox.addLayout(vbox_shots, 1)
        hbox.addLayout(vbox_canvas, 6)


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
            print('Shot {} converted into DataFrame'.format(self.shot))
        except Exception as ex:
            template = "An exception of type {0} occurred. Arguments:\n{1!r}"
            message = template.format(type(ex).__name__, ex.args)
            print(message)
    
    def convert_to_DF(self, shot):
        ''' Convert a shot Fast Data into Pandas DataFrame '''
        # convert only if not been made before
        if not self.data.get(shot):
            print('Converting data of shot #{}'.format(shot))
            self.data[shot] = fast.FastData(shot)
        
    
    def update_plot(self):
        self.fig.clear()
        self.axes_PowQ1 = self.fig.add_subplot(231) # amplitudes
        self.axes_PowQ2 = self.fig.add_subplot(232)
        self.axes_PowQ4 = self.fig.add_subplot(233)
        self.axes_PhaQ1 = self.fig.add_subplot(234) # amplitudes
        self.axes_PhaQ2 = self.fig.add_subplot(235)
        self.axes_PhaQ4 = self.fig.add_subplot(236)
        try:
            if  not self.data[self.shot].Q1_amplitude.empty:
                self.PowQ1.plot(pen='b', x=self.data[self.shot].Q1_amplitude['PiG'].index/1e6, 
                              y=self.data[self.shot].Q1_amplitude['PiG'].values)
                self.PowQ1.plot(pen='r', x=self.data[self.shot].Q1_amplitude['PiD'].index/1e6, 
                              y=self.data[self.shot].Q1_amplitude['PiD'].values)
            if  not self.data[self.shot].Q2_amplitude.empty:
                self.PowQ2.plot(pen='b', x=self.data[self.shot].Q2_amplitude['PiG'].index/1e6, 
                              y=self.data[self.shot].Q2_amplitude['PiG'].values)
                self.PowQ2.plot(pen='r', x=self.data[self.shot].Q2_amplitude['PiD'].index/1e6, 
                              y=self.data[self.shot].Q2_amplitude['PiD'].values)
            if  not self.data[self.shot].Q4_amplitude.empty:
                self.PowQ4.plot(pen='b', x=self.data[self.shot].Q4_amplitude['PiG'].index/1e6, 
                              y=self.data[self.shot].Q4_amplitude['PiG'].values)
                self.PowQ4.plot(pen='r', x=self.data[self.shot].Q4_amplitude['PiD'].index/1e6, 
                              y=self.data[self.shot].Q4_amplitude['PiD'].values)            
            
        except AttributeError as e:
            print('No shot exist yet!')
            print(e)
                                         
#        self.axes3 = self.fig.add_subplot(223)
#        self.axes4 = self.fig.add_subplot(224)
#        
#        time = data.index/1e3 # display time in ms
#        self.axes1.plot(time, data.PiG/10, time, data.PrG/10, alpha=0.7)
#        self.axes2.plot(time, data.PiD/10, time, data.PrD/10, alpha=0.7)
#        self.axes3.plot(time, data.V1, time, data.V2, alpha=0.7)
#        self.axes4.plot(time, data.V3, time, data.V4, alpha=0.7)
#        self.axes3.set_xlabel('Time [ms]')
#        self.axes4.set_xlabel('Time [ms]')
#        self.axes1.set_ylabel('Power [kW]')
#        self.axes3.set_ylabel('Voltage [V]')
#        self.fig.tight_layout()
        self.canvas.draw()



def main():
    # Hack to be able to run the code from spyder
    # taken from http://stackoverflow.com/questions/19459299/running-a-pyqt-application-twice-from-one-prompt-in-spyder
    if QtCore.QCoreApplication.instance() != None:
        app = QtCore.QCoreApplication.instance()
    else:
        app = QApplication(sys.argv)
    form = AppForm()
    form.show()
    app.exec_()

if __name__ == "__main__":
    main()