{{- /*
Copyright 2024 New Vector Ltd

SPDX-License-Identifier: AGPL-3.0-only
*/ -}}

{{- define "element-io.element-call-sfu-jwt.labels" -}}
{{- $root := .root -}}
{{- with required "element-io.element-call.labels missing context" .context -}}
{{ include "element-io.ess-library.labels.common" (dict "root" $root "context" .labels) }}
app.kubernetes.io/component: matrix-stack-sfu-jwt
app.kubernetes.io/name: element-call
app.kubernetes.io/instance: {{ $root.Release.Name }}-element-call
app.kubernetes.io/version: {{ .image.tag }}
{{- end }}
{{- end }}

{{- define "element-io.element-call-sfu.labels" -}}
{{- $root := .root -}}
{{- with required "element-io.element-call.labels missing context" .context -}}
{{ include "element-io.ess-library.labels.common" (dict "root" $root "context" .labels) }}
app.kubernetes.io/component: matrix-stack-rtc
app.kubernetes.io/name: element-call-sfu
app.kubernetes.io/instance: {{ $root.Release.Name }}-element-call-sfu
app.kubernetes.io/version: {{ .image.tag }}
{{- end }}
{{- end }}

{{- define "element-io.element-call-sfu-jwt.env" }}
{{- $root := .root -}}
{{- with required "element-io.sfu-jwt.env missing context" .context -}}
{{- $resultEnv := dict -}}
{{- range $envEntry := .extraEnv -}}
{{- $_ := set $resultEnv $envEntry.name $envEntry.value -}}
{{- end -}}
- name: LIVEKIT_KEY_PATH
  value: /secrets/{{
  include "element-io.ess-library.init-secret-path" (
    dict "root" $root "context" (
      dict "secretPath" "elementCall.livekitKey"
           "initSecretKey" "ELEMENT_CALL_LIVEKIT_KEY"
           "defaultSecretName" (printf "%s-element-call" $root.Release.Name)
           "defaultSecretKey" "LIVEKIT_KEY"
      )
    ) }}
- name: LIVEKIT_SECRET_PATH
  value: /secrets/{{
  include "element-io.ess-library.init-secret-path" (
    dict "root" $root "context" (
      dict "secretPath" "elementCall.livekitSecret"
           "initSecretKey" "ELEMENT_CALL_LIVEKIT_SECRET"
           "defaultSecretName" (printf "%s-element-call" $root.Release.Name)
           "defaultSecretKey" "LIVEKIT_SECRET"
      )
    ) }}
- name: LIVEKIT_URL
  value: "wss://{{ .ingress.host }}"
{{- range $key, $value := $resultEnv }}
- name: {{ $key | quote }}
  value: {{ $value | quote }}
{{- end -}}
{{- end -}}
{{- end -}}

{{- define "element-io.element-call-sfu.env" }}
{{- $root := .root -}}
{{- with required "element-io.sfu-jwt missing context" .context -}}
{{- $resultEnv := dict -}}
{{- range $envEntry := .extraEnv -}}
{{- $_ := set $resultEnv $envEntry.name $envEntry.value -}}
{{- end -}}
{{- end -}}
{{- end -}}
