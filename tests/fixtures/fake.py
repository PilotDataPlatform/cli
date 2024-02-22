# Copyright (C) 2023-2024 Indoc Systems
#
# Contact Indoc Systems for any questions regarding the use of this source code.

import faker
import pytest


class Faker(faker.Faker):
    pass


@pytest.fixture
def fake() -> Faker:
    yield Faker()
