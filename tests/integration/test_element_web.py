# Copyright 2024 New Vector Ltd
#
# SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-Element-Commercial

import asyncio
import os

import pytest

from ..fixtures import ESSData
from ..lib.helpers import install_matrix_stack, kubernetes_tls_secret
from ..lib.utils import aiottp_get_json


@pytest.mark.skipif(os.environ.get("TEST_ELEMENT_WEB") != "1", reason="ElementWeb not deployed")
@pytest.mark.asyncio_cooperative
async def test_element_web(
    cluster,
    helm_client,
    kube_client,
    ssl_context,
    ca,
    generated_data: ESSData,
):
    resources = [
        kubernetes_tls_secret(
            "element-web-tls", generated_data.ess_namespace, ca, ["element.ess.localhost"], bundled=True
        )
    ]
    revision = await install_matrix_stack(helm_client, generated_data)

    await asyncio.gather(revision, *[kube_client.create(r) for r in resources])


@pytest.mark.skipif(os.environ.get("TEST_ELEMENT_WEB") != "1", reason="ElementWeb not deployed")
@pytest.mark.asyncio_cooperative
async def test_can_access_config_json(cluster, revision_deployed, generated_data: ESSData, ssl_context):
    await asyncio.to_thread(
        cluster.wait,
        name=f"ingress/{generated_data.release_name}-element-web",
        namespace=generated_data.ess_namespace,
        waitfor="jsonpath='{.status.loadBalancer.ingress[0].ip}'",
    )

    json_content = await aiottp_get_json("https://element.ess.localhost/config.json", ssl_context)
    assert "element_call" in json_content
    assert json_content["element_call"]["url"] == "https://call.ess.localhost"
    assert json_content["element_call"]["use_exclusively"]
