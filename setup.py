"""
kael
"""
from setuptools import setup

setup(
    name='kael',
    version="0.0.3",
    url='https://github.com/360skyeye',
    license='Apache-2.0',
    author='360skyeye',
    author_email='liqiongxiang@b.360.cn',
    description='A micro service framework based on MQ',
    long_description=__doc__,
    packages=['kael'],
    include_package_data=True,
    zip_safe=False,
    platforms='any',
    install_requires=[
        'gevent>=1.1.2',
        'msgpack-python>=0.4.8',
        'pika>=0.10.0',
        'PyYAML>=3.12',
        'termcolor>=1.1.0',
    ],
    extras_require={},
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ],
    entry_points='''
    '''
)
