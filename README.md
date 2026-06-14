# htmx-demo

A small personal photo site. A Go server renders HTML pages and HTMX fragments;
the photo gallery loads images straight from a public Google Cloud Storage bucket
in the browser. Deployed to Google Cloud Run.

- **Backend:** Go (1.25), standard-library `net/http` ([tutorial](https://freshman.tech/web-development-with-go/))
- **Frontend:** [HTMX](https://htmx.org/examples) + `html/template`
- **Photos:** public GCS bucket `chasedv-photos`, fetched client-side
- **Uploads:** `/upload` — basic-auth page that generates thumbnails server-side and writes to the bucket
- **Hosting:** Google Cloud Run (service `htmxdemo`, region `us-central1`)

## Running locally

The app listens on the port in `.env` (`PORT=6969`). `.env` is **not committed**
(it holds the upload secret) — create it locally:

```sh
PORT=6969
UPLOAD_USER=chase            # only needed to use /upload locally
UPLOAD_SECRET=some-password  # the route returns 503 until both are set
```

```sh
# Go directly
go run .

# or with live reload
air

# or in Docker (Compose reads .env and builds the image automatically)
docker compose up --build
docker compose down
```

Then open http://localhost:6969. To exercise `/upload` locally you also need a
service-account key at `secrets/gcs-key.json` (see `secrets/README.md`); without
it the form loads but submitting returns "Storage is not configured".

## Deploying

Deploys to the `htmxdemo` Cloud Run service from the project root. The service
runs *as* the `gallery-uploader` service account (so GCS uploads use keyless
[ADC](https://cloud.google.com/docs/authentication/application-default-credentials),
no JSON key in the image), and the basic-auth creds come from Secret Manager:

```sh
gcloud run deploy htmxdemo --source . --region=us-central1 --allow-unauthenticated \
  --service-account=gallery-uploader@website-test-400716.iam.gserviceaccount.com \
  --set-secrets=UPLOAD_USER=upload-user:latest,UPLOAD_SECRET=upload-secret:latest
```

`.dockerignore` keeps `.env` and `secrets/` out of the image. `PORT` needs no
flag — Cloud Run injects it (8080) and `godotenv` won't override an already-set var.

**One-time setup** (service account, bucket access, secrets):

```sh
gcloud services enable run.googleapis.com cloudbuild.googleapis.com \
  artifactregistry.googleapis.com secretmanager.googleapis.com

gcloud iam service-accounts create gallery-uploader --display-name="Gallery uploader"
gcloud storage buckets add-iam-policy-binding gs://chasedv-photos \
  --member="serviceAccount:gallery-uploader@website-test-400716.iam.gserviceaccount.com" \
  --role="roles/storage.objectAdmin"

printf 'chase'    | gcloud secrets create upload-user   --data-file=-
printf 'a-secret' | gcloud secrets create upload-secret --data-file=-
gcloud secrets add-iam-policy-binding upload-user   --member="serviceAccount:gallery-uploader@website-test-400716.iam.gserviceaccount.com" --role="roles/secretmanager.secretAccessor"
gcloud secrets add-iam-policy-binding upload-secret --member="serviceAccount:gallery-uploader@website-test-400716.iam.gserviceaccount.com" --role="roles/secretmanager.secretAccessor"
```

## Project layout

```
main.go                     entrypoint: loads .env, starts the ServeMux
router/
  router.go                 routes and page/fragment handlers
  middleware.go             request logging + panic recovery
  upload.go                 /upload: basic-auth gate, thumbnail gen, GCS write
requests/
  request_handler.go        navbar helper (active-link state)
views/                      full-page templates (index, spain, uk, upload)
components/                 HTMX fragments (navbar)
assets/
  gallery.js                shared gallery renderer (loadGallery(folder))
  ...                       images served at /assets
styles/                     stylesheets served at /styles
scripts/
  upload_gallery.py         generate thumbnails + upload a gallery to GCS (CLI)
secrets/                    gitignored; local GCS key + secrets/README.md
.dockerignore               keeps .env / secrets out of the built image
architecture.drawio         architecture diagram (regenerate via build_diagram.py)
```

### Routes

| Path        | Purpose                                       |
|-------------|-----------------------------------------------|
| `/`         | Home page                                     |
| `/spain`    | Photo gallery — `spain` folder                |
| `/uk`       | Photo gallery — `uk` folder                   |
| `/upload`   | Upload page (basic-auth) — thumbnails + GCS   |
| `/navbar`   | Navbar fragment (loaded via HTMX)             |
| `/assets/`  | Static assets (incl. `gallery.js`)            |
| `/styles/`  | Stylesheets                                   |

### Galleries

Each gallery page calls `loadGallery(folder)` from `assets/gallery.js`, which lists
the bucket scoped to that folder and renders thumbnails. The bucket convention is:
full-size images under `<folder>/` and thumbnails under `<folder>-thumbs/` — a thumb
links to its full-size image (same name with `-thumbs` stripped).

**Adding / populating a gallery.** Two ways, both writing 256px (longest-side)
EXIF-rotated thumbnails to `<folder>-thumbs/` and full-size to `<folder>/`:

- **Web UI** — visit `/upload`, log in (basic auth), pick a gallery name and JPEGs.
  `router/upload.go` does the resize and bucket write server-side. Best for adding
  photos to a gallery that already has a page.
- **CLI** — bulk-upload a local folder:

  ```sh
  pip install -r scripts/requirements.txt          # Pillow, once
  python scripts/upload_gallery.py <folder> <local-dir-of-jpegs>
  # e.g. python scripts/upload_gallery.py uk ~/Desktop/uk_photos
  # --no-upload to only build thumbnails, --dry-run to preview the gcloud commands
  ```

  Requires an authenticated `gcloud`; the bucket must grant public read
  (allUsers → Storage Object Viewer).

**New gallery page.** Add a view that calls `loadGallery('<folder>')`, register a
route in `router/router.go`, and add a navbar link in `components/navbar.html`.

## Roadmap

- **Harden `/upload`.** Basic auth over a single shared secret is the minimum;
  consider per-user accounts or a real session/login if more people upload.
- **Auto-wire new galleries.** Uploading to a new folder still needs a hand-added
  page + route + navbar link; could be data-driven instead.
- Consider restructuring the Go packages once the app grows
  ([Ben Johnson style](https://medium.com/sellerapp/golang-project-structuring-ben-johnson-way-2a11035f94bc)).
