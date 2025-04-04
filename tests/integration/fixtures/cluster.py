# Copyright 2024 New Vector Ltd
#
# SPDX-License-Identifier: AGPL-3.0-only

import asyncio
import os
from collections.abc import AsyncGenerator
from pathlib import Path
from typing import Any

import pyhelm3
import pytest
import yaml
from lightkube import AsyncClient, KubeConfig
from lightkube.models.meta_v1 import ObjectMeta
from lightkube.resources.core_v1 import Namespace, Service
from pytest_kubernetes.options import ClusterOptions
from pytest_kubernetes.providers import KindManager
from python_on_whales import docker

from .data import ESSData


class PotentiallyExistingKindCluster(KindManager):
    def __init__(self, cluster_name, cluster_config=None):
        super().__init__(cluster_name, cluster_config)

        # Remove the pytest- prefix
        self.cluster_name = cluster_name

        clusters = self._exec(["get", "clusters"])
        if self.cluster_name in clusters.stdout.decode("utf-8").split("\n"):
            self.existing_cluster = True
        else:
            self.existing_cluster = False

    def _on_create(self, cluster_options, **kwargs):
        if self.existing_cluster:
            self._exec(
                [
                    "export",
                    "kubeconfig",
                    "--name",
                    self.cluster_name,
                    "--kubeconfig ",
                    str(cluster_options.kubeconfig_path),
                ]
            )
        else:
            # The cluster requires extraMounts. These are relative paths from the cluster config file
            # as they'll be different for everyone + CI.
            # We save off the current working directory incase it is important, change to the folder
            # with the cluster config file and then change back afterwards
            cwd = os.getcwd()
            try:
                fixtures_folder = Path(__file__).parent.resolve()
                os.chdir(fixtures_folder / Path("files/clusters"))
                super()._on_create(cluster_options, **kwargs)
            finally:
                os.chdir(cwd)

    def _on_delete(self):
        # We always keep around an existing cluster, it can always be deleted with scripts/destroy-test-cluster.sh
        if not self.existing_cluster and os.environ.get("PYTEST_KEEP_CLUSTER", "") != "1":
            return super()._on_delete()


@pytest.fixture(autouse=True, scope="session")
async def cluster():
    # This name must match what `setup_test_cluster.sh` would create
    this_cluster = PotentiallyExistingKindCluster("ess-helm")
    this_cluster.create(ClusterOptions(cluster_config="kind.yml"))

    yield this_cluster

    this_cluster.delete()


@pytest.fixture(scope="session")
async def helm_client(cluster):
    yield pyhelm3.Client(kubeconfig=cluster.kubeconfig, kubecontext=cluster.context)


@pytest.fixture(scope="session")
async def kube_client(cluster):
    kube_config = KubeConfig.from_file(cluster.kubeconfig)
    yield AsyncClient(config=kube_config)


@pytest.fixture(autouse=True, scope="session")
async def ingress(cluster, kube_client, helm_client: pyhelm3.Client):
    chart = await helm_client.get_chart("ingress-nginx", repo="https://kubernetes.github.io/ingress-nginx")

    values_file = Path(__file__).parent.resolve() / Path("files/charts/ingress-nginx.yml")
    # Install or upgrade a release
    await helm_client.install_or_upgrade_release(
        "ingress-nginx",
        chart,
        yaml.safe_load(values_file.read_text("utf-8")),
        namespace="ingress-nginx",
        create_namespace=True,
        atomic=True,
        wait=True,
    )

    await asyncio.to_thread(
        cluster.wait,
        name="endpoints/ingress-nginx-controller-admission",
        waitfor="jsonpath='{.subsets[].addresses}'",
        namespace="ingress-nginx",
    )
    await asyncio.to_thread(
        cluster.wait,
        name="lease/ingress-nginx-leader",
        waitfor="jsonpath='{.spec.holderIdentity}'",
        namespace="ingress-nginx",
    )
    return (await kube_client.get(Service, name="ingress-nginx-controller", namespace="ingress-nginx")).spec.clusterIP


@pytest.fixture(autouse=True, scope="session")
async def registry(cluster):
    pytest_registry_container_name = "pytest-ess-helm-registry"
    test_cluster_registry_container_name = "ess-helm-registry"

    # We have a registry created by `setup_test_cluster.sh`
    if docker.container.exists(test_cluster_registry_container_name):
        container_name = test_cluster_registry_container_name
    # We have a registry created by a previous run of pytest
    elif docker.container.exists(pytest_registry_container_name):
        container_name = pytest_registry_container_name
    # We have no registry, create one
    else:
        container_name = pytest_registry_container_name
        container = docker.run(
            name=container_name,
            image="registry:2",
            publish=[("127.0.0.1:5000", "5000")],
            restart="always",
            detach=True,
        )

    container = docker.container.inspect(container_name)
    if not container.state.running:
        container.start()

    kind_network = docker.network.inspect("kind")
    if container.id not in kind_network.containers:
        docker.network.connect(kind_network, container, alias="registry")

    yield

    if container_name == pytest_registry_container_name:
        container.stop()
        container.remove()


@pytest.fixture(autouse=True, scope="session")
async def prometheus_operator_crds(helm_client):
    if os.environ.get("SKIP_SERVICE_MONITORS_CRDS", "false") == "false":
        chart = await helm_client.get_chart(
            "prometheus-operator-crds", repo="https://prometheus-community.github.io/helm-charts"
        )

        # Install or upgrade a release
        await helm_client.install_or_upgrade_release(
            "prometheus-operator-crds",
            chart,
            {},
            namespace="prometheus-operator",
            create_namespace=True,
            atomic=True,
            wait=True,
        )


@pytest.fixture(scope="session")
async def ess_namespace(
    cluster: PotentiallyExistingKindCluster, kube_client: pyhelm3.Client, generated_data: ESSData
) -> AsyncGenerator[Namespace, Any]:
    (major_version, minor_version) = cluster.version()
    namespace = await kube_client.create(
        Namespace(
            metadata=ObjectMeta(
                name=generated_data.ess_namespace,
                labels={
                    "app.kubernetes.io/managed-by": "pytest",
                    # We do turn on enforce here to cause test failures.
                    # If we actually need restricted functionality then the tests can drop this
                    # and parse the audit logs
                    "pod-security.kubernetes.io/enforce": "restricted",
                    "pod-security.kubernetes.io/enforce-version": f"v{major_version}.{minor_version}",
                    "pod-security.kubernetes.io/audit": "restricted",
                    "pod-security.kubernetes.io/audit-version": f"v{major_version}.{minor_version}",
                    "pod-security.kubernetes.io/warn": "restricted",
                    "pod-security.kubernetes.io/warn-version": f"v{major_version}.{minor_version}",
                },
            )
        )
    )

    yield namespace

    if os.environ.get("PYTEST_KEEP_CLUSTER", "") != "1":
        await kube_client.delete(Namespace, name=generated_data.ess_namespace)
