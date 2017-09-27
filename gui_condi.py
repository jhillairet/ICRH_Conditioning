import sys
import matplotlib
from matplotlib.figure import Figure
import ICRH_Conditioning as condi
import ICRH_FileIO as io
import os

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
        self.setGeometry(0, 0, 1600, 600)
        self.setWindowTitle("WEST ICRH Conditoning Analysis")

        # sync remote files to local
        self.sync_files()

        # fill the shot table with the date of the last shots
        self.update_shot_table()
        # default plotted data are from last shot file
        self.data = self.get_conditioning_data(-1)
        self.update_metadata_table()
        self.update_plot()

    def create_main_frame(self):
        self.main_frame = QWidget()
        # Figure and toolbar
        self.fig = Figure((10.0, 6.0), dpi=100)
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
        vbox_canvas.addWidget(self.canvas)  # the matplotlib canvas
        vbox_canvas.addWidget(self.mpl_toolbar)

        hbox = QHBoxLayout()
        hbox.addLayout(vbox_shots)
        hbox.addLayout(vbox_metadata)
        hbox.addLayout(vbox_canvas)

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
        self.data = self.get_conditioning_data(-1)
        self.update_metadata_table(-1)
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
            self.fig.clear()
            self.axes1 = self.fig.add_subplot(221)
            self.axes2 = self.fig.add_subplot(222)
            self.axes3 = self.fig.add_subplot(223)
            self.axes4 = self.fig.add_subplot(224)
            time = data.index/1e3  # display time in ms
            self.axes1.plot(time, data.PiG/10, time, data.PrG/10, alpha=0.7)
            self.axes2.plot(time, data.PiD/10, time, data.PrD/10, alpha=0.7)
            self.axes3.plot(time, data.V1, time, data.V2, alpha=0.7)
            self.axes4.plot(time, data.V3, time, data.V4, alpha=0.7)
            self.axes3.set_xlabel('Time [ms]')
            self.axes4.set_xlabel('Time [ms]')
            self.axes1.set_ylabel('Power [kW]')
            self.axes3.set_ylabel('Voltage [V]')
            self.fig.tight_layout()
            self.canvas.draw()


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
