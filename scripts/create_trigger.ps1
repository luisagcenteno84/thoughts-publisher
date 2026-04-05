param(
    [Parameter(Mandatory = $true)]
    [string]$ProjectId,
    [Parameter(Mandatory = $true)]
    [string]$GithubOwner,
    [Parameter(Mandatory = $true)]
    [string]$RepoName,
    [Parameter(Mandatory = $true)]
    [string]$TriggerName,
    [string]$BranchPattern = "^main$"
)

$ErrorActionPreference = "Stop"
$gcloud = "C:\Users\luisa\AppData\Local\Google\Cloud SDK\google-cloud-sdk\bin\gcloud.cmd"

& $gcloud config set project $ProjectId

$existing = & $gcloud builds triggers list --format="value(name)" --filter="name=$TriggerName"
if ($existing) {
    Write-Output "Trigger already exists: $TriggerName"
    exit 0
}

& $gcloud builds triggers create github `
  --name=$TriggerName `
  --repo-owner=$GithubOwner `
  --repo-name=$RepoName `
  --branch-pattern=$BranchPattern `
  --build-config=cloudbuild.yaml

Write-Output "Created trigger $TriggerName"
