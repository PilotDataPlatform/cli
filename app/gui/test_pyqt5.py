# Copyright (C) 2024 Indoc Systems
#
# Contact Indoc Systems for any questions regarding the use of this source code.

import io
import sys
import time
from uuid import uuid4

import jwt
from PIL import Image
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QImage
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QApplication
from PyQt5.QtWidgets import QHeaderView
from PyQt5.QtWidgets import QLabel
from PyQt5.QtWidgets import QLineEdit
from PyQt5.QtWidgets import QMainWindow
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtWidgets import QSizePolicy
from PyQt5.QtWidgets import QTableWidget
from PyQt5.QtWidgets import QTableWidgetItem
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QWidget

from app.configs.app_config import AppConfig
from app.configs.config import ConfigClass
from app.configs.user_config import UserConfig
from app.services.clients.base_auth_client import BaseAuthClient
from app.services.clients.base_client import BaseClient
from app.services.user_authentication.user_login_logout import user_device_id_login

button_css = """
    QPushButton {
        background-color: white;
        border: 2px solid #CCCCCC;
        color: black;
        padding: 10px 24px;
        font-size: 16px;
        font-weight: bold;
        border-radius: 12px;
    }
    QPushButton:hover {
        background-color: #f2f2f2;
    }
    QPushButton:pressed {
        background-color: #D3D3D3;
    }
"""

line_edit_css = """
QLineEdit {
    padding: 8px;
    font-size: 16px;
    border: 2px solid #cccccc;
    border-radius: 8px;
    background-color: white;
}
"""

table_css = """
    QTableWidget {
        background-color: #ffffff;
        border: 1px solid #dcdcdc;
        gridline-color: #e0e0e0;
        font-size: 14px;
        border-radius: 8px;
    }
    QTableWidget::item {
        padding: 8px;
    }
    QTableWidget::item:selected {
        background-color: #4CAF50;
        color: black;
    }
    QHeaderView::section {
        background-color: #f5f5f5;
        color: #333333;
        padding: 6px;
        font-size: 14px;
        font-weight: bold;
        border: 1px solid #dcdcdc;
    }
    QTableCornerButton::section {
        background-color: #f5f5f5;
        border: 1px solid #dcdcdc;
    }
    QTableWidget::item:alternate {
        background-color: #f9f9f9;
    }
    QTableWidget::item:alternate:selected{
        background-color: #4CAF50;
        color: black;
    }
"""


class MainWindow(QMainWindow):

    device_login = user_device_id_login()

    def __init__(self):
        super().__init__()

        # Set window properties
        self.setWindowTitle('PILOT CLI GUI')
        self.setGeometry(600, 600, 800, 400)
        self.setStyleSheet('background-color: #0f3c4c;')

        # Load and resize the image with Pillow
        image = Image.open('/home/color/indoc/pilot/cli/app/gui/assets/indoc.png')
        resized_image = image.resize((image.width // 4, image.height // 4), Image.Resampling.LANCZOS)

        # Convert the Pillow image to a format compatible with PyQt (QImage)
        # Step 1: Convert Pillow image to bytes
        img_data = io.BytesIO()
        resized_image.save(img_data, format='PNG')
        img_data.seek(0)

        # Step 2: Create QImage from the byte data
        qt_image = QImage.fromData(img_data.read())

        # Step 3: Convert QImage to QPixmap
        pixmap = QPixmap.fromImage(qt_image)

        # Create a QLabel to display the image
        label = QLabel(self)
        label.setPixmap(pixmap)
        label.setAlignment(Qt.AlignCenter)
        # add button
        button = QPushButton('Login')
        button.clicked.connect(self.on_button_click)
        button.setStyleSheet(button_css)

        self.layout = QVBoxLayout()
        self.layout.addWidget(label, alignment=Qt.AlignCenter)
        self.layout.addWidget(button, alignment=Qt.AlignCenter)

        # Set the layout in a central widget
        central_widget = QWidget()
        central_widget.setLayout(self.layout)
        self.setCentralWidget(central_widget)

    def on_button_click(self):
        self.reset_window()

        # Create a QLineEdit (equivalent to tkinter Entry)
        url_entry = QLineEdit(self)
        url_entry.setText(self.device_login['verification_uri_complete'])
        url_entry.setReadOnly(True)
        url_entry.setAlignment(Qt.AlignCenter)
        url_entry.setStyleSheet('color: blue;')
        url_entry.setStyleSheet(line_edit_css)
        self.layout.addWidget(url_entry)

        # Create a QPushButton (equivalent to tkinter Button)
        button = QPushButton('Next')
        button.setStyleSheet('background-color: white; color: blue;')
        button.clicked.connect(self.check_login)
        button.setStyleSheet(button_css)
        self.layout.addWidget(button, alignment=Qt.AlignCenter)

        # Set the layout in the central widget
        central_widget = QWidget()
        central_widget.setLayout(self.layout)
        self.setCentralWidget(central_widget)

    def check_login(self):
        http_client = BaseClient(AppConfig.Connections.url_keycloak)
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        data = {
            'device_code': self.device_login['device_code'],
            'client_id': ConfigClass.keycloak_device_client_id,
            'grant_type': 'urn:ietf:params:oauth:grant-type:device_code',
        }
        resp = http_client._post('token', data=data, headers=headers)

        resp_dict = resp.json()
        decode_token = jwt.decode(resp_dict['access_token'], options={'verify_signature': False}, algorithms=['RS256'])
        user_config = UserConfig()
        user_config.api_key = ''
        user_config.access_token = resp_dict['access_token']
        user_config.refresh_token = resp_dict['refresh_token']
        user_config.username = decode_token['preferred_username']
        user_config.last_active = str(int(time.time()))
        user_config.session_id = 'cli-' + str(uuid4())
        user_config.save()

        # call list projects
        http_client = BaseAuthClient(AppConfig.Connections.url_bff)
        http_client.endpoint = AppConfig.Connections.url_bff + '/v1'
        params = {'page': 0, 'page_size': 10, 'order': 'desc', 'order_by': 'created_at'}
        response = http_client._get('projects', params=params)
        # print(response.json())

        self.reset_window()
        project_list = response.json().get('result', [])
        # Create a QTableWidget (equivalent to Treeview in tkinter)
        table = QTableWidget()
        table.setRowCount(len(project_list))  # Set number of rows
        table.setColumnCount(2)  # Set number of columns
        table.setStyleSheet('background-color: white;')
        table.setHorizontalHeaderLabels(['name', 'code'])  # Set column headers

        # Populate the table with data from project_list
        for row_idx, row_data in enumerate(project_list):
            # Create table items for each column
            name_item = QTableWidgetItem(row_data['name'])
            code_item = QTableWidgetItem(row_data['code'])

            # Align text to center (optional)
            name_item.setTextAlignment(Qt.AlignCenter)
            code_item.setTextAlignment(Qt.AlignCenter)

            # Insert data into the table
            table.setItem(row_idx, 0, name_item)
            table.setItem(row_idx, 1, code_item)

        table.setStyleSheet(table_css)
        table.setAlternatingRowColors(True)
        table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        table.resizeColumnsToContents()
        table.resizeRowsToContents()
        table.horizontalHeader().setStretchLastSection(True)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        for i in range(3):
            table.setColumnWidth(i, 200)

        # Add the table to the layout
        central_widget = QWidget()
        self.layout.addWidget(table)
        central_widget.setLayout(self.layout)
        self.setCentralWidget(central_widget)

    def reset_window(self):
        # Clear the layout by removing all widgets
        for i in reversed(range(self.layout.count())):
            widget = self.layout.itemAt(i).widget()
            if widget is not None:
                widget.deleteLater()  # Delete each widget


app = QApplication(sys.argv)

main_window = MainWindow()
main_window.show()

sys.exit(app.exec_())
