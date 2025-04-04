# Copyright 2024 New Vector Ltd
#
# SPDX-License-Identifier: AGPL-3.0-only

import pytest

from .fixtures import ESSData
from .lib.utils import aiohttp_post_json, value_file_has


@pytest.mark.skipif(value_file_has("matrixRTC.enabled", False), reason="ElementWeb not deployed")
@pytest.mark.parametrize("users", [("matrix-rtc-user",)], indirect=True)
@pytest.mark.asyncio_cooperative
async def test_element_call_livekit_jwt(ingress_ready, users, generated_data: ESSData, ssl_context):
    await ingress_ready("synapse")
    access_token = users[0]

    openid_token = await aiohttp_post_json(
        f"https://synapse.{generated_data.server_name}/_matrix/client/v3/user/@matrix-rtc-user:{generated_data.server_name}/openid/request_token",
        {},
        {"Authorization": f"Bearer {access_token}"},
        ssl_context,
    )

    livekit_jwt_payload = {
        "openid_token": {
            "access_token": openid_token["access_token"],
            "matrix_server_name": generated_data.server_name,
        },
        "room": f"!blah:{generated_data.server_name}",
        "device_id": "something",
    }

    await ingress_ready("matrix-rtc-sfu-jwt")
    await ingress_ready("well-known")
    livekit_jwt = await aiohttp_post_json(
        f"https://mrtc.{generated_data.server_name}/sfu/get",
        livekit_jwt_payload,
        {"Authorization": f"Bearer {access_token}"},
        ssl_context,
    )

    assert livekit_jwt["url"] == f"wss://mrtc.{generated_data.server_name}"
    assert "jwt" in livekit_jwt
