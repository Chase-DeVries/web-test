package requestHandler

import (
	"bytes"
	"context"
	"crypto/subtle"
	"fmt"
	"html/template"
	"image/jpeg"
	"log"
	"net/http"
	"os"
	"path"
	"strings"
	"time"

	"cloud.google.com/go/storage"
	"github.com/disintegration/imaging"
)

// Upload mirrors the convention used by scripts/upload_gallery.py and gallery.js:
// full-size images live under "<folder>/" and 256px thumbnails under
// "<folder>-thumbs/", sharing the same filename, served as image/jpeg.
const (
	uploadBucket    = "chasedv-photos"
	thumbMaxLength  = 256
	thumbJPEGQual   = 85
	maxUploadMemory = 32 << 20 // 32MB kept in memory; larger multipart spills to temp files
)

// requireBasicAuth gates a handler behind the UPLOAD_USER / UPLOAD_SECRET env
// vars. Uses constant-time comparison so the gate doesn't leak timing. If either
// var is unset the route is disabled (503) rather than left wide open.
func requireBasicAuth(next http.HandlerFunc) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		wantUser := os.Getenv("UPLOAD_USER")
		wantPass := os.Getenv("UPLOAD_SECRET")
		if wantUser == "" || wantPass == "" {
			http.Error(w, "Upload is not configured", http.StatusServiceUnavailable)
			return
		}
		user, pass, ok := r.BasicAuth()
		userOK := subtle.ConstantTimeCompare([]byte(user), []byte(wantUser)) == 1
		passOK := subtle.ConstantTimeCompare([]byte(pass), []byte(wantPass)) == 1
		if !ok || !userOK || !passOK {
			w.Header().Set("WWW-Authenticate", `Basic realm="upload"`)
			http.Error(w, "Unauthorized", http.StatusUnauthorized)
			return
		}
		next(w, r)
	}
}

// uploadForm serves the photo-picker page (GET /upload).
func uploadForm(w http.ResponseWriter, r *http.Request) {
	tpl := template.Must(template.ParseFiles("views/upload.html"))
	tpl.Execute(w, nil)
}

// uploadSubmit handles POST /upload: for each picked JPEG it uploads the
// original to "<folder>/" and a generated thumbnail to "<folder>-thumbs/".
func uploadSubmit(w http.ResponseWriter, r *http.Request) {
	if err := r.ParseMultipartForm(maxUploadMemory); err != nil {
		http.Error(w, "Could not parse upload: "+err.Error(), http.StatusBadRequest)
		return
	}

	folder := sanitizeFolder(r.FormValue("folder"))
	if folder == "" {
		http.Error(w, "A gallery name is required (letters, numbers, dashes).", http.StatusBadRequest)
		return
	}

	files := r.MultipartForm.File["photos"]
	if len(files) == 0 {
		http.Error(w, "No photos were selected.", http.StatusBadRequest)
		return
	}

	ctx, cancel := context.WithTimeout(r.Context(), 5*time.Minute)
	defer cancel()

	client, err := storage.NewClient(ctx)
	if err != nil {
		log.Printf("upload: storage client: %v", err)
		http.Error(w, "Storage is not configured on the server.", http.StatusInternalServerError)
		return
	}
	defer client.Close()
	bucket := client.Bucket(uploadBucket)

	var uploaded, skipped int
	var failures []string
	for _, fh := range files {
		name := path.Base(fh.Filename)
		if !isJPEG(name) {
			skipped++
			failures = append(failures, name+" (not a .jpg)")
			continue
		}

		f, err := fh.Open()
		if err != nil {
			failures = append(failures, name+" (could not read)")
			continue
		}
		img, err := imaging.Decode(f, imaging.AutoOrientation(true)) // honor EXIF orientation, like Pillow's exif_transpose
		f.Close()
		if err != nil {
			failures = append(failures, name+" (not a valid image)")
			continue
		}

		// Re-encode the original so EXIF rotation is baked in and the content
		// type is a clean image/jpeg, matching what gallery.js filters on.
		var fullBuf bytes.Buffer
		if err := jpeg.Encode(&fullBuf, img, &jpeg.Options{Quality: thumbJPEGQual}); err != nil {
			failures = append(failures, name+" (encode failed)")
			continue
		}

		thumb := imaging.Fit(img, thumbMaxLength, thumbMaxLength, imaging.Lanczos)
		var thumbBuf bytes.Buffer
		if err := jpeg.Encode(&thumbBuf, thumb, &jpeg.Options{Quality: thumbJPEGQual}); err != nil {
			failures = append(failures, name+" (thumbnail failed)")
			continue
		}

		fullObj := fmt.Sprintf("%s/%s", folder, name)
		thumbObj := fmt.Sprintf("%s-thumbs/%s", folder, name)
		if err := writeObject(ctx, bucket, fullObj, fullBuf.Bytes()); err != nil {
			failures = append(failures, name+" (upload failed)")
			log.Printf("upload: %s: %v", fullObj, err)
			continue
		}
		if err := writeObject(ctx, bucket, thumbObj, thumbBuf.Bytes()); err != nil {
			failures = append(failures, name+" (thumbnail upload failed)")
			log.Printf("upload: %s: %v", thumbObj, err)
			continue
		}
		uploaded++
	}

	w.Header().Set("Content-Type", "text/html; charset=utf-8")
	fmt.Fprintf(w, `<p class="paragraph">Uploaded %d photo(s) to <strong>%s</strong>.`, uploaded, template.HTMLEscapeString(folder))
	if skipped+len(failures) > 0 {
		fmt.Fprintf(w, ` Skipped %d: %s.`, len(failures), template.HTMLEscapeString(strings.Join(failures, ", ")))
	}
	fmt.Fprint(w, `</p>`)
}

// writeObject uploads bytes as a public-readable image/jpeg object.
func writeObject(ctx context.Context, bucket *storage.BucketHandle, object string, data []byte) error {
	wc := bucket.Object(object).NewWriter(ctx)
	wc.ContentType = "image/jpeg"
	if _, err := wc.Write(data); err != nil {
		wc.Close()
		return err
	}
	return wc.Close()
}

// sanitizeFolder keeps only the safe characters a gallery name can contain, so a
// form value can't escape into another bucket prefix.
func sanitizeFolder(s string) string {
	s = strings.TrimSpace(strings.ToLower(s))
	var b strings.Builder
	for _, r := range s {
		if (r >= 'a' && r <= 'z') || (r >= '0' && r <= '9') || r == '-' {
			b.WriteRune(r)
		}
	}
	return strings.Trim(b.String(), "-")
}

func isJPEG(name string) bool {
	ext := strings.ToLower(path.Ext(name))
	return ext == ".jpg" || ext == ".jpeg"
}
