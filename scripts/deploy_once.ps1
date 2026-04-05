param(
    [Parameter(Mandatory = $true)]
    [string]$ProjectId,
    [string]$Region = "us-central1",
    [string]$BackendService,
    [string]$FrontendService,
    [string]$FirestoreCollection = "items"
)

$ErrorActionPreference = "Stop"
$gcloud = "C:\Users\luisa\AppData\Local\Google\Cloud SDK\google-cloud-sdk\bin\gcloud.cmd"

& $gcloud config set project $ProjectId

& $gcloud builds submit --config cloudbuild.yaml --substitutions="_REGION=$Region,_BACKEND_SERVICE=$BackendService,_FRONTEND_SERVICE=$FrontendService,_FIRESTORE_COLLECTION=$FirestoreCollection"

$backendUrl = & $gcloud run services describe $BackendService --region $Region --format="value(status.url)"
$frontendUrl = & $gcloud run services describe $FrontendService --region $Region --format="value(status.url)"

Write-Output "BACKEND_URL=$backendUrl"
Write-Output "FRONTEND_URL=$frontendUrl"
