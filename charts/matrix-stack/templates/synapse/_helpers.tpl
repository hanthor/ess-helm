# Copyright 2024 New Vector Ltd
#
# SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-Element-Commercial

{{- define "element-io.synapse.labels" -}}
{{ include "element-io.ess-library.labels.common" (list $ .Values.synapse.labels) }}
app.kubernetes.io/component: matrix-server
app.kubernetes.io/name: synapse
app.kubernetes.io/instance: {{ .Release.Name }}-synapse
app.kubernetes.io/version: {{ .Values.synapse.image.tag | default $.Chart.AppVersion }}
k8s.element.io/synapse-instance: {{ .Release.Name }}-synapse
{{- end }}

{{- define "element-io.synapse.process.labels" -}}
{{ include "element-io.ess-library.labels.common" (list $ .Values.synapse.labels) }}
app.kubernetes.io/component: matrix-server
app.kubernetes.io/name: synapse-{{ .ProcessType }}
app.kubernetes.io/instance: {{ .Release.Name }}-synapse-{{ .ProcessType }}
app.kubernetes.io/version: {{ .Values.synapse.image.tag | default $.Chart.AppVersion }}
k8s.element.io/synapse-instance: {{ .Release.Name }}-synapse
{{- end }}

{{- define "element-io.synapse.redis.labels" -}}
{{ include "element-io.ess-library.labels.common" (list $ .Values.synapse.redis.labels) }}
app.kubernetes.io/part-of: matrix-stack
app.kubernetes.io/component: matrix-server-pubsub
app.kubernetes.io/name: synapse-redis
app.kubernetes.io/instance: {{ .Release.Name }}-synapse-redis
app.kubernetes.io/version: {{ .Values.synapse.redis.image.tag }}
{{- end }}

{{- define "element-io.synapse.haproxy.labels" -}}
{{ include "element-io.ess-library.labels.common" (list $ .Values.synapse.haproxy.labels) }}
app.kubernetes.io/part-of: matrix-stack
app.kubernetes.io/component: matrix-server-ingress
app.kubernetes.io/name: synapse-haproxy
app.kubernetes.io/instance: {{ .Release.Name }}-synapse-haproxy
app.kubernetes.io/version: {{ .Values.synapse.haproxy.image.tag }}
{{- end }}

{{- define "element-io.synapse.serviceAccountName" -}}
{{ default (printf "%s-synapse" .Release.Name ) .Values.synapse.serviceAccount.name }}
{{- end }}

{{- define "element-io.synapse.redis.serviceAccountName" -}}
{{ default (printf "%s-synapse-redis" .Release.Name ) .Values.synapse.redis.serviceAccount.name }}
{{- end }}

{{- define "element-io.synapse.haproxy.serviceAccountName" -}}
{{ default (printf "%s-synapse-haproxy" .Release.Name ) .Values.synapse.haproxy.serviceAccount.name }}
{{- end }}

{{- define "element-io.synapse.enabledWorkers" -}}
{{ $enabledWorkers := dict }}
{{- range $workerType, $workerDetails := .Values.synapse.workers }}
{{- if $workerDetails.enabled }}
{{ $_ := set $enabledWorkers $workerType $workerDetails }}
{{- end }}
{{- end }}
{{ $enabledWorkers | toJson }}
{{- end }}

{{- define "element-io.synapse.pvcName" -}}
{{- if .Values.synapse.media.storage.existingClaim -}}
{{ .Values.synapse.media.storage.existingClaim }}
{{- else -}}
{{ .Release.Name }}-synapse-media
{{- end -}}
{{- end }}
