from glob import glob
import os

from setuptools import find_packages, setup

package_name = 'tour_guide'


def optional_files(pattern):
    return glob(pattern)


data_files = [
    ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
    ('share/' + package_name, ['package.xml']),
    ('share/' + package_name + '/launch', optional_files('launch/*.py')),
    ('share/' + package_name + '/worlds', optional_files('worlds/*')),
    ('share/' + package_name + '/maps', optional_files('maps/*')),
]

for model_dir in glob('models/*'):
    if os.path.isdir(model_dir):
        model_name = os.path.basename(model_dir)
        model_files = glob(os.path.join(model_dir, '*.sdf')) + glob(os.path.join(model_dir, '*.config'))
        if model_files:
            data_files.append(('share/' + package_name + '/models/' + model_name, model_files))

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=data_files,
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Donovan Semenuk',
    maintainer_email='donovansemenuk@ou.edu',
    description='TurtleBot 4 tour-guide package with ArUco and manual landmark registration.',
    license='MIT',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'nav_node = tour_guide.navnode:main',
        ],
    },
)
