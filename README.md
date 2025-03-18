<!-- COMPATIBLE_VERSIONS_START -->
| Cli Version | Pilot Release Version | Compatible Version |
|----------|----------|----------|
| 3.15.0   | 2.14.2  | 2.14.2   |
| 3.15.1   | 2.14.2  | 2.14.2   |
| 3.15.2   | 2.15  | 2.15   |
| Unknown | 2.15 | 2.15 |
<!-- COMPATIBLE_VERSIONS_END -->

## Build Instructions
1. Each system has its own credential, so building should be done after the updated the env file.
2. Run build commands for your system.

    Linux example for each environment:

        pyinstaller -F --distpath ./app/bundled_app/linux --specpath ./app/build/linux --workpath ./app/build/linux --paths=./.venv/lib/python3.10/site-packages ./app/pilotcli.py -n <app-name>

    Note: Building for ARM Mac may require a newer version of `pyinstaller`.

    Or Windows example:

        # remember to remove the poetry.lock file before building for windows
        rm poetry.lock
        pyinstaller -F --distpath ./app/bundled_app/windows --specpath ./app/build/windows --workpath ./app/build/windows --paths=./.venv/Lib/site-packages ./app/pilotcli.py -n <app-name>
