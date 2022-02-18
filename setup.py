from setuptools import setup, find_packages
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
