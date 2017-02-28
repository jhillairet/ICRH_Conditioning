import sys
import numpy as np
from matplotlib.figure import Figure
from matplotlib.backend_bases import key_press_handler
from matplotlib.backends.backend_qt4agg import (
    FigureCanvasQTAgg as FigureCanvas,
    NavigationToolbar2QT as NavigationToolbar)

from PyQt4.QtCore import *
from PyQt4.QtGui import *

from ICRH_Conditioning import *

class AppForm(QMainWindow):
    def __init__(self, parent=None):
        QMainWindow.__init__(self, parent)        
        self.create_main_frame()
        self.data = self.get_last_conditioning_data()


    def create_main_frame(self):
        self.main_frame = QWidget()

        self.fig = Figure((10.0, 6.0), dpi=100)
        self.canvas = FigureCanvas(self.fig)
        self.canvas.setParent(self.main_frame)
        
        self.plot_button = QPushButton('Plot', parent=self.main_frame)
        self.plot_button.clicked.connect(self.update_plot)
 
        
        
        self.canvas.setFocusPolicy(Qt.StrongFocus)
        self.canvas.setFocus()

        self.mpl_toolbar = NavigationToolbar(self.canvas, self.main_frame)

        self.canvas.mpl_connect('key_press_event', self.on_key_press)

        vbox = QVBoxLayout()
        vbox.addWidget(self.canvas)  # the matplotlib canvas
        vbox.addWidget(self.mpl_toolbar)
        vbox.addWidget(self.plot_button)

        self.main_frame.setLayout(vbox)
        self.setCentralWidget(self.main_frame)
        
    

    def get_last_conditioning_data(self):
        # Get the conditioning data from last conditioning file. 
        remote_file_list = list_remote_files()
        copy_remote_files_to_local(remote_file_list)
    
        local_file_list = list_local_files()
        data = read_conditoning_data(local_file_list[-1])
        return data

    def update_plot(self):
        self.fig.clear()
        self.axes1 = self.fig.add_subplot(221) 
        self.axes2 = self.fig.add_subplot(222)
        self.axes3 = self.fig.add_subplot(223)
        self.axes4 = self.fig.add_subplot(224)
        
        time = self.data.index/1e3 # display time in ms
        self.axes1.plot(time, self.data.PiG/10, time, self.data.PrG/10)
        self.axes2.plot(time, self.data.PiD/10, time, self.data.PrD/10)
        self.axes3.plot(time, self.data.V1, time, self.data.V2)
        self.axes4.plot(time, self.data.V3, time, self.data.V4)
        self.axes3.set_xlabel('Time [ms]')
        self.axes4.set_xlabel('Time [ms]')
        self.axes1.set_ylabel('Power [kW]')
        self.axes3.set_ylabel('Voltage [V]')
        self.fig.tight_layout()
        self.canvas.draw()
    

    def on_key_press(self, event):
        print('you pressed', event.key)
        self.data = self.get_last_conditioning_data()
        # implement the default mpl key press events described at
        # http://matplotlib.org/users/navigation_toolbar.html#navigation-keyboard-shortcuts
        key_press_handler(event, self.canvas, self.mpl_toolbar)


def main():
    app = QApplication(sys.argv)
    form = AppForm()
    form.show()
    app.exec_()

if __name__ == "__main__":
    main()