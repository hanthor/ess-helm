# Copyright 2024 New Vector Ltd
#
# SPDX-License-Identifier: AGPL-3.0-only

import asyncio
import os

import pytest
from lightkube import AsyncClient
from lightkube import operators as op
from lightkube.resources.core_v1 import Pod, Service

from .fixtures.data import ESSData
from .lib.helpers import wait_for_endpoint_ready
from .lib.utils import read_service_monitor_kind


@pytest.mark.asyncio_cooperative
@pytest.mark.usefixtures("matrix_stack")
async def test_services_have_matching_labels(
    kube_client: AsyncClient,
    generated_data: ESSData,
):
    ignored_labels = [
        "app.kubernetes.io/managed-by",
        "k8s.element.io/service-type",
        "k8s.element.io/synapse-instance",
        "replica",
    ]

    async for service in kube_client.list(
        Service, namespace=generated_data.ess_namespace, labels={"app.kubernetes.io/part-of": op.in_(["matrix-stack"])}
    ):
        assert service.spec is not None, f"Encountered a service without spec : {service}"
        label_selectors = {label: value for label, value in service.spec.selector.items()}

        async for pod in kube_client.list(Pod, namespace=generated_data.ess_namespace, labels=label_selectors):
            assert service.metadata is not None, f"Encountered a service without metadata : {service}"
            assert pod.metadata is not None, f"Encountered a pod without metadata : {pod}"
            has_target_label = any(label.startswith("k8s.element.io/target-") for label in service.metadata.labels)
            for label, value in service.metadata.labels.items():
                if label in ["k8s.element.io/owner-name", "k8s.element.io/owner-group-kind"]:
                    assert label not in pod.metadata.labels
                    continue
                elif label in ignored_labels or (
                    has_target_label and label in ["app.kubernetes.io/name", "app.kubernetes.io/instance"]
                ):
                    continue
                assert label.replace("k8s.element.io/target-", "app.kubernetes.io/") in pod.metadata.labels
                assert value.startswith(
                    pod.metadata.labels[label.replace("k8s.element.io/target-", "app.kubernetes.io/")]
                )


@pytest.mark.asyncio_cooperative
@pytest.mark.usefixtures("matrix_stack")
async def test_services_have_endpoints(
    cluster,
    kube_client: AsyncClient,
    generated_data: ESSData,
):
    endpoints_to_wait = []
    services = {}
    async for service in kube_client.list(
        Service, namespace=generated_data.ess_namespace, labels={"app.kubernetes.io/part-of": op.in_(["matrix-stack"])}
    ):
        assert service.metadata is not None, f"Encountered a service without metadata : {service}"
        endpoints_to_wait.append(
            wait_for_endpoint_ready(service.metadata.name, generated_data.ess_namespace, cluster, kube_client)
        )
        services[service.metadata.name] = service

    for endpoint in await asyncio.gather(*endpoints_to_wait):
        assert endpoint.metadata is not None, f"Encountered an endpoint without metadata : {endpoint}"
        assert endpoint.subsets, f"Endpoint {endpoint.metadata.name} has no subsets"

        ports = []
        for subset in endpoint.subsets:
            assert subset.addresses, f"Endpoint {endpoint.metadata.name} has no addresses"
            assert not subset.notReadyAddresses, f"Endpoint {endpoint.metadata.name} has notReadyAddresses"
            assert subset.ports, f"Endpoint {endpoint.metadata.name} has no ports"
            ports += subset.ports

        port_names = [port.name for port in ports if port.name]
        port_numbers = [port.port for port in ports]
        assert services[endpoint.metadata.name].spec is not None, f"Service {service.metadata.name} has no spec"
        for port in services[endpoint.metadata.name].spec.ports:
            if port.name:
                assert port.name in port_names
            else:
                assert port.port in port_numbers


@pytest.mark.skipif(
    os.environ.get("SKIP_SERVICE_MONITORS_CRDS", "false") == "true", reason="ServiceMonitors not deployed"
)
@pytest.mark.asyncio_cooperative
@pytest.mark.usefixtures("matrix_stack")
async def test_pods_monitored(
    kube_client: AsyncClient,
    generated_data: ESSData,
):
    all_monitorable_pods = set()
    async for pod in kube_client.list(
        Pod, namespace=generated_data.ess_namespace, labels={"app.kubernetes.io/part-of": op.in_(["matrix-stack"])}
    ):
        if pod.metadata and pod.metadata.annotations and "has-no-service-monitor" in pod.metadata.annotations:
            continue
        elif pod.metadata:
            all_monitorable_pods.add(pod.metadata.name)
        else:
            raise RuntimeError(f"Pod {pod} has no metadata")

    monitored_pods = set()
    async for service_monitor in kube_client.list(
        await read_service_monitor_kind(kube_client),
        namespace=generated_data.ess_namespace,
        labels={"app.kubernetes.io/part-of": op.in_(["matrix-stack"])},
    ):
        service_monitor_is_useful = False
        async for service in kube_client.list(
            Service, namespace=generated_data.ess_namespace, labels=service_monitor["spec"]["selector"]["matchLabels"]
        ):
            if not service.spec:
                raise RuntimeError(f"Service {service} has no spec")

            for endpoint in service_monitor["spec"]["endpoints"]:
                service_port_names = [port.name for port in service.spec.ports if port.name]
                if endpoint["port"] in service_port_names:
                    break
            # This Service does not have the named port. Potentially there's another Service that covers it
            else:
                continue

            async for covered_pod in kube_client.list(
                Pod, namespace=generated_data.ess_namespace, labels=service.spec.selector
            ):
                if not covered_pod.metadata:
                    raise RuntimeError(f"Pod {covered_pod} has no metadata")

                # Something monitored by multiple ServiceMonitors smells like a bug
                assert covered_pod.metadata.name not in monitored_pods, (
                    f"Pod {covered_pod.metadata.name} is monitored multiple times"
                )

                monitored_pods.add(covered_pod.metadata.name)
                service_monitor_is_useful = True

        assert service_monitor_is_useful, f"ServiceMonitor {service_monitor['metadata']['name']} does not cover any pod"

    assert all_monitorable_pods == monitored_pods, (
        f"Some pods are not monitored : {', '.join(list(set(all_monitorable_pods) ^ set(monitored_pods)))}"
    )
