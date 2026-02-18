/**
 * Seminars App - Main JavaScript
 */

// Get token from URL or cookie
function getToken() {
    const params = new URLSearchParams(window.location.search);
    return params.get('token') || getCookie('token');
}

function getCookie(name) {
    const match = document.cookie.match(new RegExp('(^| )' + name + '=([^;]+)'));
    return match ? match[2] : null;
}

function setCookie(name, value, days) {
    const expires = new Date(Date.now() + days * 864e5).toUTCString();
    document.cookie = name + '=' + encodeURIComponent(value) + '; expires=' + expires + '; path=/';
}

// API client
const API_BASE = '/api';

async function api(endpoint, options = {}) {
    const token = getToken();
    const url = `${API_BASE}${endpoint}${endpoint.includes('?') ? '&' : '?'}token=${token}`;
    
    const res = await fetch(url, {
        ...options,
        headers: {
            'Content-Type': 'application/json',
            ...options.headers
        }
    });
    
    if (res.status === 401) {
        // Redirect to login
        window.location.href = 'https://inacio-auth.fly.dev/login?returnTo=' + encodeURIComponent(window.location.href);
        return;
    }
    
    if (!res.ok) {
        throw new Error(`API error: ${res.status}`);
    }
    
    return res.json();
}

// Store token from URL if present
const urlToken = new URLSearchParams(window.location.search).get('token');
if (urlToken) {
    setCookie('token', urlToken, 30);
    // Clean URL
    window.history.replaceState({}, '', window.location.pathname);
}

// Load seminars
async function loadSeminars() {
    const container = document.getElementById('seminars-list');
    if (!container) return;
    
    try {
        const seminars = await api('/seminars?upcoming=true');
        
        if (seminars.length === 0) {
            container.innerHTML = '<p>No upcoming seminars.</p>';
            return;
        }
        
        container.innerHTML = seminars.map(s => `
            <div class="seminar-card">
                <div class="seminar-date">${formatDate(s.date)} at ${s.start_time}</div>
                <h3>${escapeHtml(s.title)}</h3>
                <p class="speaker">${escapeHtml(s.speaker?.name || 'TBD')} ${s.speaker?.affiliation ? `(${escapeHtml(s.speaker.affiliation)})` : ''}</p>
                <p class="room">📍 ${escapeHtml(s.room?.name || 'TBD')}</p>
                ${s.abstract ? `<p class="abstract">${escapeHtml(s.abstract.substring(0, 200))}${s.abstract.length > 200 ? '...' : ''}</p>` : ''}
                <div class="tasks">
                    ${!s.room_booked ? '<span class="badge warning">Room needed</span>' : ''}
                    ${!s.announcement_sent ? '<span class="badge warning">Announcement needed</span>' : ''}
                    ${!s.calendar_invite_sent ? '<span class="badge warning">Calendar needed</span>' : ''}
                </div>
                <div class="actions">
                    <button onclick="editSeminar(${s.id})">Edit</button>
                    <button onclick="deleteSeminar(${s.id})" class="danger">Delete</button>
                </div>
            </div>
        `).join('');
    } catch (err) {
        container.innerHTML = `<p class="error">Error loading seminars: ${err.message}</p>`;
    }
}

// Load speakers
async function loadSpeakers() {
    const container = document.getElementById('speakers-list');
    if (!container) return;
    
    try {
        const speakers = await api('/speakers');
        
        if (speakers.length === 0) {
            container.innerHTML = '<p>No speakers added yet.</p>';
            return;
        }
        
        container.innerHTML = speakers.map(s => `
            <div class="speaker-card">
                <h4>${escapeHtml(s.name)}</h4>
                ${s.affiliation ? `<p>${escapeHtml(s.affiliation)}</p>` : ''}
                ${s.email ? `<p>📧 ${escapeHtml(s.email)}</p>` : ''}
            </div>
        `).join('');
    } catch (err) {
        container.innerHTML = `<p class="error">Error loading speakers: ${err.message}</p>`;
    }
}

// Create seminar
async function createSeminar(data) {
    return api('/seminars', {
        method: 'POST',
        body: JSON.stringify(data)
    });
}

// Create speaker
async function createSpeaker(data) {
    return api('/speakers', {
        method: 'POST',
        body: JSON.stringify(data)
    });
}

// Delete seminar
async function deleteSeminar(id) {
    if (!confirm('Delete this seminar?')) return;
    
    await api(`/seminars/${id}`, { method: 'DELETE' });
    loadSeminars();
}

// Edit seminar (placeholder)
function editSeminar(id) {
    alert('Edit functionality coming soon! ID: ' + id);
}

// Helpers
function formatDate(dateStr) {
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    loadSeminars();
    loadSpeakers();
});
