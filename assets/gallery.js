// Shared photo-gallery renderer. Each gallery page calls loadGallery(folder),
// where `folder` is a top-level folder in the GCS bucket. Full-size images live
// under `<folder>/` and thumbnails under `<folder>-thumbs/`; clicking a thumb
// opens its full-size image (same name with `-thumbs` stripped).
const BUCKET = 'chasedv-photos';

function loadGallery(folder, columnCount = 4) {
  const gallery = document.getElementById('gallery');

  function showMessage(text) {
    gallery.innerHTML = `<p class="paragraph">${text}</p>`;
  }

  async function fetchPhotos() {
    let data;
    try {
      const prefix = encodeURIComponent(`${folder}-thumbs/`);
      const url = `https://storage.googleapis.com/storage/v1/b/${BUCKET}/o?prefix=${prefix}`;
      const response = await fetch(url);
      if (!response.ok) {
        throw new Error(`bucket request failed: ${response.status}`);
      }
      data = await response.json();
    } catch (err) {
      console.error('failed to load photos', err);
      showMessage('Could not load photos right now. Please try again later.');
      return;
    }

    const thumbnails = ((data && data.items) || [])
      .filter(item => item && item.contentType === 'image/jpeg');
    if (thumbnails.length === 0) {
      showMessage('No photos yet.');
      return;
    }

    for (let i = 0; i < columnCount; i++) {
      const column = document.createElement('div');
      column.className = 'column';
      column.id = `column${i + 1}`;
      gallery.appendChild(column);
    }

    let imageCount = 0;
    function recursiveRender(index) {
      if (index >= thumbnails.length) return;
      const thumbnail = thumbnails[index];
      const fullName = thumbnail.name.replace('-thumbs', '');
      const a = document.createElement('a');
      a.href = `https://storage.googleapis.com/${BUCKET}/${fullName}`;
      a.target = '_blank';
      const img = document.createElement('img');
      img.src = `https://storage.googleapis.com/${BUCKET}/${thumbnail.name}`;
      img.alt = thumbnail.name;
      img.loading = 'lazy';
      // chain the next render off this image so we don't slam the network
      img.onload = () => recursiveRender(index + 1);
      img.onerror = () => recursiveRender(index + 1);
      const column = document.getElementById(`column${(imageCount % columnCount) + 1}`);
      a.appendChild(img);
      column.appendChild(a);
      imageCount++;
    }
    recursiveRender(0);
  }

  fetchPhotos();
}
