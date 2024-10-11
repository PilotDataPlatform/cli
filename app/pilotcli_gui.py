# Copyright (C) 2022-2024 Indoc Systems
#
# Contact Indoc Systems for any questions regarding the use of this source code.

import tkinter as tk

from PIL import Image
from PIL import ImageTk

from app.services.user_authentication.user_login_logout import user_device_id_login
from app.services.user_authentication.user_login_logout import validate_user_device_login

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


def clear_window():
    # Loop over all widgets in the window and destroy them
    for widget in window.winfo_children():
        widget.destroy()


def on_button_click():
    clear_window()

    device_login = user_device_id_login()
    # url_label.pack()

    url_entry = tk.Entry(window, width=100, fg='blue', justify='center')
    url_entry.insert(0, device_login['verification_uri_complete'])  # Insert the URL into the Entry widget
    url_entry.config(state='readonly')  # Make the Entry read-only so users can copy but not edit
    url_entry.pack(pady=10)

    # force update
    window.update()

    validate_user_device_login(device_login['device_code'], device_login['expires'], device_login['interval'])


button = tk.Button(window, text='Login', command=on_button_click, bg='white', fg='blue')
button.pack(pady=20)


window.mainloop()
