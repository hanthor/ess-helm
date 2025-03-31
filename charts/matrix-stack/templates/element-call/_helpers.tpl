{{- /*
Copyright 2024 New Vector Ltd

SPDX-License-Identifier: AGPL-3.0-only
*/ -}}

{{- define "element-io.element-call.sfu-jwt.labels" -}}
{{- $root := .root -}}
{{- with required "element-io.element-call.labels missing context" .context -}}
{{ include "element-io.ess-library.labels.common" (dict "root" $root "context" .labels) }}
app.kubernetes.io/component: matrix-stack-rtc
app.kubernetes.io/name: element-call-sfu-jwt
app.kubernetes.io/instance: {{ $root.Release.Name }}-element-call-sfu-jwt
app.kubernetes.io/version: {{ .image.tag }}
{{- end }}
{{- end }}


{{- define "element-io.element-call.sfu-jwt.env" }}
{{- $root := .root -}}
{{- with required "element-io.sfuJwt.env missing context" .context -}}
{{- $resultEnv := dict -}}
{{- range $envEntry := .extraEnv -}}
{{- $_ := set $resultEnv $envEntry.name $envEntry.value -}}
{{- end -}}
{{- range $key, $value := $resultEnv }}
- name: {{ $key | quote }}
  value: {{ $value | quote }}
{{- end -}}
{{- end -}}
{{- end -}}
