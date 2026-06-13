/* Admin panel interactivity */
(function() {
  'use strict';

  // Toast system
  function toast(msg, type = 'info') {
    const container = document.querySelector('.toast-container');
    if (!container) return;
    const el = document.createElement('div');
    el.className = `toast ${type}`;
    el.textContent = msg;
    container.appendChild(el);
    setTimeout(() => { el.style.opacity = '0'; el.style.transition = 'opacity .3s'; setTimeout(() => el.remove(), 300); }, 3000);
  }

  // Fetch wrapper
  async function api(url, opts = {}) {
    const resp = await fetch(url, {
      headers: { 'Accept': 'application/json', ...(opts.body ? { 'Content-Type': 'application/json' } : {}) },
      ...opts,
    });
    const data = await resp.json();
    if (!resp.ok) throw new Error(data.error || resp.statusText);
    return data;
  }

  // --- Gallery page ---
  const galleryGrid = document.getElementById('gallery-grid');
  const filterForm = document.getElementById('gallery-filters');
  if (galleryGrid && filterForm) {
    let debounceTimer;
    function loadGallery() {
      const params = new URLSearchParams();
      ['type', 'pillar', 'source', 'section', 'status', 'q'].forEach(k => {
        const el = filterForm.elements[k];
        if (el && el.value) params.set(k, el.value);
      });
      const url = `/admin/api/images?${params}`;
      galleryGrid.innerHTML = '<div class="empty-state"><div class="spinner" style="margin:0 auto 12px"></div><p>Loading...</p></div>';
      api(url).then(data => {
        if (!data.images || data.images.length === 0) {
          galleryGrid.innerHTML = '<div class="empty-state"><div class="empty-icon">🖼</div><p>No images found</p></div>';
          return;
        }
        galleryGrid.innerHTML = data.images.map(img => {
          let badges = '';
          if (img.source) badges += `<span class="badge badge-source">${img.source}</span>`;
          if (img.width && img.height) badges += `<span class="badge badge-score">${img.width}×${img.height}</span>`;
          if (img.used_by && img.used_by.length > 0) badges += `<span class="badge badge-used">${img.used_by.length} used</span>`;
          else badges += `<span class="badge badge-orphan">orphan</span>`;
          const thumbUrl = img.url.replace('/static/', '/static/');
          return `<div class="gallery-item" onclick="window.location='/admin/image/${encodeURIComponent(img.path)}'">
            <div class="thumb-wrap"><img src="${thumbUrl}" alt="${img.filename}" loading="lazy"></div>
            <div class="gallery-info">
              <div class="filename" title="${img.filename}">${img.filename}</div>
              <div class="meta">${badges}</div>
            </div>
          </div>`;
        }).join('');
      }).catch(err => {
        galleryGrid.innerHTML = `<div class="empty-state"><p class="error">Error: ${err.message}</p></div>`;
      });
    }
    filterForm.addEventListener('input', () => {
      clearTimeout(debounceTimer);
      debounceTimer = setTimeout(loadGallery, 250);
    });
    filterForm.addEventListener('change', loadGallery);
    loadGallery();
  }

  // --- Article detail image picker ---
  function initImagePicker() {
    document.querySelectorAll('[data-pick-image]').forEach(btn => {
      btn.addEventListener('click', function() {
        const slug = this.dataset.articleSlug;
        const sectionIdx = this.dataset.sectionIndex;
        const role = this.dataset.role || 'section';
        openImagePicker(slug, sectionIdx, role);
      });
    });
  }
  initImagePicker();

  function openImagePicker(slug, sectionIdx, role) {
    const overlay = document.getElementById('image-picker-modal');
    if (!overlay) return;
    overlay.classList.add('open');
    const body = overlay.querySelector('.modal-body');
    body.innerHTML = '<div class="empty-state"><div class="spinner" style="margin:0 auto 12px"></div><p>Loading gallery...</p></div>';

    const params = new URLSearchParams();
    if (role !== 'featured') params.set('section', sectionIdx);
    api(`/admin/api/images?${params}`).then(data => {
      if (!data.images || data.images.length === 0) {
        body.innerHTML = '<div class="empty-state"><p>No images available</p></div>';
        return;
      }
      body.innerHTML = `<div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:10px">
        ${data.images.map(img => `
          <div class="suggest-item" data-path="${img.path}">
            <img src="${img.url}" alt="${img.filename}" loading="lazy">
            <div class="suggest-score">
              <span>${img.filename}</span>
            </div>
          </div>
        `).join('')}
      </div>`;
      body.querySelectorAll('.suggest-item').forEach(el => {
        el.addEventListener('click', function() {
          const path = this.dataset.path;
          assignImage(slug, sectionIdx, role, path, body);
        });
      });
    }).catch(err => {
      body.innerHTML = `<div class="empty-state"><p>Error: ${err.message}</p></div>`;
    });

    overlay.querySelector('.modal-close').onclick = () => overlay.classList.remove('open');
    overlay.addEventListener('click', e => { if (e.target === overlay) overlay.classList.remove('open'); });
  }

  async function assignImage(slug, sectionIdx, role, path, bodyEl) {
    const btn = bodyEl.querySelector('.suggest-item.selected') || bodyEl.querySelector('[data-path="' + path + '"]');
    if (btn) btn.classList.add('selected');
    try {
      const endpoint = role === 'featured'
        ? `/admin/api/article/${slug}/set-featured`
        : `/admin/api/article/${slug}/assign-section-image`;
      const result = await api(endpoint, {
        method: 'POST',
        body: JSON.stringify({ image_path: path, section_index: parseInt(sectionIdx) }),
      });
      toast('Image assigned successfully', 'success');
      document.getElementById('image-picker-modal').classList.remove('open');
      // Reload the page to show updated state
      setTimeout(() => location.reload(), 500);
    } catch (err) {
      toast(err.message, 'error');
    }
  }

  // --- Smart Suggest ---
  document.querySelectorAll('[data-suggest]').forEach(btn => {
    btn.addEventListener('click', async function() {
      const slug = this.dataset.articleSlug;
      const sectionIdx = this.dataset.sectionIndex;
      const resultEl = document.getElementById(`suggest-${slug}-${sectionIdx}`);
      if (!resultEl) return;
      resultEl.innerHTML = '<div class="empty-state"><div class="spinner" style="margin:0 auto 8px"></div><p>Searching backends...</p></div>';
      resultEl.style.display = 'block';
      try {
        const data = await api(`/admin/api/article/${slug}/suggest`, {
          method: 'POST',
          body: JSON.stringify({ section_index: parseInt(sectionIdx) }),
        });
        if (!data.candidates || data.candidates.length === 0) {
          resultEl.innerHTML = '<p style="color:var(--admin-text-secondary);font-size:13px">No candidates found from backends.</p>';
          return;
        }
        resultEl.innerHTML = `<div style="margin-bottom:6px;font-size:12px;color:var(--admin-text-secondary)">Top ${data.candidates.length} candidates from backends. Click one to assign:</div>
          <div class="suggest-grid">
            ${data.candidates.map(c => `
              <div class="suggest-item" data-url="${c.url}" data-source="${c.source}" data-score="${c.score}">
                <img src="${c.thumbnail || c.url}" alt="" loading="lazy">
                <div class="suggest-score">
                  <span>${c.score}</span>
                  <span>${c.source}</span>
                </div>
              </div>
            `).join('')}
          </div>`;
        resultEl.querySelectorAll('.suggest-item').forEach(el => {
          el.addEventListener('click', async function() {
            resultEl.querySelectorAll('.suggest-item').forEach(x => x.classList.remove('selected'));
            this.classList.add('selected');
            // Download and assign
            try {
              const assignResult = await api(`/admin/api/article/${slug}/assign-section-image`, {
                method: 'POST',
                body: JSON.stringify({
                  section_index: parseInt(sectionIdx),
                  external_url: this.dataset.url,
                  source: this.dataset.source,
                  score: parseFloat(this.dataset.score),
                }),
              });
              toast('Image fetched and assigned!', 'success');
              setTimeout(() => location.reload(), 600);
            } catch (err) {
              toast(err.message, 'error');
            }
          });
        });
      } catch (err) {
        resultEl.innerHTML = `<p style="color:var(--admin-danger);font-size:13px">Error: ${err.message}</p>`;
      }
    });
  });

  // --- Remove image ---
  document.querySelectorAll('[data-remove-image]').forEach(btn => {
    btn.addEventListener('click', async function() {
      if (!confirm('Remove this image?')) return;
      const slug = this.dataset.articleSlug;
      const sectionIdx = this.dataset.sectionIndex;
      const role = this.dataset.role || 'section';
      try {
        const endpoint = role === 'featured'
          ? `/admin/api/article/${slug}/remove-featured`
          : `/admin/api/article/${slug}/remove-section-image`;
        await api(endpoint, {
          method: 'POST',
          body: JSON.stringify({ section_index: parseInt(sectionIdx) }),
        });
        toast('Image removed', 'info');
        setTimeout(() => location.reload(), 500);
      } catch (err) {
        toast(err.message, 'error');
      }
    });
  });

  // --- Manifest editor ---
  const manifestForm = document.getElementById('manifest-form');
  if (manifestForm) {
    manifestForm.addEventListener('submit', async function(e) {
      e.preventDefault();
      const formData = new FormData(this);
      const data = { slug: formData.get('slug'), section_index: parseInt(formData.get('section_index')), image_url: formData.get('image_url') };
      try {
        await api('/admin/api/manifest', { method: 'POST', body: JSON.stringify(data) });
        toast('Manifest entry saved', 'success');
        setTimeout(() => location.reload(), 500);
      } catch (err) {
        toast(err.message, 'error');
      }
    });
    document.querySelectorAll('[data-delete-manifest]').forEach(btn => {
      btn.addEventListener('click', async function() {
        if (!confirm('Delete this manifest entry?')) return;
        const slug = this.dataset.slug;
        try {
          await api(`/admin/api/manifest/${slug}`, { method: 'DELETE' });
          toast('Manifest entry deleted', 'info');
          setTimeout(() => location.reload(), 500);
        } catch (err) {
          toast(err.message, 'error');
        }
      });
    });
  }

  // --- Curated tester ---
  const curatedForm = document.getElementById('curated-test-form');
  if (curatedForm) {
    curatedForm.addEventListener('submit', async function(e) {
      e.preventDefault();
      const formData = new FormData(this);
      const data = {};
      formData.forEach((v, k) => data[k] = v);
      const resultsEl = document.getElementById('curated-results');
      resultsEl.innerHTML = '<div class="spinner" style="margin:0 auto"></div>';
      try {
        const result = await api('/admin/api/curated-test', { method: 'POST', body: JSON.stringify(data) });
        resultsEl.innerHTML = '';
        if (result.matches && result.matches.length > 0) {
          result.matches.forEach(m => {
            const div = document.createElement('div');
            div.className = 'match-result match';
            div.innerHTML = `<div class="phrase">${m.phrase}</div><div class="filename">${m.filename}</div><div class="match-status">Matched in: ${m.matched_in}</div>`;
            resultsEl.appendChild(div);
          });
        } else {
          resultsEl.innerHTML = '<div class="match-result no-match"><div class="phrase">No curated matches found</div></div>';
        }
      } catch (err) {
        resultsEl.innerHTML = `<p style="color:var(--admin-danger)">${err.message}</p>`;
      }
    });
  }

  // --- Re-fetch section ---
  document.querySelectorAll('[data-refetch]').forEach(btn => {
    btn.addEventListener('click', async function() {
      if (!confirm('Re-fetch image for this section? This will search backends again.')) return;
      const slug = this.dataset.articleSlug;
      const sectionIdx = this.dataset.sectionIndex;
      try {
        await api(`/admin/api/article/${slug}/re-fetch-section`, {
          method: 'POST',
          body: JSON.stringify({ section_index: parseInt(sectionIdx) }),
        });
        toast('Re-fetch complete', 'success');
        setTimeout(() => location.reload(), 800);
      } catch (err) {
        toast(err.message, 'error');
      }
    });
  });
})();
