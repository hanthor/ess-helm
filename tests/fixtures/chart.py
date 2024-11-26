# Copyright 2024 New Vector Ltd
#
# SPDX-License-Identifier: LicenseRef-Element-Commercial

import asyncio  # noqa: I001

import pyhelm3
import pytest
from .data import ESSData


@pytest.fixture(scope="session")
async def revision_deployed(cluster, helm_client: pyhelm3.Client, ingress, ess_namespace, generated_data: ESSData):
    counter = 0
    while True:
        try:
            revision = await helm_client.get_current_revision(
                generated_data.release_name,
                namespace=generated_data.ess_namespace,
            )
            if revision.status == pyhelm3.ReleaseRevisionStatus.DEPLOYED:
                break
            elif revision.status != pyhelm3.ReleaseRevisionStatus.PENDING_INSTALL:
                raise Exception("Helm Release seems to have failed deploying")
        except pyhelm3.errors.ReleaseNotFoundError:
            continue

        counter += 1
        await asyncio.sleep(1)
        if counter > 180:
            raise Exception("Helm Release did not become DEPLOYED after 180s")
