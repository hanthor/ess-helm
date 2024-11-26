# Copyright 2024 New Vector Ltd
#
# SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-Element-Commercial

{{- define "element-io.ess-library.labels.common" -}}
{{- $ := index . 0 }}
{{- $userLabels := dict -}}
{{- $userLabels = merge $userLabels $.Values.global.ess.labels }}
{{- $userLabels = merge $userLabels ( index . 1) }}
{{- /* These labels are owned by the chart, don't allow overriding */}}
{{- $userLabels = unset $userLabels "helm.sh/chart.sh" }}
{{- $userLabels = unset $userLabels "app.kubernetes.io/managed-by" }}
{{- $userLabels = unset $userLabels "app.kubernetes.io/part-of" }}
{{- $userLabels = unset $userLabels "app.kubernetes.io/component" }}
{{- $userLabels = unset $userLabels "app.kubernetes.io/name" }}
{{- $userLabels = unset $userLabels "app.kubernetes.io/instance" }}
{{- $userLabels = unset $userLabels "app.kubernetes.io/version" }}
{{- if $userLabels }}
{{- toYaml $userLabels }}
{{- end }}
helm.sh/chart: {{ $.Chart.Name }}-{{ $.Chart.Version | replace "+" "_" }}
app.kubernetes.io/managed-by: {{ $.Release.Service }}
app.kubernetes.io/part-of: matrix-stack
{{- end }}
