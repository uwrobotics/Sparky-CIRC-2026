from setuptools import setup
import os
from glob import glob

package_name = 'servo_control'

setup(
    name=package_name,
    version='0.0.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'config'), glob('config/*.yaml')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='UWRobotics Team',
    maintainer_email='uwaterloorobotics@gmail.com',
    description='PS4 d-pad controlled RC servo/ESC PWM node for the Sparky rover',
    license='Apache License 2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'servo_control_node = servo_control.servo_control_node:main',
        ],
    },
)
