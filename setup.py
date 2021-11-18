from setuptools import setup

setup(name='c8ydm',
      version='0.2',
      description='Cumulocity Device Management Agent',
      author='Tobias Sommer, Stefan Witschel, Marco Stoffel, Murat Bayram',
      license='Apache 2.0',
      packages=['c8ydm',
            'c8ydm.agentmodules',
            'c8ydm.client',
            'c8ydm.core',
            'c8ydm.framework',
            'c8ydm.utils'
      ],
      entry_points={
        'console_scripts': [
              'c8ydm.start=c8ydm.main:start',
              'c8ydm.stop=c8ydm.main:stop'
            ],
      },
      zip_safe=False)