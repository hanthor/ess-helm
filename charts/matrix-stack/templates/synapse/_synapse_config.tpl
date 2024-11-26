# Copyright 2024 New Vector Ltd
#
# SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-Element-Commercial

{{- define "element-io.synapse.config.shared-underrides" -}}
report_stats: false

require_auth_for_profile_requests: true
{{ end }}

{{- define "element-io.synapse.config.shared-overrides" -}}
public_baseurl: https://{{ .Values.synapse.ingress.host }}
serverName: {{ required "Synapse requires ess.serverName set" .Values.ess.serverName }}
signing_key_path: /secrets/{{ .Values.synapse.signingKey.secret | default (printf "%s-synapse" .Release.Name) }}/{{ .Values.synapse.signingKey.secretKey | default "SIGNING_KEY" }}
enable_metrics: true
log_config: "/conf/log_config.yaml"
macaroon_secret_key: ${SYNAPSE_MACAROON}
registration_shared_secret: ${SYNAPSE_REGISTRATION_SHARED_SECRET}

database:
  name: psycopg2
  args:
    user: {{ .Values.synapse.postgres.user }}
    password: ${SYNAPSE_POSTGRES_PASSWORD}
    database: {{ .Values.synapse.postgres.database }}
    host: {{ .Values.synapse.postgres.host }}
    port: {{ .Values.synapse.postgres.port }}

    application_name: ${APPLICATION_NAME}
    sslmode: {{ .Values.synapse.postgres.sslMode }}
    keepalives: 1
    keepalives_idle: 10
    keepalives_interval: 10
    keepalives_count: 3

# The default as of 1.27.0
ip_range_blacklist:
- '127.0.0.0/8'
- '10.0.0.0/8'
- '172.16.0.0/12'
- '192.168.0.0/16'
- '100.64.0.0/10'
- '192.0.0.0/24'
- '169.254.0.0/16'
- '192.88.99.0/24'
- '198.18.0.0/15'
- '192.0.2.0/24'
- '198.51.100.0/24'
- '203.0.113.0/24'
- '224.0.0.0/4'
- '::1/128'
- 'fe80::/10'
- 'fc00::/7'
- '2001:db8::/32'
- 'ff00::/8'
- 'fec0::/10'

{{- if dig "appservice" "enabled" false .Values.synapse.workers }}

notify_appservices_from_worker: appservice-0
{{- end }}

{{- with .Values.synapse.appservices }}
app_service_config_files:
{{- range $appservice := . }}
 - /as/{{ .registrationFileConfigMapName }}/registration.yaml
{{- end }}
{{- end }}

{{- if dig "background" "enabled" false .Values.synapse.workers }}

run_background_tasks_on: background-0
{{- end }}

{{- if dig "federation-sender" "enabled" false .Values.synapse.workers }}

send_federation: false
federation_sender_instances:
{{- range $index := untilStep 0 ((index .Values.synapse.workers "federation-sender").instances | int) 1 }}
- federation-sender-{{ $index }}
{{- end }}
{{- else }}

send_federation: true
{{- end }}

# This is still required despite media_storage_providers as otherwise Synapse attempts to mkdir /media_store
media_store_path: "/media/media_store"
{{- if dig "media-repository" "enabled" false .Values.synapse.workers }}
media_instance_running_background_jobs: "media-repository-0"
{{- end }}

presence:
  enabled: {{ dig "presence-writer" "enabled" false .Values.synapse.workers }}

{{- if dig "pusher" "enabled" false .Values.synapse.workers }}

start_pushers: false
pusher_instances:
{{- range $index := untilStep 0 ((index .Values.synapse.workers "pusher").instances | int) 1 }}
- pusher-{{ $index }}
{{- end }}
{{- else }}

start_pushers: true
{{- end }}

{{- if dig "user-dir" "enabled" false .Values.synapse.workers }}

update_user_directory_from_worker: user-dir-0
{{- end }}
{{- $enabledWorkers := (include "element-io.synapse.enabledWorkers" .) | fromJson }}

instance_map:
  main:
    host: {{ .Release.Name }}-synapse-main.{{ .Release.Namespace }}.svc.cluster.local.
    port: 9093
{{- range $workerType, $workerDetails := $enabledWorkers }}
{{- if include "element-io.synapse.process.hasReplication" $workerType }}
{{- range $index := untilStep 0 ($workerDetails.instances | int | default 1) 1 }}
  {{ $workerType }}-{{ $index }}:
    host: {{ .Release.Name }}-synapse-{{ $workerType }}-{{ $index }}.{{ .Release.Name }}-synapse-{{ $workerType }}.{{ .Release.Namespace }}.svc.cluster.local.
    port: 9093
{{- end }}
{{- end }}
{{- end }}

{{- if $enabledWorkers }}

redis:
  enabled: true
  host: "{{ .Release.Name }}-synapse-redis.{{ .Release.Namespace }}.svc.cluster.local"
{{- if include "element-io.synapse.streamWriterWorkers" $ | fromJsonArray }}

stream_writers:
{{- range $workerType, $workerDetails := $enabledWorkers }}
{{- if include "element-io.synapse.process.streamWriters" $workerType | fromJsonArray }}
{{- range $stream_writer := include "element-io.synapse.process.streamWriters" $workerType | fromJsonArray }}
  {{ $stream_writer }}:
{{- range $index := untilStep 0 ($workerDetails.instances | int | default 1) 1 }}
  - {{ $workerType }}-{{ $index }}
{{- end }}
{{- end }}
{{- end }}
{{- end }}
{{- end }}
{{- end }}

{{ end }}


{{- define "element-io.synapse.config.processSpecific" -}}
worker_app: {{ include "element-io.synapse.process.app" .processType }}

{{- if eq .processType "main" }}
listeners:
{{- else }}
worker_name: ${APPLICATION_NAME}

worker_listeners:
{{- end }}
{{- if (include "element-io.synapse.process.hasHttp" .processType) }}
- port: 8008
  tls: false
  bind_addresses: ['0.0.0.0']
  type: http
  x_forwarded: true
  resources:
  - names:
    - client
    - federation
{{- /* main always loads this if client or federation is set. media-repo workers need it explicitly set.... */}}
{{- if eq .processType "media-repository" }}
    - media
{{- end }}
    compress: false
{{- end }}
{{- if (include "element-io.synapse.process.hasReplication" .processType) }}
- port: 9093
  tls: false
  bind_addresses: ['0.0.0.0']
  type: http
  x_forwarded: false
  resources:
  - names: [replication]
    compress: false
{{- end }}
- type: metrics
  port: 9001
  bind_addresses: ['0.0.0.0']
{{- /* Unfortunately the metrics type doesn't get the health endpoint*/}}
- port: 8080
  tls: false
  bind_addresses: ['0.0.0.0']
  type: http
  x_forwarded: false
  resources:
  - names: []
    compress: false

{{- $enabledWorkers := (include "element-io.synapse.enabledWorkers" .context) | fromJson }}
{{- if (include "element-io.synapse.process.responsibleForMedia" (dict "processType" .processType "enabledWorkerTypes" (keys $enabledWorkers))) }}
enable_media_repo: true
{{- else }}
# Stub out the media storage provider for processes not responsible for media
media_storage_providers:
- module: file_system
  store_local: false
  store_remote: false
  store_synchronous: false
  config:
    directory: "/media/media_store"
{{- end }}
{{ end }}
