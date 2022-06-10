# Copyright (C) 2022 Indoc Research
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from setuptools import find_packages
from setuptools import setup

from env import ENVAR

app_name = ENVAR.app_name


def read_requirements():
    with open('requirements.txt') as req:
        content = req.read()
        requirements = content.split('\n')
    return requirements


setup(
    name=app_name,
    version='1.8.0',
    packages=find_packages(),
    include_package_data=True,
    install_requires=read_requirements(),
    entry_points=f"""
        [console_scripts]
        {app_name}=app.pilotcli:cli
    """
)
