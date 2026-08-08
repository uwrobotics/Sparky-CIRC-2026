import os
from glob import glob

from setuptools import setup

package_name = 'gimbal_teleop'

setup(
    name=package_name,
    version='1.0.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob('launch/*.py')),
        (os.path.join('share', package_name, 'config'), glob('config/*.yaml')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='UWRobotics Team',
    maintainer_email='uwaterloorobotics@gmail.com',
    description='D-pad teleoperation of the SIYI gimbal',
    license='Apache License 2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'gimbal_joy_node = gimbal_teleop.gimbal_joy_node:main',
        ],
    },
)
