#
# Copyright (c) 2021 Software AG, Darmstadt, Germany and/or its licensors
#
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

from setuptools import setup, find_packages
from pathlib import Path

this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

setup(
      python_requires=">=3.7",
      name='c8ydm',
      long_description=long_description,
      long_description_content_type="text/markdown",
      version='1.1.1',
      description='Cumulocity Device Management Agent',
      author='Tobias Sommer, Stefan Witschel, Marco Stoffel, Murat Bayram',
      author_email="Stefan.Witschel@softwareag.com",
      license='Apache 2.0',
      packages=find_packages(),
      entry_points={
        'console_scripts': [
              'c8ydm.start=c8ydm.main:start',
              'c8ydm.stop=c8ydm.main:stop'
            ],
      },
      install_requires=[
        "paho-mqtt>=1.5.1",
        "psutil>=5.8.0",
        "requests>=2.25.1",
        "c8y-device-proxy>=1.1.1",
        "certifi>=2021.10.8",
        "distro>=1.6.0",
        "sense-hat>=2.2.0"
    ],
      zip_safe=False)