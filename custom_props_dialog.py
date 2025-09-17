import os, re
from qgis.PyQt import uic
from qgis.PyQt import QtWidgets, QtCore
from qgis.core import QgsProject
from qgis.PyQt.QtGui import QBrush, QColor, QFont
import json


FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'custom_props_dialog_base.ui'))

class PropsTableModel(QtCore.QAbstractTableModel):
    HEADERS = ["Group", "Key", "Value", "Type", "Layer"]
    PLACEHOLDER_EMPTY = "null"
    PLACEHOLDER_NULL  = "null"

    def __init__(self, rows=None, parent=None):
        super().__init__(parent)
        self._rows = rows or []

    def set_rows(self, rows):
        self.beginResetModel()
        self._rows = rows
        self.endResetModel()

    def rowCount(self, parent=QtCore.QModelIndex()):
        return len(self._rows)

    def columnCount(self, parent=QtCore.QModelIndex()):
        return 5

    def headerData(self, section, orientation, role=QtCore.Qt.DisplayRole):
        if role != QtCore.Qt.DisplayRole:
            return None
        if orientation == QtCore.Qt.Horizontal:
            return self.HEADERS[section]
        return section + 1

    def data(self, index, role=QtCore.Qt.DisplayRole):
        if not index.isValid():
            return None

        r, c = index.row(), index.column()
        group, key, val, typ, layer_name, layer_id, full_key = self._rows[r]

        is_placeholder = False

        if c == 0:
            text = group or self.PLACEHOLDER_EMPTY
            is_placeholder = not bool(group)

        elif c == 1:
            text = key or self.PLACEHOLDER_EMPTY
            is_placeholder = not bool(key)

        elif c == 2:
            if val is None:
                text = self.PLACEHOLDER_NULL
                is_placeholder = True
            else:
                text = "true" if isinstance(val, bool) and val else \
                    "false" if isinstance(val, bool) else str(val)
                if isinstance(val, str) and text.strip() == "":
                    text = self.PLACEHOLDER_EMPTY
                    is_placeholder = True

        elif c == 3:
            text = typ

        elif c == 4:
            text = layer_name or self.PLACEHOLDER_EMPTY
            is_placeholder = not bool(layer_name)

        else:
            return None

        if role == QtCore.Qt.DisplayRole:
            return text

        if role == QtCore.Qt.UserRole:
            if c == 2:
                return val
            if c == 4:
                return layer_id

        if is_placeholder:
            if role == QtCore.Qt.ForegroundRole:
                return QBrush(QColor(31, 45, 61, 150))
            if role == QtCore.Qt.FontRole:
                f = QFont(); f.setItalic(True); return f
            if role == QtCore.Qt.ToolTipRole:
                return "Absent value"

        return None

    def sort(self, column, order):
        self.layoutAboutToBeChanged.emit()
        reverse = (order == QtCore.Qt.DescendingOrder)
        if column in (0, 1, 4):
            self._rows.sort(key=lambda r: (str(r[column]) or "").lower(), reverse=reverse)
        elif column == 2:
            self._rows.sort(key=lambda r: str(r[2]).lower(), reverse=reverse)
        else:
            self._rows.sort(key=lambda r: r[3], reverse=reverse)
        self.layoutChanged.emit()

class PropsFilterProxy(QtCore.QSortFilterProxyModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._pattern = ""
        self._layer_id = None

    def setLayerFilter(self, layer_id):
        self._layer_id = layer_id
        self.invalidateFilter()

    def setFilterString(self, text: str):
        self._pattern = text.strip().lower()
        self.invalidateFilter()

    def filterAcceptsRow(self, source_row, source_parent):
        sm = self.sourceModel()

        if self._layer_id:
            idx_layer = sm.index(source_row, 4, source_parent)
            row_layer_id = sm.data(idx_layer, QtCore.Qt.UserRole)
            if row_layer_id != self._layer_id:
                return False

        if not self._pattern:
            return True
        for col in range(sm.columnCount()):
            txt = sm.data(sm.index(source_row, col, source_parent), QtCore.Qt.DisplayRole)
            if txt is not None and self._pattern in str(txt).lower():
                return True
        return False

class CustomPropsDialog(QtWidgets.QDialog, FORM_CLASS):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)

        self._model = PropsTableModel()
        self._proxy = PropsFilterProxy(self)
        self._proxy.setSourceModel(self._model)
        self._proxy.setDynamicSortFilter(True)

        self.tblProps.setModel(self._proxy)
        self.tblProps.setSortingEnabled(True)
        self.tblProps.horizontalHeader().setStretchLastSection(True)
        self.tblProps.verticalHeader().setVisible(False)
        self.tblProps.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.tblProps.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)

        self.tblProps.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.tblProps.setFocusPolicy(QtCore.Qt.NoFocus)

        self.tblProps.setAlternatingRowColors(True)

        self.tblProps.sortByColumn(0, QtCore.Qt.AscendingOrder)

        self.txtFilter.textChanged.connect(self._proxy.setFilterString)

        self._setup_layers_combo()
        self._reload_rows()
        self._proxy.setLayerFilter(self.cmbLayer.currentData())
        self.tblProps.sortByColumn(0, QtCore.Qt.AscendingOrder)

        self.btnRemove.clicked.connect(self._on_remove_clicked)
        self.btnRefresh.clicked.connect(self._on_refresh_clicked)
        self.btnAdd.clicked.connect(self._on_add_clicked)

        self.btnAdd.setEnabled(False)
        self.cmbLayer.currentIndexChanged.connect(self._update_add_enabled)
        self.txtKey.textChanged.connect(self._update_add_enabled)
        self.cmbType.currentIndexChanged.connect(self._update_add_enabled)
        self.txtValue.textChanged.connect(self._update_add_enabled)

    def set_rows(self, rows):
        self._model.set_rows(rows)

    def _setup_layers_combo(self):
        self._populate_layers_combo()
        self.cmbLayer.currentIndexChanged.connect(self._on_layer_changed)

        prj = QgsProject.instance()
        prj.layersAdded.connect(lambda _ls: self._on_layers_changed())
        prj.layerRemoved.connect(lambda _id: self._on_layers_changed())
        prj.cleared.connect(self._on_layers_changed)

    def _populate_layers_combo(self):
        self.cmbLayer.blockSignals(True)
        current = self.cmbLayer.currentData() if self.cmbLayer.count() else None
        self.cmbLayer.clear()
        self.cmbLayer.addItem("All Layers", None)
        for lyr in QgsProject.instance().mapLayers().values():
            self.cmbLayer.addItem(lyr.name(), lyr.id())
        if current is not None:
            idx = self.cmbLayer.findData(current)
            if idx != -1:
                self.cmbLayer.setCurrentIndex(idx)
        self.cmbLayer.blockSignals(False)

    def _on_layers_changed(self):
        self._populate_layers_combo()
        self._reload_rows()
        self._proxy.setLayerFilter(self.cmbLayer.currentData())

    def _on_layer_changed(self, _index):
        self._proxy.setLayerFilter(self.cmbLayer.currentData())

    def _collect_rows_all_layers(self):
        rows = []
        for lyr in QgsProject.instance().mapLayers().values():
            layer_name, layer_id = lyr.name(), lyr.id()
            for k in lyr.customPropertyKeys():
                v = lyr.customProperty(k)
                group, short_key = self.split_group_key(k)
                rows.append((group, short_key, v, self.type_str(v), layer_name, layer_id, k))
        rows.sort(key=lambda r: ((r[0] or "").lower(), (str(r[1]) or "").lower(), (r[4] or "").lower()))
        return rows

    def _reload_rows(self):
        self._model.set_rows(self._collect_rows_all_layers())

    def _on_remove_clicked(self):
        def info_box(title: str, text: str, icon=QtWidgets.QMessageBox.Information):
            m = QtWidgets.QMessageBox(self)
            m.setWindowTitle(title)
            m.setIcon(icon)
            m.setText(text)
            m.setTextFormat(QtCore.Qt.RichText if ("<" in text and ">" in text) else QtCore.Qt.PlainText)
            m.setStyleSheet("""
                QLabel { font-size: 10pt; }
                QPushButton { min-width: 86px; padding: 3px 8px; font-size: 8pt; }
            """)
            m.addButton("OK", QtWidgets.QMessageBox.AcceptRole)
            m.exec_()

        def confirm_box(title: str, html_text: str) -> bool:
            m = QtWidgets.QMessageBox(self)
            m.setWindowTitle(title)
            m.setIcon(QtWidgets.QMessageBox.Question)
            m.setTextFormat(QtCore.Qt.RichText)
            m.setText(html_text)
            m.setStyleSheet("""
                QLabel { font-size: 10pt; }
                QPushButton { min-width: 86px; padding: 3px 8px; font-size: 8pt; }
            """)
            ok_btn = m.addButton("OK", QtWidgets.QMessageBox.AcceptRole)
            cancel_btn = m.addButton("Cancel", QtWidgets.QMessageBox.RejectRole)
            m.setDefaultButton(ok_btn)
            m.setEscapeButton(cancel_btn)
            m.exec_()
            return m.clickedButton() is ok_btn

        sel = self.tblProps.selectionModel().selectedRows()
        if not sel:
            info_box("Nothing selected", "Please select a property in the table to remove.")
            return

        proxy_index = sel[0]
        src_index = self._proxy.mapToSource(proxy_index)

        try:
            group, key, val, typ, layer_name, layer_id, full_key = self._model._rows[src_index.row()]
        except Exception:
            info_box("Unexpected error", "Could not read the selected row.", icon=QtWidgets.QMessageBox.Warning)
            return

        val_str = "null" if val is None else str(val)
        if len(val_str) > 400:
            val_str = val_str[:400] + "…"

        summary = (
            "You are about to <b>remove</b> a custom property.<br><br>"
            f"<b>Layer:</b> {layer_name}<br>"
            f"<b>Group:</b> {group or '—'}<br>"
            f"<b>Key:</b> {key or '—'}<br>"
            f"<b>Full key:</b> <code>{full_key}</code><br>"
            f"<b>Type:</b> {typ}<br>"
            f"<b>Value:</b> {val_str}"
        )
        if not confirm_box("Confirm removal", summary):
            return

        lyr = QgsProject.instance().mapLayer(layer_id)
        if not lyr:
            info_box("Layer not found",
                    "The selected layer is no longer available in the project.",
                    icon=QtWidgets.QMessageBox.Warning)
            return

        try:
            lyr.removeCustomProperty(full_key)
        except Exception as e:
            info_box("Removal failed",
                    f"Couldn't remove the property:<br><br><code>{full_key}</code><br><br>"
                    f"<b>Error:</b> {e}",
                    icon=QtWidgets.QMessageBox.Critical)
            return

        current_layer_id = self.cmbLayer.currentData()
        self._reload_rows()
        self._proxy.setLayerFilter(current_layer_id)

        info_box("Removed", "The custom property has been removed.")

    def _msg_info(self, title: str, text: str, icon=QtWidgets.QMessageBox.Information):
        m = QtWidgets.QMessageBox(self)
        m.setWindowTitle(title)
        m.setIcon(icon)
        m.setText(text)
        m.setTextFormat(QtCore.Qt.RichText if ("<" in text and ">" in text) else QtCore.Qt.PlainText)
        m.setStyleSheet("""
            QLabel { font-size: 10pt; }
            QPushButton { min-width: 86px; padding: 3px 8px; font-size: 8pt; }
        """)
        m.addButton("OK", QtWidgets.QMessageBox.AcceptRole)
        m.exec_()

    def _msg_confirm(self, title: str, html_text: str) -> bool:
        m = QtWidgets.QMessageBox(self)
        m.setWindowTitle(title)
        m.setIcon(QtWidgets.QMessageBox.Question)
        m.setTextFormat(QtCore.Qt.RichText)
        m.setText(html_text)
        m.setStyleSheet("""
            QLabel { font-size: 10pt; }
            QPushButton { min-width: 86px; padding: 3px 8px; font-size: 8pt; }
        """)
        ok_btn = m.addButton("OK", QtWidgets.QMessageBox.AcceptRole)
        cancel_btn = m.addButton("Cancel", QtWidgets.QMessageBox.RejectRole)
        m.setDefaultButton(ok_btn)
        m.setEscapeButton(cancel_btn)
        m.exec_()
        return m.clickedButton() is ok_btn

    def _on_refresh_clicked(self):
        current_layer_id = self.cmbLayer.currentData()
        self._reload_rows()
        self._proxy.setLayerFilter(current_layer_id)

    def _parse_value(self, type_name: str, text: str):
        t = (type_name or "").strip().lower()
        s = (text or "").strip()

        if t == "string":
            return True, (text if text is not None else ""), None

        if t == "integer":
            try:
                if s.lower().startswith(("0x", "0o", "0b")):
                    return False, None, "Use base-10 integer."
                v = int(s)
                return True, v, None
            except Exception:
                return False, None, "Enter a valid integer (e.g. 42)."

        if t == "float":
            try:
                v = float((text or "").replace(",", "."))
                return True, v, None
            except Exception:
                return False, None, "Enter a valid number (e.g. 3.14)."

        if t == "bool":
            sl = (text or "").strip().lower()
            if sl in ("true", "false"):
                return True, (sl == "true"), None
            return False, None, "Type boolean requires 'true' or 'false'."

        if t == "json":
            try:
                v = json.loads(text or "")
                if not isinstance(v, (dict, list)):
                    return False, None, "JSON must be an object or array."
                return True, v, None
            except Exception as e:
                return False, None, f"Invalid JSON: {e}"

        return True, (text if text is not None else ""), None
    
    def _update_add_enabled(self):
        layer_ok = self.cmbLayer.currentData() is not None
        key_ok = bool((self.txtKey.text() or "").strip())
        type_name = self.cmbType.currentText()
        ok_val, _parsed, _err = self._parse_value(type_name, self.txtValue.text())

        self.btnAdd.setEnabled(layer_ok and key_ok and ok_val)

    def _on_add_clicked(self):
        if self.cmbLayer.currentData() is None:
            self._msg_info("Missing layer", "Select a target layer.", icon=QtWidgets.QMessageBox.Warning)
            return

        key_txt = (self.txtKey.text() or "").strip()
        type_name = self.cmbType.currentText()
        ok_val, value, err = self._parse_value(type_name, self.txtValue.text())
        if not key_txt or not ok_val:
            self._update_add_enabled()
            return

        full_key = key_txt
        group, short_key = self.split_group_key(full_key)

        layer_id = self.cmbLayer.currentData()
        lyr = QgsProject.instance().mapLayer(layer_id)
        if not lyr:
            self._msg_info("Layer not found",
                        "The selected layer is no longer available in the project.",
                        icon=QtWidgets.QMessageBox.Warning)
            return

        val_preview = "null" if value is None else str(value)
        if len(val_preview) > 400:
            val_preview = val_preview[:400] + "…"

        html = (
            "You are about to <b>add/update</b> a custom property.<br><br>"
            f"<b>Layer:</b> {lyr.name()}<br>"
            f"<b>Group:</b> {group or '—'}<br>"
            f"<b>Key:</b> {short_key or full_key}<br>"
            f"<b>Full key:</b> <code>{full_key}</code><br>"
            f"<b>Type:</b> {type_name}<br>"
            f"<b>Value:</b> {val_preview}"
        )
        if not self._msg_confirm("Confirm add/update", html):
            return

        try:
            lyr.setCustomProperty(full_key, value)
        except Exception as e:
            self._msg_info("Write failed",
                        f"Couldn't set the property:<br><br><code>{full_key}</code><br><br>"
                        f"<b>Error:</b> {e}",
                        icon=QtWidgets.QMessageBox.Critical)
            return

        current_layer_id = self.cmbLayer.currentData()
        self._reload_rows()
        self._proxy.setLayerFilter(current_layer_id)

        self._msg_info("Done", "The custom property has been saved.")


    @staticmethod
    def split_group_key(key: str):
        if not isinstance(key, str):
            key = str(key)
        m = re.match(r'^([A-Za-z0-9\-]+)[\/_.:]+(.+)$', key)
        if m:
            return m.group(1), m.group(2)
        return "", key

    @staticmethod
    def type_str(value):
        if value is None: return "Null"
        if isinstance(value, bool): return "Bool"
        if isinstance(value, int) and not isinstance(value, bool): return "Int"
        if isinstance(value, float): return "Double"
        if isinstance(value, (dict, list)): return "JSON"
        return "String"

