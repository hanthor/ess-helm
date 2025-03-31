{{- /*
Copyright 2024 New Vector Ltd

SPDX-License-Identifier: AGPL-3.0-only
*/ -}}

{{- $root := .root -}}
{{- with required "element-call/sfu/config.yaml.tpl missing context" .context -}}

port: 7880
# WebRTC configuration
rtc:
  tcp_port: {{ .exposedServices.rtcTcp.port }}
  udp_port: {{ .exposedServices.rtcUdp.port }}
{{ if .exposedServices.rtcMuxedUdp.enabled }}
  port_range_start: {{ .exposedServices.rtcMuxedUdp.portRange.startPort }}
  port_range_end: {{ .exposedServices.rtcMuxedUdp.portRange.endPort }}
{{ end }}
{{ if .useExternalIp }}
  use_external_ip: true
{{- else }}
  use_external_ip: false
  # To workaround https://github.com/livekit/livekit/issues/2088
  # Any IP address is acceptable, it doesn't need to be a correct one,
  # it just needs to be present to get LiveKit to skip checking all local interfaces
  # We assign here a TEST-NET IP which is
  # overridden by the NODE_IP env var at runtime
  node_ip: 198.51.100.1
{{- end }}
{{- with .stunServers }}
  stun_servers:
  {{ . | toYaml | nindent 4 }}
{{- end }}

prometheus_port: 6789

key_file: keys.yaml

# Logging config
logging:
  # log level, valid values: debug, info, warn, error
  level: {{ .logging.level }}
  # log level for pion, default error
  pion_level: {{ .logging.pionLevel }}
  # when set to true, emit json fields
  json: {{ .logging.json }}

# Signal Relay is enabled by default as of v1.5.3

# turn server
turn:
  enabled: false

{{ end }}
