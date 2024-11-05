# Copyright (C) 2024 Indoc Systems
#
# Contact Indoc Systems for any questions regarding the use of this source code.

import time
from uuid import uuid4

import jwt
from kivy.app import App
from kivy.core.window import Window
from kivy.graphics import Color
from kivy.graphics import Line
from kivy.graphics import Rectangle
from kivy.properties import ListProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput

from app.configs.app_config import AppConfig
from app.configs.config import ConfigClass
from app.configs.user_config import UserConfig
from app.services.clients.base_auth_client import BaseAuthClient
from app.services.clients.base_client import BaseClient
from app.services.user_authentication.user_login_logout import user_device_id_login


class HoverButton(Button):
    # Default background color
    default_color = ListProperty([1, 1, 1, 1])  # White
    hover_color = ListProperty([0.95, 0.95, 0.95, 1])  # Light grey
    pressed_color = ListProperty([0.83, 0.83, 0.83, 1])  # Darker grey

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.background_normal = ''  # Remove default background
        self.background_color = self.default_color
        self.bind(on_enter=self.on_hover, on_leave=self.on_unhover, on_press=self.on_press, on_release=self.on_unhover)
        self.size_hint = (None, None)
        self.width = 150  # Set specific width
        self.height = 50

    def on_hover(self, *args):
        self.background_color = self.hover_color

    def on_unhover(self, *args):
        self.background_color = self.default_color

    def on_press(self, *args):
        self.background_color = self.pressed_color


class TableCell(Label):
    def __init__(self, text='', is_header=False, is_selected=False, **kwargs):
        super().__init__(text=text, **kwargs)
        self.color = (0, 0, 0, 1)
        with self.canvas.before:
            # Set cell background color
            Color(*([0.95, 0.95, 0.95, 1] if is_header else [1, 1, 1, 1]))  # Light grey for header, white for cells
            # make text black
            self.rect = Rectangle(size=self.size, pos=self.pos)

        # Bind cell to update color on resize and add selection effect
        self.bind(size=self.update_rect, pos=self.update_rect)
        self.is_selected = is_selected

    def update_rect(self, *args):
        self.rect.size = self.size
        self.rect.pos = self.pos

    def select(self):
        with self.canvas.before:
            Color(0.3, 0.75, 0.3, 1)  # Green background for selected cells
            self.rect = Rectangle(size=self.size, pos=self.pos)


class MyApp(App):
    device_login = user_device_id_login()

    def build(self):
        self.title = 'Pilot CLI'
        Window.clearcolor = (0.0588, 0.2353, 0.2980, 1)

        self.layout = BoxLayout(orientation='vertical', padding=0, spacing=10)

        img = Image(source='/home/color/indoc/pilot/cli/app/gui/assets/indoc.png')
        button = HoverButton(text='Login', font_size=24, size_hint=(1, 0.2), pos_hint={'center_x': 0.5})
        button.bind(on_press=self.login)  # Bind button to click event

        # Add widgets to the layout
        self.layout.add_widget(img)
        self.layout.add_widget(button)

        return self.layout

    # Define button click event
    def login(self, instance):
        self.clear_window()

        url_entry = TextInput(
            text=self.device_login['verification_uri_complete'],
            readonly=True,
            font_size=20,
            size_hint=(None, None),
            width=1500,
            multiline=False,
            background_color=(1, 1, 1, 1),
            foreground_color=(0, 0, 1, 1),
            padding=[5, 10],
        )

        button = HoverButton(text='Next', font_size=24, size_hint=(1, 0.2), pos_hint={'center_x': 0.5})
        button.bind(on_press=self.check_login)

        self.layout.add_widget(url_entry)
        self.layout.add_widget(button)

    def check_login(self, instance):
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

        self.clear_window()
        project_list = response.json().get('result', [])
        scroll_view = ScrollView(size_hint=(1, None), size=(400, 500))
        table_layout = GridLayout(cols=2, size_hint_y=None, spacing=5, padding=5)
        table_layout.bind(minimum_height=table_layout.setter('height'))
        headers = ['Name', 'Code']
        for header in headers:
            cell = TableCell(text=header, is_header=True, bold=True, size_hint_y=None, height=40)
            table_layout.add_widget(cell)

            with cell.canvas.before:
                Color(0, 0, 0, 1)  # Black border color
                Line(rectangle=(cell.x, cell.y, cell.width, cell.height), width=1.2)

        for row in project_list:
            name = TableCell(text=row['name'], size_hint_y=None, height=30)
            with name.canvas.before:
                Color(0, 0, 0, 1)
                Line(rectangle=(name.x, name.y, name.width, name.height), width=1.2)
            table_layout.add_widget(name)

            code = TableCell(text=row['code'], size_hint_y=None, height=30)
            with code.canvas.before:
                Color(0, 0, 0, 1)
                Line(rectangle=(code.x, code.y, code.width, code.height), width=1.2)
            table_layout.add_widget(code)

        scroll_view.add_widget(table_layout)
        self.layout.add_widget(scroll_view)

    def clear_window(self):
        self.layout.clear_widgets()


# Run the application
if __name__ == '__main__':
    MyApp().run()
