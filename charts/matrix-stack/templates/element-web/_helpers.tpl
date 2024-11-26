# Copyright 2024 New Vector Ltd
#
# SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-Element-Commercial

{{- define "element-io.element-web.labels" -}}
{{ include "element-io.ess-library.labels.common" (list $ .Values.elementWeb.labels) }}
app.kubernetes.io/component: matrix-client
app.kubernetes.io/name: element-web
app.kubernetes.io/instance: {{ .Release.Name }}-element-web
app.kubernetes.io/version: {{ .Values.elementWeb.image.tag | default $.Chart.AppVersion }}
{{- end }}

{{- define "element-io.element-web.serviceAccountName" -}}
{{ default (printf "%s-element-web" .Release.Name ) .Values.elementWeb.serviceAccount.name }}
{{- end }}

{{- define "element-io.element-web.config" }}
{{- $config := dict }}
{{- $serverName := required "Element Web requires global.ess.server_name set" .Values.elementWeb.global.ess.server_name }}
{{- with .Values.elementWeb.defaultMatrixServer }}
{{- $mHomeserver := dict "base_url" .baseUrl "server_name" $serverName }}
{{- $defaultServerConfig := dict "m.homeserver" $mHomeserver -}}
{{- $_ := set $config "default_server_config" $defaultServerConfig }}
{{- end }}
{{- toPrettyJson (merge $config .Values.elementWeb.additional) }}
{{- end }}
