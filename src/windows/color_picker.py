"""
 @file
 @brief A modal Qt color picker dialog launcher, which works in Wayland
 @author Jonathan Thomas <jonathan@openshot.org>

 @section LICENSE

 Copyright (c) 2008-2024 OpenShot Studios, LLC
 (http://www.openshotstudios.com). This file is part of
 OpenShot Video Editor (http://www.openshot.org), an open-source project
 dedicated to delivering high quality video editing and animation solutions
 to the world.

 OpenShot Video Editor is free software: you can redistribute it and/or modify
 it under the terms of the GNU General Public License as published by
 the Free Software Foundation, either version 3 of the License, or
 (at your option) any later version.

 OpenShot Video Editor is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 GNU General Public License for more details.

 You should have received a copy of the GNU General Public License
 along with OpenShot Library.  If not, see <http://www.gnu.org/licenses/>.
 """

from PyQt5.QtWidgets import QColorDialog, QPushButton, QDialog
from PyQt5.QtGui import QColor, QPainter, QPen, QCursor
from PyQt5.QtCore import Qt
from classes.logger import log
from classes.app import get_app


class ColorPicker(QColorDialog):
    def __init__(self, initial_color, parent=None, title=None, callback=None, *args, **kwargs):
        super().__init__(initial_color, parent, *args, **kwargs)
        self.parent_window = parent
        self.callback = callback
        self.picked_pixmap = None

        if title:
            self.setWindowTitle(title)

        self.setOption(QColorDialog.DontUseNativeDialog)
        self.colorSelected.connect(self.on_color_selected)

        # Override the "Pick Screen Color" button signal
        self._override_pick_screen_color()

        # Automatically open the dialog
        self.open()

    def _override_pick_screen_color(self):
        # Get first pushbutton (color picker)
        color_picker_button = self.findChildren(QPushButton)[0]
        log.debug(f"Color picker button text: {color_picker_button.text()}")

        # Connect to button signals
        color_picker_button.clicked.disconnect()
        color_picker_button.clicked.connect(self.start_color_picking)
        log.debug("Overridden the 'Pick Screen Color' button action")

    def start_color_picking(self):
        if self.parent_window:
            self.picked_pixmap = get_app().window.grab()
            self._show_picking_dialog()
        else:
            log.error("No parent window available for color picking")

    def _show_picking_dialog(self):
        dialog = PickingDialog(self.picked_pixmap, self)
        dialog.exec_()  # Show modal dialog
        self.raise_()

    def on_color_selected(self, color):
        log.debug(f"Color selected: {color.name()}")
        if self.callback:
            self.callback(color)

class PickingDialog(QDialog):
    def __init__(self, pixmap, color_picker, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.pixmap = pixmap
        self.device_pixel_ratio = pixmap.devicePixelRatio()
        self.color_picker = color_picker
        self.setWindowModality(Qt.WindowModal)
        self.setGeometry(get_app().window.geometry())
        self.setFixedSize(self.size())
        self.setCursor(Qt.CrossCursor)
        self.color_preview = QColor("#FFFFFF")
        self.setMouseTracking(True)

        # Get first pushbutton (color picker)
        color_picker_button = self.color_picker.findChildren(QPushButton)[0]
        self.setWindowTitle(f"OpenShot: {color_picker_button.text().replace('&', '')}")

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.drawPixmap(self.rect(), self.pixmap)
        # Draw color preview rectangle near the cursor
        if self.color_preview:
            pen = QPen(Qt.black, 2)
            painter.setPen(pen)
            painter.setBrush(self.color_preview)
            cursor_pos = self.mapFromGlobal(QCursor.pos())
            painter.drawRect(cursor_pos.x() + 15, cursor_pos.y() + 15, 50, 50)  # Rectangle offset from cursor
        painter.end()

    def mouseMoveEvent(self, event):
        if self.pixmap:
            image = self.pixmap.toImage()
            # Scale the coordinates for High DPI displays
            scaled_x = int(event.x() * self.device_pixel_ratio)
            scaled_y = int(event.y() * self.device_pixel_ratio)
            if 0 <= scaled_x < image.width() and 0 <= scaled_y < image.height():
                color = QColor(image.pixel(scaled_x, scaled_y))
                self.color_preview = color
                self.update()

    def mousePressEvent(self, event):
        if self.pixmap:
            image = self.pixmap.toImage()
            # Scale the coordinates for High DPI displays
            scaled_x = int(event.x() * self.device_pixel_ratio)
            scaled_y = int(event.y() * self.device_pixel_ratio)
            if 0 <= scaled_x < image.width() and 0 <= scaled_y < image.height():
                color = QColor(image.pixel(scaled_x, scaled_y))
                self.color_picker.setCurrentColor(color)
                log.debug(f"Picked color: {color.name()}")
        self.accept()  # Close the dialog
