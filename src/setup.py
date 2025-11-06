from setuptools import setup

setup(
    name='queuectl',
    version='1.0',
    py_modules=['queuectl'],
    install_requires=['click'],
    entry_points='''
        [console_scripts]
        queuectl=queuectl:cli
    ''',
)
