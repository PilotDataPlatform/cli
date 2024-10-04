# Copyright (C) 2022-2024 Indoc Systems
#
# Contact Indoc Systems for any questions regarding the use of this source code.

from logging import getLogger

from app.configs.config import ConfigClass

debug_logger = getLogger()
debug_logger.setLevel(ConfigClass.log_level)
