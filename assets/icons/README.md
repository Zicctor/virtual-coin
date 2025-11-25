# Icon Resources

Place your icon files here:

- `app_icon.png` - Main application window icon (256x256 recommended)
- `google_icon.png` - Google sign-in button icon (48x48)
- `bitcoin_icon.png` - Bitcoin/crypto logo (48x48)

## Where to Download Icons:

### Google Icon
- https://img.icons8.com/color/48/google-logo.png
- Right-click → Save As → `google_icon.png`

### Bitcoin Icon  
- https://img.icons8.com/color/48/bitcoin--v1.png
- Right-click → Save As → `bitcoin_icon.png`

### App Icon (Crypto)
- https://img.icons8.com/fluency/96/bitcoin.png
- Right-click → Save As → `app_icon.png`

## Quick Download (PowerShell):

```powershell
# Run from pyqt_crypto_app/assets/icons directory
Invoke-WebRequest -Uri "https://img.icons8.com/color/48/google-logo.png" -OutFile "google_icon.png"
Invoke-WebRequest -Uri "https://img.icons8.com/color/48/bitcoin--v1.png" -OutFile "bitcoin_icon.png"
Invoke-WebRequest -Uri "https://img.icons8.com/fluency/96/bitcoin.png" -OutFile "app_icon.png"
```

All icons are free from Icons8 (attribution appreciated but not required for personal use).
