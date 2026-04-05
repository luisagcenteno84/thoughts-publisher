param(
    [Parameter(Mandatory = $true)]
    [string]$ProjectId,
    [string]$Region = "us-central1",
    [string]$ArtifactRepo = "app-images"
)

$ErrorActionPreference = "Stop"
$gcloud = "C:\Users\luisa\AppData\Local\Google\Cloud SDK\google-cloud-sdk\bin\gcloud.cmd"

if (-not (Test-Path $gcloud)) {
    throw "gcloud CLI not found at $gcloud"
}

$projectExists = $false
try {
    & $gcloud projects describe $ProjectId --format="value(projectId)" *> $null
    if ($LASTEXITCODE -eq 0) {
        $projectExists = $true
    }
} catch {
    $projectExists = $false
}

if (-not $projectExists) {
    try {
        & $gcloud projects create $ProjectId --name $ProjectId
    } catch {
        throw "Failed to create project '$ProjectId'. It may be unavailable or require billing/org permissions."
    }
}

& $gcloud config set project $ProjectId

& $gcloud services enable run.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com firestore.googleapis.com secretmanager.googleapis.com iam.googleapis.com cloudresourcemanager.googleapis.com

$repoExists = & $gcloud artifacts repositories list --location $Region --filter="name~$ArtifactRepo" --format="value(name)"
if (-not $repoExists) {
    & $gcloud artifacts repositories create $ArtifactRepo --repository-format=docker --location=$Region --description="Container images"
}

$firestore = & $gcloud firestore databases list --format="value(name)"
if (-not $firestore) {
    & $gcloud firestore databases create --location=$Region --type=firestore-native
}

Write-Output "Bootstrap complete for project $ProjectId"
