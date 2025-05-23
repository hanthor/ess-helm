{{- /*
Copyright 2024 New Vector Ltd

SPDX-License-Identifier: AGPL-3.0-only
*/ -}}

{{- define "element-io.ess-library.serviceAccountName" -}}
{{- $root := .root -}}
{{- with required "element-io.ess-library.serviceAccountName missing context" .context -}}
{{ default (printf "%s-%s" $root.Release.Name (required "element-io.ess-library.serviceAccountName missing context.key" .key)) .serviceAccount.name }}
{{- end }}
{{- end }}

{{- define "element-io.ess-library.serviceAccount" -}}
{{- $root := .root -}}
{{- with required "element-io.ess-library.serviceAccount missing context" .context -}}
{{- $key := required "element-io.ess-library.serviceAccount missing context.key" .key -}}
{{- $extraAnnotations := .extraAnnotations | default dict -}}
{{- with required "element-io.ess-library.serviceAccount missing context.componentValues" .componentValues -}}
{{- if .serviceAccount.create }}
apiVersion: v1
kind: ServiceAccount
metadata:
  {{- with (merge dict .serviceAccount.annotations $extraAnnotations) }}
  annotations:
    {{- toYaml . | nindent 4 }}
  {{- end }}
  labels:
    {{- include (printf "element-io.%s.labels" $key) (dict "root" $root "context" .) | nindent 4 }}
  name: {{ include "element-io.ess-library.serviceAccountName" (dict "root" $root "context" (dict "serviceAccount" .serviceAccount "key" $key)) }}
  namespace: {{ $root.Release.Namespace }}
automountServiceAccountToken: false
{{- end }}
{{- end }}
{{- end }}
{{- end }}
