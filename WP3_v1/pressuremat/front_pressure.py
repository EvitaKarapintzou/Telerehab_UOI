import sys
import numpy as np
from PyQt5 import QtWidgets
import pyqtgraph as pg

class RandomDataApp(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Random 48x48 Data Visualization')

        # Create the main widget
        self.main_widget = QtWidgets.QWidget(self)
        self.setCentralWidget(self.main_widget)
        
        # Create a layout
        layout = QtWidgets.QVBoxLayout(self.main_widget)

        # Create the image view widget for displaying the heatmap
        self.image_view = pg.ImageView()
        layout.addWidget(self.image_view)

        # Set up a timer to refresh the display
        self.timer = pg.QtCore.QTimer(self)
        self.timer.timeout.connect(self.update_heatmap)
        self.timer.start(100)  # Update every 100 milliseconds (0.1 seconds)

        self.show()

    def update_heatmap(self):
        # Generate random 48x48 data
        #z_data = np.random.rand(48, 48)

        # Update the image view with the new data
        self.image_view.setImage(z_data.T, autoLevels=True)

if __name__ == '__main__':
    # Create the PyQt application
    app = QtWidgets.QApplication(sys.argv)
    ex = RandomDataApp()
    sys.exit(app.exec_())
