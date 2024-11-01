# Copyright (C) 2022-2024 Indoc Systems
#
# Contact Indoc Systems for any questions regarding the use of this source code.

import time
import tkinter as tk
from tkinter import ttk
from uuid import uuid4

import jwt
from PIL import Image
from PIL import ImageTk

from app.configs.app_config import AppConfig
from app.configs.config import ConfigClass
from app.configs.user_config import UserConfig
from app.services.clients.base_auth_client import BaseAuthClient
from app.services.clients.base_client import BaseClient
from app.services.user_authentication.user_login_logout import user_device_id_login

window = tk.Tk()
window.title('Pilot CLI')
window.geometry('800x400')
window.resizable(False, False)

label = tk.Label(text='Python rocks!')

image = Image.open('/home/color/indoc/pilot/cli/app/gui/assets/indoc.png')
resized_image = image.resize(
    (image.width // 4, image.height // 4), Image.Resampling.LANCZOS
)  # Use LANCZOS for high-quality resizing
# Convert the resized image to a PhotoImage object
photo = ImageTk.PhotoImage(resized_image)

label = tk.Label(window, image=photo)
label.pack()
label.image = photo

device_login = user_device_id_login()


def clear_window():
    # Loop over all widgets in the window and destroy them
    for widget in window.winfo_children():
        widget.destroy()


def check_login():
    http_client = BaseClient(AppConfig.Connections.url_keycloak)
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    data = {
        'device_code': device_login['device_code'],
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

    clear_window()
    project_list = response.json().get('result', [])
    table = ttk.Treeview(window)
    table['columns'] = ['name', 'code']
    for column in ['name', 'code']:
        table.heading(column, text=column)
        table.column(column, anchor='center')

    for row in project_list:
        row_val = [row['name'], row['code']]
        table.insert('', 'end', values=row_val)

    table.pack(pady=20)


def on_button_click():
    clear_window()

    url_entry = tk.Entry(window, width=100, fg='blue', justify='center')
    url_entry.insert(0, device_login['verification_uri_complete'])  # Insert the URL into the Entry widget
    url_entry.config(state='readonly')  # Make the Entry read-only so users can copy but not edit
    url_entry.pack(pady=10)
    button = tk.Button(window, text='Next', command=check_login, bg='white', fg='blue')
    button.pack(pady=20)

    # force update
    window.update()


button = tk.Button(window, text='Login', command=on_button_click, bg='white', fg='blue')
button.pack(pady=20)


window.mainloop()
