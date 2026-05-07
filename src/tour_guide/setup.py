from setuptools import find_packages, setup
from glob import glob

package_name = 'tour_guide'

setup(
    name=package_name,
    version='0.1.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/launch', glob('launch/*.py')),
        ('share/' + package_name + '/worlds', glob('worlds/*')),
        ('share/' + package_name + '/maps', glob('maps/*')),
        ('share/' + package_name + '/landmarks', glob('landmarks/*.yaml')),
        ('share/' + package_name + '/models/aruco_marker_0', ['models/aruco_marker_0/model.config', 'models/aruco_marker_0/model.sdf']),
        ('share/' + package_name + '/models/aruco_marker_1', ['models/aruco_marker_1/model.config', 'models/aruco_marker_1/model.sdf']),
        ('share/' + package_name + '/models/aruco_marker_2', ['models/aruco_marker_2/model.config', 'models/aruco_marker_2/model.sdf']),
        ('share/' + package_name + '/models/aruco_marker_3', ['models/aruco_marker_3/model.config', 'models/aruco_marker_3/model.sdf']),
        ('share/' + package_name + '/models/aruco_marker_0/materials/textures', ['models/aruco_marker_0/materials/textures/marker_0.png']),
        ('share/' + package_name + '/models/aruco_marker_1/materials/textures', ['models/aruco_marker_1/materials/textures/marker_1.png']),
        ('share/' + package_name + '/models/aruco_marker_2/materials/textures', ['models/aruco_marker_2/materials/textures/marker_2.png']),
        ('share/' + package_name + '/models/aruco_marker_3/materials/textures', ['models/aruco_marker_3/materials/textures/marker_3.png']),
    ],
    install_requires=['setuptools', 'PyYAML'],
    zip_safe=True,
    maintainer='Donovan Semenuk',
    maintainer_email='donovansemenuk@ou.edu',
    description='TurtleBot4 autonomous tour guide using Nav2 and classroom landmarks.',
    license='MIT',
    extras_require={'test': ['pytest']},
    entry_points={
        'console_scripts': [
            'nav_node = tour_guide.navnode:main',
            'landmark_mapper = tour_guide.landmark_mapper:main',
            'known_stop_recorder = tour_guide.known_stop_recorder:main',
            'sim_aruco_detector = tour_guide.sim_aruco_detector:main',
        ],
    },
)
