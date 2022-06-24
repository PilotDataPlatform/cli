# command_line_tool_ctl
[![License: AGPL v3](https://img.shields.io/badge/License-AGPL_v3-blue.svg?style=for-the-badge)](https://www.gnu.org/licenses/agpl-3.0)
[![Python 3.7](https://img.shields.io/badge/python-3.7-green?style=for-the-badge)](https://www.python.org/)
[![GitHub Workflow Status (branch)](https://img.shields.io/github/workflow/status/PilotDataPlatform/cli/CI/develop?style=for-the-badge)](https://github.com/PilotDataPlatform/cli/actions/workflows/main.yml)

[![codecov](https://img.shields.io/codecov/c/github/PilotDataPlatform/cli/develop?style=for-the-badge)](https://codecov.io/gh/PilotDataPlatform/cli)
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

