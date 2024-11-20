import os
import PyInstaller.__main__

package_name = 'OTM Integration Application - Admin Panel (Test)'

PyInstaller.__main__.run([
    '--name=%s' % package_name,
    '--onefile',
    # '--icon=%s' % os.path.join('../images', 'icon.ico'),
    os.path.join('AdminPanel.py'),
])
