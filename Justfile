# Copyright 2024 New Vector Ltd
#
# SPDX-License-Identifier: AGPL-3.0-only

# -*- mode: sh -*-
# Set shell options for safety and consistency

set shell := ["bash", "-euo", "pipefail", "-c"]

# Prevent variables from being exported to recipe shells by default

set export := false

# --- Variables ---

chart_dir := "charts/matrix-stack"
ci_dir := chart_dir + "/ci"
scripts_dir := "scripts"
default_namespace := "ess"

# --- Linting & Validation ---

# Run chart-testing linters (Helm lint wrapper)
lint-helm: install-deps
    @echo "Running chart-testing lint..."
    ./{{ scripts_dir }}/ct-lint.sh

# Run checkov security scanner on the Helm chart using a specific values file

# Usage: just lint-checkov ci/component-checkov-values.yaml [NAMESPACE]
lint-checkov values_file namespace=default_namespace: install-deps
    @echo "Running checkov with values file: {{ chart_dir }}/{{ values_file }} in namespace {{ namespace }}..."
    cd {{ chart_dir }} && HELM_NAMESPACE={{ namespace }} checkov -d . --framework helm --quiet --var-file {{ values_file }}

# Run kubeconform to validate rendered manifests against Kubernetes schemas using a specific values file

# Usage: just lint-kubeconform ci/some-values.yaml
lint-kubeconform values_file: install-deps
    @echo "Running kubeconform validation with values file: {{ chart_dir }}/{{ values_file }}..."
    cd {{ chart_dir }} && helm template -f {{ values_file }} . | kubeconform -summary

# Run reuse to validate file copyright and licensing
lint-reuse: install-deps
    @echo "Running REUSE lint..."
    reuse lint

# Run shellcheck on shell scripts in the scripts/ directory
lint-shellcheck: install-deps
    @echo "Running shellcheck..."
    shellcheck {{ scripts_dir }}/*.sh

# Run all linters (using a default checkov/kubeconform values file if needed, adjust as necessary)

# Note: You might want specific recipes for linting against all relevant CI values files
lint: lint-helm lint-reuse lint-shellcheck
    @echo "Running default checkov (requires ci/synapse-checkov-values.yaml)..."
    # Example: Choose a default or representative checkov file
    just lint-checkov ci/synapse-checkov-values.yaml
    @echo "Running default kubeconform (requires ci/nothing-enabled-values.yaml)..."
    # Example: Choose a default or representative kubeconform file
    just lint-kubeconform ci/nothing-enabled-values.yaml


# --- Setup ---

# Install development dependencies using Poetry
install-deps:
    poetry install

# --- Building ---

# Assemble Helm chart values.yaml and values.schema.json from fragments
build-helm-values: install-deps
    @echo "Assembling Helm chart values and schema..."
    ./{{ scripts_dir }}/assemble_helm_charts_from_fragments.sh
    @echo "Done. Remember to commit the changes to {{ chart_dir }}/values.yaml and {{ chart_dir }}/values.schema.json"

# Assemble CI values files from fragments
build-ci-values: install-deps
    @echo "Assembling CI values files..."
    ./{{ scripts_dir }}/assemble_ci_values_files_from_fragments.sh
    @echo "Done. Remember to commit any changes to files in {{ ci_dir }}"

# Set the chart version in Chart.yaml
set-version version:
    @echo "Setting chart version to {{ version }}..."
    ./{{ scripts_dir }}/set_chart_version.sh {{ version }}
    @echo "Done. Remember to commit the changes to {{ chart_dir }}/Chart.yaml"

# Build all generated files
build: build-helm-values build-ci-values

# --- Test Cluster Management ---
# Setup the test cluster using Kind (ingress, cert-manager, postgres, etc.)

# Usage: just cluster-up [NAMESPACES='ess']
cluster-up *namespaces:
    @echo "Setting up test cluster..."
    {%- if namespaces -%}
    export ESS_NAMESPACES="{{ namespaces }}"
    {%- else -%}
    export ESS_NAMESPACES="{{ default_namespace }}"
    {%- endif -%}
    ./{{ scripts_dir }}/setup_test_cluster.sh
    @echo "Cluster setup script finished."
    @echo "Use 'just cluster-kubeconfig' to get the kubeconfig command."

# Destroy the test cluster
cluster-down:
    @echo "Destroying test cluster..."
    ./{{ scripts_dir }}/destroy_test_cluster.sh

# Show command to export kubeconfig for the test cluster
cluster-kubeconfig:
    @echo "Run the following command to configure kubectl:"
    @echo "  kind export kubeconfig --name ess-helm"

# Deploy or upgrade the chart to the test cluster

# Usage: just cluster-deploy ci/your-values.yaml [NAMESPACE]
cluster-deploy values_file namespace=default_namespace:
    @echo "Deploying chart with values {{ chart_dir }}/{{ values_file }} to namespace {{ namespace }}..."
    helm -n {{ namespace }} upgrade -i ess {{ chart_dir }} -f {{ chart_dir }}/ci/test-cluster-mixin.yaml -f {{ chart_dir }}/{{ values_file }}
    @echo "Deployment complete."

# --- Integration Tests ---
# Run Pytest integration tests

# Usage: just test [KEEP_CLUSTER=0] [PYTEST_ARGS='']
test keep_cluster='0' *pytest_args: install-deps
    @echo "Running integration tests..."
    export PYTEST_KEEP_CLUSTER={{ keep_cluster }}
    pytest test {{ pytest_args }}

# --- Development Utilities ---
# Inspect a rendered Helm template

# Usage: just template-inspect ci/your-values.yaml templates/your-template.yaml [NAMESPACE] [EXTRA_ARGS='']
template-inspect values_file template_path namespace=default_namespace *extra_args:
    @echo "Rendering template {{ template_path }} with values {{ chart_dir }}/{{ values_file }}..."
    cd {{ chart_dir }} && helm template -n {{ namespace }} -f {{ values_file }} . -s {{ template_path }} {{ extra_args }}

# Inspect a rendered Helm template with debug output (useful for syntax errors)

# Usage: just template-debug ci/your-values.yaml templates/your-template.yaml [NAMESPACE] [EXTRA_ARGS='']
template-debug values_file template_path namespace=default_namespace *extra_args:
    @echo "Rendering template {{ template_path }} with values {{ chart_dir }}/{{ values_file }} (DEBUG)..."
    cd {{ chart_dir }} && helm template -n {{ namespace }} -f {{ values_file }} . -s {{ template_path }} --debug {{ extra_args }}

# --- Changelog ---
# Create a towncrier newsfragment for a PR

# Usage: just changelog-create <pr_number>.<type> (e.g., just changelog-create 123.added)
changelog-create fragment_name: install-deps
    @echo "Creating newsfragment: {{ fragment_name }}"
    cd {{ chart_dir }} && towncrier create {{ fragment_name }}

# Build the changelog (usually done at release time)
changelog-build: install-deps
    @echo "Building changelog..."
    cd {{ chart_dir }} && towncrier build --draft # Use --draft to see output, remove for actual build
    @echo "Changelog build preview complete (used --draft)."

