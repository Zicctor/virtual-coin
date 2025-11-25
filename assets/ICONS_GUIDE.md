# How to Add Icons to Your PyQt6 Crypto Trading App

## Overview
There are several ways to add icons in PyQt6:
1. **PNG/SVG files** - Download and store locally
2. **Icon fonts** - Use icon fonts like Font Awesome
3. **Base64 embedded** - Embed small icons directly in code
4. **Qt Resources** - Compile icons into a resource file

## Method 1: Using PNG/SVG Files (Recommended for Beginners)

### Step 1: Download Icons

Download these icons and save them in `pyqt_crypto_app/assets/icons/`:

**App Icon (window icon):**
- Download from: https://icon-icons.com/icon/bitcoin-cryptocurrency-digital-currency/93774
- Save as: `app_icon.png` (256x256 or larger)

**Google Icon:**
- Download from: https://www.google.com/favicon.ico
- Or use: https://img.icons8.com/color/48/000000/google-logo.png
- Save as: `google_icon.png`

**Bitcoin Icon:**
- Download from: https://cryptologos.cc/bitcoin
- Save as: `bitcoin_icon.png`

### Step 2: Folder Structure
```
pyqt_crypto_app/
└── assets/
    └── icons/
        ├── app_icon.png      # Main window icon
        ├── google_icon.png   # For Google sign-in button
        ├── bitcoin_icon.png  # For crypto icon
        └── README.md
```

### Step 3: Update Code to Use Icons

See the updated `login_window.py` for implementation.

---

## Method 2: Using Icon Fonts (Font Awesome)

### Step 1: Install qtawesome
```powershell
pip install qtawesome
```

### Step 2: Use in Code
```python
import qtawesome as qta

# Create icons with Font Awesome
google_icon = qta.icon('fa5b.google', color='#4285F4')
bitcoin_icon = qta.icon('fa5b.bitcoin', color='#F0B90B')
```

---

## Method 3: Base64 Embedded Icons (No Files Needed)

For small icons, you can embed them directly in code:

```python
import base64
from PyQt6.QtGui import QPixmap, QIcon
from PyQt6.QtCore import QByteArray

# Google icon as base64 (simplified)
GOOGLE_ICON_BASE64 = "iVBORw0KGgoAAAANSUhEUgAA..."

def load_icon_from_base64(base64_string):
    pixmap = QPixmap()
    pixmap.loadFromData(QByteArray.fromBase64(base64_string.encode()))
    return QIcon(pixmap)
```

---

## Method 4: Qt Resource System (Professional)

### Step 1: Create resources.qrc
```xml
<!DOCTYPE RCC>
<RCC version="1.0">
  <qresource>
    <file>icons/app_icon.png</file>
    <file>icons/google_icon.png</file>
  </qresource>
</RCC>
```

### Step 2: Compile Resources
```powershell
pyrcc5 resources.qrc -o resources_rc.py
```

### Step 3: Use in Code
```python
import resources_rc  # Auto-generated file

icon = QIcon(":/icons/app_icon.png")
```

---

## Quick Start: Using Method 1

1. **Create icons folder:**
   ```powershell
   mkdir pyqt_crypto_app\assets\icons
   ```

2. **Download icons:**
   - Google: Save from https://img.icons8.com/color/48/google-logo.png
   - Bitcoin: Save from https://img.icons8.com/color/48/bitcoin--v1.png
   - Save both to `assets/icons/`

3. **Icons are already integrated** in the updated `login_window.py`!

---

## Free Icon Resources

- **Icons8**: https://icons8.com/ (free with attribution)
- **Flaticon**: https://www.flaticon.com/ (free/premium)
- **Font Awesome**: https://fontawesome.com/ (free icons)
- **Material Icons**: https://fonts.google.com/icons
- **Crypto Icons**: https://cryptologos.cc/

---

## Tips

✅ **Use PNG with transparency** for best results  
✅ **Size**: 48x48 or 256x256 for icons, 512x512 for app icon  
✅ **Format**: PNG > SVG > ICO  
✅ **Fallback**: Code checks if icon exists before loading  
✅ **High DPI**: Use @2x versions for retina displays  

## Common Issues

**Icon not showing:**
- Check file path is correct (use absolute path)
- Verify file exists with `os.path.exists()`
- Check file permissions
- Try different image format (PNG vs ICO)

**Blurry icons:**
- Use higher resolution images
- Enable high DPI scaling in main.py
