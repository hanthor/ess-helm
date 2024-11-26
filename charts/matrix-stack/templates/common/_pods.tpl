# Copyright 2024 New Vector Ltd
#
# SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-Element-Commercial

{{- define "element-io.ess-library.pods.pullSecrets" -}}
{{- $ := index . 0 }}
{{- with index . 1 }}
{{- $pullSecrets := concat .pullSecrets $.Values.global.ess.imagePullSecrets }}
{{- with ($pullSecrets | uniq) }}
imagePullSecrets:
{{ toYaml . }}
{{- end }}
{{- end }}
{{- end }}
