// Admin panel JavaScript - static site version
// No API calls - all data is pre-rendered in templates

// Sidebar toggle
function toggleSidebar() {
    const sidebar = document.getElementById('sidebar');
    sidebar.classList.toggle('open');
}

// Close sidebar when clicking outside
document.addEventListener('click', (e) => {
    const sidebar = document.getElementById('sidebar');
    const toggle = document.getElementById('sidebar-toggle');
    if (!sidebar.classList.contains('open')) return;
    if (!sidebar.contains(e.target) && !toggle.contains(e.target)) {
        sidebar.classList.remove('open');
    }
});

// Close sidebar on Escape key
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        document.getElementById('sidebar').classList.remove('open');
    }
});

// Gallery - static version (no API)
// The gallery data is already rendered in the template
// This file provides basic UI functionality

// Tag editor modal
function openTagModal(path) {
    document.getElementById('tag-path').value = path;
    document.getElementById('tag-filename').textContent = 'Filename: ' + path.split('/').pop();
    document.getElementById('tag-modal').style.display = 'flex';
}

function closeTagModal() {
    document.getElementById('tag-modal').style.display = 'none';
}

function addTag() {
    const tagInput = document.getElementById('tag-input');
    const tagList = document.getElementById('tag-list');
    const tag = tagInput.value.trim();
    
    if (tag && !tagList.querySelector(`[data-tag="${tag}"]`)) {
        const tagEl = document.createElement('span');
        tagEl.className = 'tag';
        tagEl.dataset.tag = tag;
        tagEl.innerHTML = `${tag} <button type="button">&times;</button>`;
        tagEl.querySelector('button').onclick = () => tagEl.remove();
        tagList.appendChild(tagEl);
        tagInput.value = '';
    }
}

// Close modal on click outside
document.getElementById('tag-modal').addEventListener('click', (e) => {
    if (e.target.id === 'tag-modal') closeTagModal();
});

// Image picker modal
function openImagePicker(callback) {
    const modal = document.getElementById('image-picker-modal');
    const body = modal.querySelector('.modal-body');
    body.innerHTML = '<div class="empty-state"><p>Loading...</p></div>';
    modal.style.display = 'flex';
}

function closeImagePicker() {
    document.getElementById('image-picker-modal').style.display = 'none';
}

// Close modal on click outside
document.getElementById('image-picker-modal').addEventListener('click', (e) => {
    if (e.target.id === 'image-picker-modal') closeImagePicker();
});

// Toast notifications
function showToast(message, type = 'info') {
    const container = document.querySelector('.toast-container');
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;
    container.appendChild(toast);
    setTimeout(() => toast.remove(), 3000);
}

// Gallery pagination (static - no API)
let currentGalleryPage = 1;
const GALLERY_ITEMS_PER_PAGE = 60;

function galleryPrev() {
    if (currentGalleryPage > 1) {
        currentGalleryPage--;
        renderGalleryPage();
    }
}

function galleryNext() {
    const totalPages = Math.ceil(galleryTotalItems / GALLERY_ITEMS_PER_PAGE);
    if (currentGalleryPage < totalPages) {
        currentGalleryPage++;
        renderGalleryPage();
    }
}

function renderGalleryPage() {
    const grid = document.getElementById('gallery-grid');
    const pagination = document.getElementById('gallery-pagination');
    const pageInfo = document.getElementById('page-info');
    
    const totalPages = Math.ceil(galleryTotalItems / GALLERY_ITEMS_PER_PAGE);
    
    // Update pagination
    pagination.style.display = totalPages > 1 ? 'flex' : 'none';
    pageInfo.textContent = `Page ${currentGalleryPage} of ${totalPages}`;
    
    // Update buttons
    document.getElementById('page-prev').disabled = currentGalleryPage === 1;
    document.getElementById('page-next').disabled = currentGalleryPage === totalPages;
    
    // Render current page items
    const start = (currentGalleryPage - 1) * GALLERY_ITEMS_PER_PAGE;
    const end = Math.min(start + GALLERY_ITEMS_PER_PAGE, galleryTotalItems);
    
    grid.innerHTML = '<div class="empty-state"><div class="spinner" style="margin:0 auto 12px"></div><p>Loading gallery...</p></div>';
    
    // In a real app, we'd fetch paginated data here
    // For now, show a message
    setTimeout(() => {
        grid.innerHTML = `
            <div class="empty-state" style="text-align:center;padding:40px">
                <p>Gallery loading...</p>
                <p style="font-size:13px;color:var(--admin-text-secondary)">In a production environment, this would fetch from /admin/api/images</p>
            </div>
        `;
    }, 100);
}

// Gallery data - populated from template
let galleryTotalItems = {{ stats_total_images }} || 0;
