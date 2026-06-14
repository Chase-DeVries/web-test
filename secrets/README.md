# secrets/

This folder is gitignored. Put runtime credentials here; they are mounted
read-only into the container at `/run/secrets/`.

## gcs-key.json

The service-account key used by the `/upload` route to write to the
`chasedv-photos` bucket. Create it once:

```sh
# a dedicated service account with write access to the bucket
gcloud iam service-accounts create gallery-uploader \
  --display-name="Gallery uploader"

gcloud storage buckets add-iam-policy-binding gs://chasedv-photos \
  --member="serviceAccount:gallery-uploader@$(gcloud config get-value project).iam.gserviceaccount.com" \
  --role="roles/storage.objectAdmin"

gcloud iam service-accounts keys create secrets/gcs-key.json \
  --iam-account="gallery-uploader@$(gcloud config get-value project).iam.gserviceaccount.com"
```

`compose.yml` points `GOOGLE_APPLICATION_CREDENTIALS` at `/run/secrets/gcs-key.json`.

## Basic-auth credentials

Set `UPLOAD_USER` and `UPLOAD_SECRET` in your environment or a `.env` file next
to `compose.yml`. The `/upload` route returns 503 until both are set.
