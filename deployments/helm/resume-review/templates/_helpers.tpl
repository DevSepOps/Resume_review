{{- define "rr.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{/* Release-scoped base name; Services are <fullname>-backend / -frontend / -db (contract). */}}
{{- define "rr.fullname" -}}
{{- if .Values.fullnameOverride -}}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" -}}
{{- else if contains .Chart.Name .Release.Name -}}
{{- .Release.Name | trunc 63 | trimSuffix "-" -}}
{{- else -}}
{{- printf "%s-%s" .Release.Name .Chart.Name | trunc 63 | trimSuffix "-" -}}
{{- end -}}
{{- end -}}

{{/* Contract: Service name is <release>-backend. */}}
{{- define "rr.backendName" -}}{{ printf "%s-backend" .Release.Name | trunc 63 | trimSuffix "-" }}{{- end -}}
{{- define "rr.frontendName" -}}{{ printf "%s-frontend" .Release.Name | trunc 63 | trimSuffix "-" }}{{- end -}}
{{- define "rr.dbName" -}}{{ printf "%s-db" .Release.Name | trunc 63 | trimSuffix "-" }}{{- end -}}

{{- define "rr.labels" -}}
helm.sh/chart: {{ printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
app.kubernetes.io/name: {{ include "rr.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end -}}

{{/* call with (dict "ctx" . "component" "backend") */}}
{{- define "rr.selectorLabels" -}}
app.kubernetes.io/name: {{ include "rr.name" .ctx }}
app.kubernetes.io/instance: {{ .ctx.Release.Name }}
app.kubernetes.io/component: {{ .component }}
{{- end -}}

{{/* call with (dict "ctx" . "image" .Values.backend.image) */}}
{{- define "rr.image" -}}
{{- $tag := default (default .ctx.Chart.AppVersion .ctx.Values.global.imageTag) .image.tag -}}
{{- if eq $tag "latest" -}}{{- fail "image tag 'latest' is not allowed; set global.imageTag to a sha-xxxxxxx or vX.Y.Z tag" -}}{{- end -}}
{{- printf "%s/%s:%s" .ctx.Values.global.imageRegistry .image.repository $tag -}}
{{- end -}}

{{- define "rr.secretName" -}}
{{- if .Values.secrets.create -}}{{ include "rr.fullname" . }}{{- else -}}{{ required "secrets.existingSecret is required when secrets.create=false" .Values.secrets.existingSecret }}{{- end -}}
{{- end -}}

{{- define "rr.pullSecrets" -}}
{{- with .Values.global.imagePullSecrets }}
imagePullSecrets:
{{- toYaml . | nindent 2 }}
{{- end }}
{{- end -}}

{{/* Fails early on invalid combinations. */}}
{{- define "rr.validate" -}}
{{- if and (gt (int .Values.backend.replicas) 1) (ne .Values.uploads.accessMode "ReadWriteMany") -}}
{{- fail "backend.replicas > 1 needs shared uploads storage: set uploads.accessMode=ReadWriteMany (and an RWX uploads.storageClass), or keep backend.replicas=1" -}}
{{- end -}}
{{- if and (not .Values.secrets.create) (not .Values.secrets.existingSecret) -}}
{{- fail "secrets.create=false requires secrets.existingSecret" -}}
{{- end -}}
{{- end -}}

{{/* Wait-for-database init container (used by the migrations Job). */}}
{{- define "rr.waitForDb" -}}
- name: wait-for-db
  image: {{ .Values.db.image.repository }}:{{ .Values.db.image.tag }}
  command: ["sh", "-c", "until pg_isready -h {{ include "rr.dbName" . }} -p 5432 -U healthcheck -t 3; do echo waiting for db; sleep 3; done"]
  securityContext:
    {{- toYaml .Values.securityContext | nindent 4 }}
  resources:
    requests: {cpu: 10m, memory: 16Mi}
    limits: {memory: 64Mi}
{{- end -}}
