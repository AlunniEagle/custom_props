# Custom Props

[![QGIS](https://img.shields.io/badge/QGIS-3.x-green.svg)](https://qgis.org) 
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0) 
[![Issues](https://img.shields.io/github/issues/AlunniEagle/custom_props)](https://github.com/AlunniEagle/custom_props/issues)
[![Stars](https://img.shields.io/github/stars/AlunniEagle/custom_props?style=social)](https://github.com/AlunniEagle/custom_props)

Custom Props is a **QGIS plugin** that allows you to **inspect, filter, add, update, and remove custom properties** (key–value pairs) associated with project layers.  
It is designed as a lightweight but powerful tool for **debugging, analysis, and plugin development**.

---

## ✨ Features

- 🔍 **Inspect all custom properties** of project layers in a clear tabular view  
- 📑 **Dynamic filtering** by text or by layer  
- ➕ **Add / update custom properties** with type validation (String, Int, Double, Bool, JSON, Null)  
- ❌ **Remove properties** safely with confirmation dialogs  
- 🔄 **Refresh automatically** when layers are added or removed from the project  
- 🧩 **Group/key parsing** (supports `group/key`, `group.key`, `group:key`, etc.)  
- 📋 **JSON validation and preview** when adding properties  
- ⚡ Clean UI with **sorting, alternating row colors, and tooltips**  
- Works both for **debugging** and for **managing custom metadata** in projects  

---

## 📦 Installation

There are two ways to install **Custom Props**:

### 1. From the official QGIS Plugin Repository (recommended)
1. Open QGIS.  
2. Go to **Plugins → Manage and Install Plugins…**.  
3. In the *All* tab, search for **Custom Props**.  
4. Click **Install Plugin**.  

The plugin will now be available in the toolbar and under the **Plugins** menu.

### 2. From source (for developers)
1. Download or clone this repository:
   ```bash
   git clone https://github.com/eagleprojects/custom-props.git
   ```
2. Copy the folder into your QGIS plugin directory:
   - **Linux:** `~/.local/share/QGIS/QGIS3/profiles/default/python/plugins/`
   - **Windows:** `%APPDATA%\QGIS\QGIS3\profiles\default\python\plugins\`
   - **macOS:** `~/Library/Application Support/QGIS/QGIS3/profiles/default/python/plugins/`
3. Restart QGIS and enable **Custom Props** from the *Plugins → Manage and Install Plugins…* menu.

---

## 🚀 How it works

When you open **Custom Props** from the QGIS toolbar or from *Plugins → Custom Props*, a panel will appear.  

The panel provides:
- A **table** listing all custom properties from all layers in the project  
- A **filter box** to dynamically search across all columns (group, key, value, type, layer)  
- A **layer combo box** to show only the properties of a specific layer or all layers together  
- Action buttons:
  - **Refresh**: reload all properties from the project  
  - **Add**: insert or update a property in the selected layer, with confirmation dialog  
  - **Remove**: delete a selected property, with confirmation dialog  

The table supports:
- **Sorting by any column** (e.g. Group, Key, Layer)  
- **Placeholder formatting** for empty or null values  
- **Type detection** (String, Int, Double, Bool, JSON, Null)  

This makes it simple to **explore hidden metadata**, test layer properties, and manage custom settings for plugins or projects.

---

## 🛠 Development

This plugin is built using:

- **QGIS Python API (PyQGIS)**
- **PyQt5** for UI components
- `.ui` files designed with **Qt Designer**
- Standard QGIS plugin structure (`metadata.txt`, resources, etc.)

---

## 📄 Example

Adding a property to a layer from Python console:  

```python
layer = iface.activeLayer()
layer.setCustomProperty("mygroup/mykey", {"a": 1, "b": 2})
print(layer.customProperty("mygroup/mykey"))
# Output: {'a': 1, 'b': 2}
```

The plugin UI will immediately display this new property.

## 🤝 Contributing

Contributions are welcome!  
If you find a bug or have a feature request, please open an [issue](https://github.com/AlunniEagle/custom_props/issues).

---

## 📜 License

This plugin is released under the **GNU General Public License v3 (GPLv3)**.  
You are free to use, modify and distribute it under the terms of this license.

---

## 🌍 Links

- [Repository](https://github.com/AlunniEagle/custom_props)  
- [Issue Tracker](https://github.com/AlunniEagle/custom_props/issues)  

---

*Developed with ❤️ by GIS Team – Eagleprojects.*
