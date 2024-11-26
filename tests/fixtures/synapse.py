# Copyright 2024 New Vector Ltd
#
# SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-Element-Commercial

import asyncio
import logging

import pyhelm3
import pytest
from lightkube import AsyncClient

from ..lib.synapse import create_user
from .data import ESSData

# Until synapse release is ready, this is complaining that the helm status command fails
logging.getLogger("pyhelm3").setLevel(logging.ERROR)


@pytest.fixture(scope="session")
async def synapse_ready(
    cluster, kube_client: AsyncClient, helm_client: pyhelm3.Client, ingress, ess_namespace, generated_data: ESSData
):
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
                raise Exception("Synapse Release seems to have failed deploying")
        except pyhelm3.errors.ReleaseNotFoundError:
            continue
        finally:
            counter += 1
            await asyncio.sleep(1)

        if counter > 180:
            raise Exception("Synapse Release did not become DEPLOYED after 180s")

    await asyncio.to_thread(
        cluster.wait,
        name=f"ingress/{generated_data.release_name}-synapse",
        namespace=generated_data.ess_namespace,
        waitfor="jsonpath='{.status.loadBalancer.ingress[0].ip}'",
    )


@pytest.fixture(scope="session")
async def synapse_users(request, generated_data: ESSData, ssl_context, synapse_ready):
    wait_for_users = []
    for user in request.param:
        wait_for_users.append(
            create_user(
                "synapse.ess.localhost",
                user,
                generated_data.secrets_random,
                False,
                generated_data.registration_shared_secret,
                ssl_context,
            )
        )
    return await asyncio.gather(*wait_for_users)
