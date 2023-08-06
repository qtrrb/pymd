from setuptools import setup, find_packages

setup(
    name='pymd',
    version='0.1',
    packages=find_packages(),
    install_requires=[
        'matplotlib'
    ],
    entry_points={
        'console_scripts': [
            'pymd=pymd.__main__:main'
        ]
    }
)

