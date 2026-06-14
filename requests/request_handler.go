package requestHandler

import (
	"net/http"
	"net/url"
)

type Navbar struct {
	Referer string `json:"referer"`
}

// GetNavbarForRequest extracts the path of the referer so the active nav link
// can be highlighted. Parsing with net/url keeps this working in any
// environment (localhost, Cloud Run, etc.) rather than a hardcoded host.
func GetNavbarForRequest(r *http.Request) Navbar {
	referer := r.Referer()
	if u, err := url.Parse(referer); err == nil {
		referer = u.Path
	}

	return Navbar{
		Referer: referer,
	}
}
