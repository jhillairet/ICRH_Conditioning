import sys
import matplotlib
from matplotlib.figure import Figure
import ICRH_Conditioning as condi

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
    matplotlib.use('Qt5Agg')
except ImportError:    
    import PyQt4.QtCore as QtCore
    import PyQt4.QtGui as QtGui
    import PyQt4.QtGui as QtWidgets
    from PyQt4.QtGui import (QMainWindow, QApplication, QWidget, QPushButton, 
                                 QHBoxLayout, QVBoxLayout, QTableWidget, QTableWidgetItem)
    from matplotlib.backends.backend_qt4agg import (
            FigureCanvasQTAgg as FigureCanvas,
            NavigationToolbar2QT as NavigationToolbar)
    matplotlib.use('Qt4Agg')





class AppForm(QMainWindow):
    def __init__(self, parent=None):
        QMainWindow.__init__(self, parent)        
        self.create_main_frame()
        # sync remote files to local
        self.sync_files() 
        # fill the shot table with the date of the last shots
        self.update_shot_table()
        self.shot_table.resizeColumnsToContents()
        #self.shot_table.resizeRowsToContents()
        
        # default plotted data are from last shot file
        self.data = self.get_conditioning_data(-1)
        self.update_plot()

    def create_main_frame(self):
        self.main_frame = QWidget()

        self.fig = Figure((10.0, 6.0), dpi=100)
        self.canvas = FigureCanvas(self.fig)
        # Embedding in Qt4
        self.canvas.setParent(self.main_frame)
        # Update Button
        self.refresh_button = QPushButton('Refresh', parent=self.main_frame)
        self.refresh_button.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_BrowserReload))
        self.refresh_button.clicked.connect(self.refresh)
        # Conditioning Shots Table
        self.shot_table = QTableWidget(20, 1, parent=self.main_frame)
        self.shot_table.setHorizontalHeaderLabels(('Conditioning Shot#',))
        self.shot_table.cellClicked.connect(self.on_shot_table_clicked)
        self.shot_table.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.shot_table.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.shot_table.horizontalHeader().setStretchLastSection(True);

        self.canvas.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.canvas.setFocus()

        self.mpl_toolbar = NavigationToolbar(self.canvas, self.main_frame)

        #self.canvas.mpl_connect('key_press_event', self.on_key_press)

        vbox_panel = QVBoxLayout()
        vbox_panel.addWidget(self.refresh_button)
        vbox_panel.addWidget(self.shot_table)
        
        vbox_canvas = QVBoxLayout()
        vbox_canvas.addWidget(self.canvas)  # the matplotlib canvas
        vbox_canvas.addWidget(self.mpl_toolbar)

        hbox = QHBoxLayout()
        hbox.addLayout(vbox_panel)
        hbox.addLayout(vbox_canvas)

        self.main_frame.setLayout(hbox)
        self.setCentralWidget(self.main_frame)
        
    
    def get_local_file_list(self):
        return condi.list_local_files()
    
    def get_remote_file_list(self):
        return condi.list_remote_files()
    
    def sync_files(self):
        self.remote_files = self.get_remote_file_list()
        condi.copy_remote_files_to_local(self.remote_files)
        self.local_files = self.get_local_file_list()

    def update_shot_table(self):
        for row,filename in enumerate(self.local_files):
            self.shot_table.setItem(row,0,QTableWidgetItem(filename))
        
    def refresh(self):
        self.update_shot_table()
        self.shot_table.selectRow(0)
        self.data = self.get_conditioning_data(-1)
        self.update_plot()
        
    def on_shot_table_clicked(self, row, col):
        print("Click on " + str(row) + " " + str(col))
        print(self.shot_table.item(row,col))
        print('Plotting shot {}'.format(row))
        self.data = self.get_conditioning_data(row)
        self.update_plot()
        
    def get_conditioning_data(self, idx=-1):
        data = condi.read_conditoning_data(self.local_files[idx])
        print(data.head())
        return data
    
    def update_plot(self):
        data = self.data
        self.fig.clear()
        self.axes1 = self.fig.add_subplot(221) 
        self.axes2 = self.fig.add_subplot(222)
        self.axes3 = self.fig.add_subplot(223)
        self.axes4 = self.fig.add_subplot(224)
        
        time = data.index/1e3 # display time in ms
        self.axes1.plot(time, data.PiG/10, time, data.PrG/10)
        self.axes2.plot(time, data.PiD/10, time, data.PrD/10)
        self.axes3.plot(time, data.V1, time, data.V2)
        self.axes4.plot(time, data.V3, time, data.V4)
        self.axes3.set_xlabel('Time [ms]')
        self.axes4.set_xlabel('Time [ms]')
        self.axes1.set_ylabel('Power [kW]')
        self.axes3.set_ylabel('Voltage [V]')
        self.fig.tight_layout()
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