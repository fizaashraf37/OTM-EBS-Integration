import os
import PyInstaller.__main__

package_name = 'OTM Integration Application (Test)'

PyInstaller.__main__.run([
    '--name=%s' % package_name,
    '--onefile',
    # '--windowed',
    # '--add-binary=%s' % os.path.join('resource', 'path', '*.png'),
    # '--add-data=%s' % os.path.join('resource', 'path', '*.txt'),
    '--icon=%s' % os.path.join('../images', 'icon.ico'),
    os.path.join('OtmIntegration.py'),
])
