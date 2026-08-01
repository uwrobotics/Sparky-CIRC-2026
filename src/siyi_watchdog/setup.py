from setuptools import setup

package_name = 'siyi_watchdog'

setup(
    name=package_name,
    version='1.0.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='UWRobotics Team',
    maintainer_email='uwaterloorobotics@gmail.com',
    description='Restarts siyi_camera_node when the RTSP stream stalls',
    license='Apache License 2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'camera_watchdog = siyi_watchdog.camera_watchdog:main',
        ],
    },
)
