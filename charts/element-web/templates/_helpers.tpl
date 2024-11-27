{{- /*
Copyright 2024 New Vector Ltd

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-Element-Commercial
*/ -}}

{{- define "element-io.element-web.labels" -}}
{{- $global := .global -}}
{{- with required "element-io.element-web.labels" .context -}}
{{ include "element-io.ess-library.labels.common" (list $global .labels) }}
app.kubernetes.io/component: matrix-client
app.kubernetes.io/name: element-web
app.kubernetes.io/instance: {{ $global.Release.Name }}-element-web
app.kubernetes.io/version: {{ .image.tag | default $global.Chart.AppVersion }}
{{- end }}
{{- end }}

{{- define "element-io.element-web.serviceAccountName" -}}
{{- $global := .global -}}
{{- with required "element-io.element-web.serviceAccountName" .context -}}
{{ default (printf "%s-element-web" $global.Release.Name ) .serviceAccount.name }}
{{- end }}
{{- end }}

{{- define "element-io.element-web.config" }}
{{- $global := .global -}}
{{- with required "element-io.element-web.config missing context" .context -}}
{{- $config := dict }}
{{- $serverName := required "Element Web requires .ess.serverName set" $global.Values.ess.serverName }}
{{- with required "elementWeb.defaultMatrixServer is required" .defaultMatrixServer }}
{{- $baseUrl := required "elementWeb.defaultMatrixServer.baseUrl is required" .baseUrl -}}
{{- $mHomeserver := dict "base_url" $baseUrl "serverName" $serverName }}
{{- $defaultServerConfig := dict "m.homeserver" $mHomeserver -}}
{{- $_ := set $config "default_server_config" $defaultServerConfig }}
{{- end }}
{{- toPrettyJson (merge $config .additional) }}
{{- end }}
{{- end }}
