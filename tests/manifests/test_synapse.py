# Copyright 2024 New Vector Ltd
#
# SPDX-License-Identifier: AGPL-3.0-only

from typing import Any

import pytest

from . import DeployableDetails
from .utils import iterate_deployables_ingress_parts


@pytest.mark.parametrize("values_file", ["synapse-minimal-values.yaml"])
@pytest.mark.asyncio_cooperative
async def test_appservice_configmaps_are_templated(release_name, values, make_templates):
    values["synapse"].setdefault("appservices", []).append(
        {"configMap": "as-{{ $.Release.Name }}", "configMapKey": "reg.yaml"}
    )

    for template in await make_templates(values):
        if template["metadata"]["name"].startswith(f"{release_name}-synapse") and template["kind"] == "StatefulSet":
            for volume in template["spec"]["template"]["spec"]["volumes"]:
                if (
                    "configMap" in volume
                    and volume["configMap"]["name"] == f"as-{release_name}"
                    and volume["name"] == "as-0"
                ):
                    break
            else:
                raise AssertionError(
                    "The appservice configMap wasn't included in the volumes : "
                    f"{','.join([volume['name'] for volume in template['spec']['template']['spec']['volumes']])}"
                )

            for volumeMount in template["spec"]["template"]["spec"]["containers"][0]["volumeMounts"]:
                if volumeMount["name"] == "as-0" and volumeMount["mountPath"] == "/as/0/reg.yaml":
                    break
            else:
                raise AssertionError("The appservice configMap isn't mounted at the expected location")


@pytest.mark.parametrize("values_file", ["synapse-minimal-values.yaml"])
@pytest.mark.asyncio_cooperative
async def test_appservice_secrets_are_templated(release_name, values, make_templates):
    values["synapse"].setdefault("appservices", []).append(
        {"secret": "as-{{ $.Release.Name }}", "secretKey": "reg.yaml"}
    )

    for template in await make_templates(values):
        if template["metadata"]["name"].startswith(f"{release_name}-synapse") and template["kind"] == "StatefulSet":
            for volume in template["spec"]["template"]["spec"]["volumes"]:
                if (
                    "secret" in volume
                    and volume["secret"]["secretName"] == f"as-{release_name}"
                    and volume["name"] == "as-0"
                ):
                    break
            else:
                raise AssertionError(
                    "The appservice secret wasn't included in the volumes : "
                    f"{','.join([volume['name'] for volume in template['spec']['template']['spec']['volumes']])}"
                )

            for volumeMount in template["spec"]["template"]["spec"]["containers"][0]["volumeMounts"]:
                if volumeMount["name"] == "as-0" and volumeMount["mountPath"] == "/as/0/reg.yaml":
                    break
            else:
                raise AssertionError("The appservice secret isn't mounted at the expected location")


@pytest.mark.parametrize("values_file", ["synapse-minimal-values.yaml"])
@pytest.mark.asyncio_cooperative
async def test_max_upload_size_annotation_global_ingressType(values, make_templates):
    for template in await make_templates(values):
        if template["kind"] == "Ingress":
            assert "nginx.ingress.kubernetes.io/proxy-body-size" not in template["metadata"].get("annotations", {})

    values.setdefault("ingress", {})["controllerType"] = "ingress-nginx"

    for template in await make_templates(values):
        if template["kind"] == "Ingress":
            assert "nginx.ingress.kubernetes.io/proxy-body-size" in template["metadata"].get("annotations", {})


@pytest.mark.parametrize("values_file", ["synapse-minimal-values.yaml"])
@pytest.mark.asyncio_cooperative
async def test_max_upload_size_annotation_component_ingressType(values, deployables_details, make_templates):
    def set_ingress_type(values_fragment: dict[str, Any], deployable_details: DeployableDetails):
        values_fragment.setdefault("ingress", {})["controllerType"] = "ingress-nginx"

    for template in await make_templates(values):
        if template["kind"] == "Ingress":
            assert "nginx.ingress.kubernetes.io/proxy-body-size" not in template["metadata"].get("annotations", {})

    iterate_deployables_ingress_parts(deployables_details, values, set_ingress_type)

    for template in await make_templates(values):
        if template["kind"] == "Ingress":
            assert "nginx.ingress.kubernetes.io/proxy-body-size" in template["metadata"].get("annotations", {})
