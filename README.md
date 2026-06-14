# htmx-demo

A small personal photo site. A Go server renders HTML pages and HTMX fragments;
the photo gallery loads images straight from a public Google Cloud Storage bucket
in the browser. Deployed to Google Cloud Run.

- **Backend:** Go, standard-library `net/http` ([tutorial](https://freshman.tech/web-development-with-go/))
- **Frontend:** [HTMX](https://htmx.org/examples) + `html/template`
- **Photos:** public GCS bucket `chasedv-photos`, fetched client-side
- **Hosting:** Google Cloud Run

## Running locally

The app listens on the port in `.env` (`PORT=6969`).

```sh
# Go directly
go run .

# or with live reload
air

# or in Docker (Compose builds the image automatically)
docker compose up --build
docker compose down
```

Then open http://localhost:6969.

## Deploying

From the project root:

```sh
gcloud run deploy --source .
# choose region: us-central1
```

## Project layout

```
main.go                     entrypoint: loads .env, starts the ServeMux
router/
  router.go                 routes and page/fragment handlers
  middleware.go             request logging + panic recovery
requests/
  request_handler.go        navbar helper (active-link state)
views/                      full-page templates (index, spain, uk)
components/                 HTMX fragments (navbar)
assets/
  gallery.js                shared gallery renderer (loadGallery(folder))
  ...                       images served at /assets
styles/                     stylesheets served at /styles
scripts/
  upload_gallery.py         generate thumbnails + upload a gallery to GCS
architecture.drawio         architecture diagram (regenerate via build_diagram.py)
```

### Routes

| Path        | Purpose                                       |
|-------------|-----------------------------------------------|
| `/`         | Home page                                     |
| `/spain`    | Photo gallery — `spain` folder                |
| `/uk`       | Photo gallery — `ukrazy` folder               |
| `/navbar`   | Navbar fragment (loaded via HTMX)             |
| `/assets/`  | Static assets (incl. `gallery.js`)            |
| `/styles/`  | Stylesheets                                   |

### Galleries

Each gallery page calls `loadGallery(folder)` from `assets/gallery.js`, which lists
the bucket scoped to that folder and renders thumbnails. The bucket convention is:
full-size images under `<folder>/` and thumbnails under `<folder>-thumbs/` — a thumb
links to its full-size image (same name with `-thumbs` stripped).

**Adding / populating a gallery.** Generate thumbnails and upload both sets with:

```sh
pip install -r scripts/requirements.txt          # Pillow, once
python scripts/upload_gallery.py <folder> <local-dir-of-jpegs>
# e.g. python scripts/upload_gallery.py ukrazy ~/Desktop/ukrazy_photos
# --no-upload to only build thumbnails, --dry-run to preview the gcloud commands
```

It writes 256px (longest-side) EXIF-rotated thumbnails and uploads full-size to
`<folder>/` and thumbnails to `<folder>-thumbs/`. Requires an authenticated
`gcloud`; the bucket must grant public read (allUsers → Storage Object Viewer).
Then wire up the page: add a view that calls `loadGallery('<folder>')`, register a
route in `router/router.go`, and add a navbar link in `components/navbar.html`.

## Roadmap

- **Photo uploads.** When this lands, reintroduce Supabase (auth + storage) and
  move config (URLs, keys) into `.env`; add `HttpOnly`/`Secure`/`SameSite` flags
  to the session cookie.
- Consider restructuring the Go packages once the app grows
  ([Ben Johnson style](https://medium.com/sellerapp/golang-project-structuring-ben-johnson-way-2a11035f94bc)).
