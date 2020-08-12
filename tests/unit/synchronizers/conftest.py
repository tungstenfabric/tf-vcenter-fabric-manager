import pytest

from cvfm import models


@pytest.fixture
def fabric_vn(project):
    return {"uuid": models.generate_uuid("dvportgroup-1")}
