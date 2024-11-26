# Copyright 2024 New Vector Ltd
#
# SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-Element-Commercial

import asyncio
import hashlib
import os
from pathlib import Path

import pytest

from ..fixtures import ESSData
from ..lib.helpers import install_matrix_stack, kubernetes_tls_secret
from ..lib.synapse import assert_downloaded_content, download_media, upload_media
from ..lib.utils import KubeCtl, aiohttp_post_json, aiottp_get_json
from ..services import PostgresServer


@pytest.mark.skipif(os.environ.get("TEST_SYNAPSE") != "1", reason="Synapse not deployed")
@pytest.mark.asyncio_cooperative
async def test_synapse(
    cluster,
    helm_client,
    kube_client,
    ssl_context,
    ca,
    generated_data: ESSData,
):
    resources = [
        kubernetes_tls_secret(
            "synapse-web-tls", generated_data.ess_namespace, ca, ["synapse.ess.localhost"], bundled=True
        ),
        generated_data.ess_secret(),
    ]

    postgres_setup = PostgresServer(
        name="synapse",
        namespace=generated_data.ess_namespace,
        database="synapse_db",
        user="synapse_user",
        password=generated_data.synapse_postgres_password,
    ).setup(helm_client, kube_client)

    revision = await install_matrix_stack(helm_client, generated_data)

    await asyncio.gather(revision, postgres_setup, *[kube_client.create(r) for r in resources])

    await asyncio.to_thread(
        cluster.wait,
        name=f"ingress/{generated_data.release_name}-synapse",
        namespace=generated_data.ess_namespace,
        waitfor="jsonpath='{.status.loadBalancer.ingress[0].ip}'",
    )

    json_content = await aiottp_get_json("https://synapse.ess.localhost/_matrix/client/versions", ssl_context)
    assert "unstable_features" in json_content


@pytest.mark.skipif(os.environ.get("TEST_SYNAPSE") != "1", reason="Synapse not deployed")
@pytest.mark.parametrize("synapse_users", [("sliding-sync-user",)], indirect=True)
@pytest.mark.asyncio_cooperative
async def test_simplified_sliding_sync_syncs(ssl_context, synapse_users, generated_data: ESSData):
    access_token = synapse_users[0]

    sync_result = await aiohttp_post_json(
        "https://synapse.ess.localhost/_matrix/client/unstable/org.matrix.simplified_msc3575/sync",
        {},
        {"Authorization": f"Bearer {access_token}"},
        ssl_context,
    )

    assert "pos" in sync_result


@pytest.mark.skipif(os.environ.get("TEST_SYNAPSE") != "1", reason="Synapse not deployed")
@pytest.mark.parametrize("synapse_users", [("media-upload-unauth",)], indirect=True)
@pytest.mark.asyncio_cooperative
async def test_synapse_media_upload_fetch_authenticated(
    cluster,
    ssl_context,
    synapse_users,
    generated_data: ESSData,
):
    user_access_token = synapse_users[0]

    filepath = Path(__file__).parent.parent.resolve() / Path("artifacts/files/minimal.png")
    with open(filepath, "rb") as file:
        source_sha256 = hashlib.file_digest(file, "sha256").hexdigest()

    content_upload_json = await upload_media(
        synapse_fqdn="synapse.ess.localhost",
        user_access_token=user_access_token,
        file_path=filepath,
        ssl_context=ssl_context,
    )

    content_download_sha256 = await download_media(
        server_name="ess.localhost",
        user_access_token=user_access_token,
        synapse_fqdn="synapse.ess.localhost",
        content_upload_json=content_upload_json,
        ssl_context=ssl_context,
    )

    media_pod_suffix = "synapse-media-repository-0"
    media_pod = f"synapse-{generated_data.secrets_random}-{media_pod_suffix}"

    await assert_downloaded_content(
        KubeCtl(cluster),
        media_pod,
        generated_data.ess_namespace,
        source_sha256,
        content_upload_json["content_uri"].replace("mxc://ess.localhost/", ""),
        content_download_sha256,
    )
