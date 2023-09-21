# command_line_tool_ctl

[![Python](https://img.shields.io/badge/python-3.7-brightgreen.svg)](https://www.python.org/)

## About
Command line tool that allows the user to execute data operations on the platform.
### Built With
- Python
- [Click](https://click.palletsprojects.com/en/8.0.x/)


#### Run from bundled application
1. Navigate to the appropriate directory for your system.

        ./app/bundled_app/linux/
        ./app/bundled_app/mac/
        ./app/bundled_app/mac_arm/

#### Run with Python
1. Install dependencies (optional: run in edit mode).

       poetry install
       poetry run pilotcli

2. Add environment variables if needed.

## Usage

    ./app/bundled_app/linux/pilotcli --help

### Build Instructions
1. Each system has its own credential, so building should be done after the updated the env file.
2. Run build commands for your system.

    Linux example for each environment:

        pyinstaller -F --distpath ./app/bundled_app/linux --specpath ./app/build/linux --workpath ./app/build/linux --paths=./.venv/lib/python3.8/site-packages ./app/pilotcli.py -n <app-name>

    Note: Building for ARM Mac may require a newer version of `pyinstaller`.

## Acknowledgements
The development of the HealthDataCloud open source software was supported by the EBRAINS research infrastructure, funded from the European Union's Horizon 2020 Framework Programme for Research and Innovation under the Specific Grant Agreement No. 945539 (Human Brain Project SGA3) and H2020 Research and Innovation Action Grant Interactive Computing E-Infrastructure for the Human Brain Project ICEI 800858.
