# command_line_tool_ctl

## About
Command line tool that allows the user to execute data operations on the platform.
### Built With
- Python
- [Click](https://click.palletsprojects.com/en/8.0.x/)
## Getting Started

### Prerequisites
N/A

### Installation

#### Run from bundled application
1. Navigate to the appropriate directory for your system.

        ./app/bundled_app/linux/
        ./app/bundled_app/mac/
        ./app/bundled_app/mac_arm/

2. Run application.

        ./cli

#### Run with Python
1. Install dependencies (optional: run in edit mode).

       pip install -r requirements.txt
       pip install --editable .

2. Add environment variables if needed.
3. Run application.

       python run.py [COMMANDS]

## Usage

### Build Instructions
1. Each system has its own credential, so building should be done after the updated the env file.
2. Run build commands for your system.

    Linux example for each environment:

        pyinstaller -F --distpath ./app/bundled_app/linux --specpath ./app/build/linux --workpath ./app/build/linux --paths=./.venv/lib/python3.8/site-packages ./app/pilotcli.py -n <app-name>

    Note: Building for ARM Mac may require a newer version of `pyinstaller`.

3. Upload files.

        ./app/bundled_app/linux/pilotcli file put ./test_seeds
