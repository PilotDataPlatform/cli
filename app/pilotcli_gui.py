# Copyright (C) 2024 Indoc Systems
#
# Contact Indoc Systems for any questions regarding the use of this source code.

import sys

from PyQt5.QtWidgets import QApplication
from PyQt5.QtWidgets import QLabel
from PyQt5.QtWidgets import QMainWindow


# Create a class for the main window
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # Set window properties
        self.setWindowTitle('My First PyQt5 Window')
        self.setGeometry(300, 300, 400, 300)

        # Add a simple label widget
        label = QLabel('Hello, PyQt5!', self)
        label.setGeometry(150, 130, 100, 30)


app = QApplication(sys.argv)

main_window = MainWindow()
main_window.show()

sys.exit(app.exec_())
