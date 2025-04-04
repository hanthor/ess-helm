# Copyright 2024 New Vector Ltd
#
# SPDX-License-Identifier: AGPL-3.0-only

import json
import re
from typing import Any

import pytest

from . import DeployableDetails
from .utils import iterate_deployables_ingress_parts

msc_2965_authentication = {
    "org.matrix.msc2965.authentication": {
        "issuer": "https://mas.ess.localhost/",
        "account": "https://mas.ess.localhost/account",
    }
}
synapse_federation = {"m.server": "synapse.ess.localhost:443"}
synapse_base_url = {"m.homeserver": {"base_url": "https://synapse.ess.localhost"}}


async def assert_well_known_files(
    release_name, values, make_templates, expected_client=None, expected_server=None, expected_element=None
):
    if expected_element is None:
        expected_element = {}
    if expected_server is None:
        expected_server = {}
    if expected_client is None:
        expected_client = {}
    expected_client = expected_client | {
        "org.matrix.msc4143.rtc_foci": [
            {"type": "livekit", "livekit_service_url": "https://livekit-jwt.mrtc.element.io"}
        ]
    }
    client_config = {"testclientkey": {"testsubket": "testvalue"}}
    server_config = {"testserverkey": {"testsubket": "testvalue"}}
    element_config = {"testelementkey": {"testsubket": "testvalue"}}
    support_config = {"testsupportkey": {"testsubket": "testvalue"}}
    values["wellKnownDelegation"].setdefault("additional", {})["client"] = json.dumps(client_config)
    values["wellKnownDelegation"].setdefault("additional", {})["server"] = json.dumps(server_config)
    values["wellKnownDelegation"].setdefault("additional", {})["element"] = json.dumps(element_config)
    values["wellKnownDelegation"].setdefault("additional", {})["support"] = json.dumps(support_config)
    for template in await make_templates(values):
        if template["kind"] == "ConfigMap" and template["metadata"]["name"] == f"{release_name}-well-known-haproxy":
            client_from_json = json.loads(template["data"]["client"])
            assert client_from_json == client_config | expected_client

            server_from_json = json.loads(template["data"]["server"])
            assert server_from_json == server_config | expected_server

            element_from_json = json.loads(template["data"]["element.json"])
            assert element_from_json == element_config | expected_element

            support_config_from_json = json.loads(template["data"]["support"])
            assert support_config == support_config_from_json

            break
    else:
        raise AssertionError("Unable to find WellKnownDelegationConfigMap")


@pytest.mark.parametrize("values_file", ["well-known-minimal-values.yaml"])
@pytest.mark.asyncio_cooperative
async def test_only_additional_if_all_disabled_in_well_known(release_name, values, make_templates):
    await assert_well_known_files(release_name, values, make_templates)


@pytest.mark.parametrize("values_file", ["well-known-synapse-values.yaml"])
@pytest.mark.asyncio_cooperative
async def test_synapse_injected_in_server_and_client_well_known(release_name, values, make_templates):
    await assert_well_known_files(
        release_name, values, make_templates, expected_client=synapse_base_url, expected_server=synapse_federation
    )


@pytest.mark.parametrize("values_file", ["well-known-mas-values.yaml"])
@pytest.mark.asyncio_cooperative
async def test_mas_injected_in_client_well_known(release_name, values, make_templates):
    await assert_well_known_files(release_name, values, make_templates, expected_client=msc_2965_authentication)


@pytest.mark.parametrize("values_file", ["well-known-synapse-mas-values.yaml"])
@pytest.mark.asyncio_cooperative
async def test_synapse_and_mas_injected_in_client_and_server_well_known(release_name, values, make_templates):
    await assert_well_known_files(
        release_name,
        values,
        make_templates,
        expected_client=(msc_2965_authentication | synapse_base_url),
        expected_server=synapse_federation,
    )


@pytest.mark.parametrize("values_file", ["well-known-element-web-values.yaml"])
@pytest.mark.asyncio_cooperative
async def test_has_redirect_to_element_web(release_name, values, make_templates):
    for template in await make_templates(values):
        if template["kind"] == "ConfigMap" and template["metadata"]["name"] == f"{release_name}-haproxy":
            haproxy_cfg = template["data"]["haproxy.cfg"]
            assert (
                re.search(
                    rf"http-request redirect\s+code\s+301\s+location\s+https://{values['elementWeb']['ingress']['host']}\sunless\swell-known",
                    haproxy_cfg,
                )
                is not None
            )


@pytest.mark.parametrize("values_file", ["well-known-minimal-values.yaml"])
@pytest.mark.asyncio_cooperative
async def test_dot_path_global_ingressType(values, make_templates):
    for template in await make_templates(values):
        if template["kind"] == "Ingress":
            for path in template["spec"]["rules"][0]["http"]["paths"]:
                if path["path"].startswith("/.well-known"):
                    assert path["pathType"] == "Prefix"

    values.setdefault("ingress", {})["controllerType"] = "ingress-nginx"

    for template in await make_templates(values):
        if template["kind"] == "Ingress":
            for path in template["spec"]["rules"][0]["http"]["paths"]:
                if path["path"].startswith("/.well-known"):
                    assert path["pathType"] == "ImplementationSpecific"


@pytest.mark.parametrize("values_file", ["well-known-minimal-values.yaml"])
@pytest.mark.asyncio_cooperative
async def test_dot_path_component_ingressType(deployables_details, values, make_templates):
    def set_ingress_type(values_fragment: dict[str, Any], deployable_details: DeployableDetails):
        values_fragment.setdefault("ingress", {})["controllerType"] = "ingress-nginx"

    for template in await make_templates(values):
        if template["kind"] == "Ingress":
            for path in template["spec"]["rules"][0]["http"]["paths"]:
                if path["path"].startswith("/.well-known"):
                    assert path["pathType"] == "Prefix"

    iterate_deployables_ingress_parts(deployables_details, values, set_ingress_type)

    for template in await make_templates(values):
        if template["kind"] == "Ingress":
            for path in template["spec"]["rules"][0]["http"]["paths"]:
                if path["path"].startswith("/.well-known"):
                    assert path["pathType"] == "ImplementationSpecific"
