# Copyright 2024 New Vector Ltd
#
# SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-Element-Commercial

import os
from collections.abc import Awaitable

import pyhelm3
import yaml
from lightkube.models.meta_v1 import ObjectMeta
from lightkube.resources.core_v1 import Namespace, Secret

from ..artifacts import CertKey, generate_cert
from ..fixtures.data import ESSData


def namespace(name: str) -> Awaitable[Namespace]:
    return Namespace(metadata=ObjectMeta(name=name))


def kubernetes_docker_secret(name: str, namespace: str, docker_config_json: str) -> Awaitable[Secret]:
    secret = Secret(
        type="kubernetes.io/dockerconfigjson",
        metadata=ObjectMeta(name=name, namespace=namespace, labels={"app.kubernetes.io/managed-by": "pytest"}),
        stringData={".dockerconfigjson": docker_config_json},
    )
    return secret


def kubernetes_tls_secret(name: str, namespace: str, ca: CertKey, dns_names: [str], bundled=False) -> Awaitable[Secret]:
    certificate = generate_cert(ca, dns_names)
    secret = Secret(
        type="kubernetes.io/tls",
        metadata=ObjectMeta(name=name, namespace=namespace, labels={"app.kubernetes.io/managed-by": "pytest"}),
        stringData={
            "tls.crt": certificate.cert_bundle_as_pem() if bundled else certificate.cert_as_pem(),
            "tls.key": certificate.key_as_pem(),
        },
    )
    return secret


async def install_matrix_stack(helm_client: pyhelm3.Client, generated_data: ESSData):
    with open(os.environ["TEST_VALUES_FILE"]) as stream:
        values = yaml.safe_load(stream)

    chart = await helm_client.get_chart("charts/matrix-stack")
    # Install or upgrade a release
    revision = helm_client.install_or_upgrade_release(
        generated_data.release_name,
        chart,
        values,
        namespace=generated_data.ess_namespace,
        atomic=True,
        wait=True,
    )
    return revision
