"""
External speaker availability page - redesigned from scratch.
- Always updatable (loads existing data, auto-saves on change)
- Same input method as internal: calendar with click, shift-click for ranges, quick actions
- Data format consistent with internal: { date, preference } per date
"""

from app.templates import get_external_header_with_logos


def get_availability_page_html(speaker_name, speaker_email, speaker_affiliation, suggested_topic, semester_plan, token, semester_start=None, semester_end=None):
    """Generate the external availability page with calendar UX matching internal form."""
    if not semester_start:
        semester_start = "2025-01-01"
    if not semester_end:
        semester_end = "2025-06-30"

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Submit Availability - University of Macau</title>
    <style>
        :root {{
            --primary: #003366;
            --primary-light: #0066CC;
            --accent: #FFD700;
            --success: #28a745;
            --error: #dc3545;
            --warning: #ffc107;
            --gray-100: #f8f9fa;
            --gray-200: #e9ecef;
            --gray-300: #dee2e6;
            --gray-600: #6c757d;
            --gray-800: #343a40;
        }}
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            min-height: 100vh;
            line-height: 1.6;
        }}
        .header {{
            background: var(--primary);
            color: white;
            padding: 24px 20px;
            text-align: center;
        }}
        .header-logos {{
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 12px;
        }}
        .header-logos-inner {{
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 24px;
            flex-wrap: wrap;
        }}
        .header .logo-wrap {{
            background: white;
            padding: 16px 28px;
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.15);
        }}
        .header .logo {{
            height: 72px;
            width: auto;
            object-fit: contain;
            display: block;
        }}
        .header .logo-um {{ max-height: 80px; }}
        .header .logo-econ {{ max-height: 72px; }}
        .header h1 {{ font-size: 26px; font-weight: 600; margin: 0; }}
        .header .subtitle {{ font-size: 15px; opacity: 0.9; margin-top: 6px; }}
        .container {{ max-width: 800px; margin: 0 auto; padding: 20px; }}
        .card {{
            background: white;
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            margin-bottom: 20px;
            overflow: hidden;
        }}
        .card-header {{
            background: linear-gradient(135deg, var(--primary) 0%, var(--primary-light) 100%);
            color: white;
            padding: 20px 24px;
        }}
        .card-body {{ padding: 24px; }}
        .info-banner {{
            background: rgba(0,102,204,0.08);
            border-left: 4px solid var(--primary);
            padding: 16px 20px;
            margin-bottom: 24px;
            border-radius: 0 8px 8px 0;
        }}
        .info-row {{ display: flex; margin-bottom: 6px; }}
        .info-label {{ width: 100px; font-weight: 500; color: var(--gray-600); }}
        .info-value {{ flex: 1; color: var(--gray-800); }}
        .saving-indicator {{
            position: fixed;
            top: 20px;
            right: 20px;
            background: var(--success);
            color: white;
            padding: 10px 18px;
            border-radius: 8px;
            font-size: 14px;
            opacity: 0;
            transition: opacity 0.3s;
            pointer-events: none;
            z-index: 1000;
            box-shadow: 0 2px 8px rgba(0,0,0,0.15);
        }}
        .saving-indicator.show {{ opacity: 1; }}
        .saving-indicator.saving {{ background: var(--warning); color: var(--gray-800); }}
        .saving-indicator.error {{ background: var(--error); }}
        .section {{ margin-bottom: 24px; }}
        .section-title {{ font-size: 18px; font-weight: 600; color: var(--gray-800); margin-bottom: 12px; }}
        .section-hint {{ font-size: 13px; color: var(--gray-600); margin-bottom: 12px; }}
        .calendar-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 12px;
        }}
        .calendar-header h3 {{ font-size: 18px; color: var(--gray-800); }}
        .calendar-nav {{
            display: flex;
            gap: 8px;
        }}
        .calendar-nav button {{
            padding: 8px 14px;
            background: var(--primary);
            color: white;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            font-size: 14px;
        }}
        .calendar-nav button:hover {{ background: var(--primary-light); }}
        .weekdays {{
            display: grid;
            grid-template-columns: repeat(7, 1fr);
            gap: 4px;
            margin-bottom: 8px;
        }}
        .weekday {{ text-align: center; font-size: 12px; font-weight: 600; color: var(--gray-600); }}
        .calendar-grid {{
            display: grid;
            grid-template-columns: repeat(7, 1fr);
            gap: 4px;
        }}
        .cal-day {{
            aspect-ratio: 1;
            display: flex;
            align-items: center;
            justify-content: center;
            border-radius: 8px;
            cursor: pointer;
            font-size: 14px;
            transition: all 0.15s;
        }}
        .cal-day.selected {{
            background: var(--primary);
            color: white;
            font-weight: 600;
        }}
        .cal-day.selected.range-mid {{ border-radius: 0; }}
        .cal-day.selected.range-start {{ border-top-right-radius: 0; border-bottom-right-radius: 0; }}
        .cal-day.selected.range-end {{ border-top-left-radius: 0; border-bottom-left-radius: 0; }}
        .cal-day:not(.selected):not(.disabled):hover {{ background: #e3f2fd; }}
        .cal-day.disabled {{ color: #ccc; cursor: not-allowed; background: var(--gray-100); }}
        .cal-day.other-month {{ color: #999; }}
        .selected-summary {{
            margin-top: 16px;
            padding: 16px;
            background: #e8f5e9;
            border: 1px solid #4caf50;
            border-radius: 8px;
        }}
        .selected-summary-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
        }}
        .selected-summary-title {{ font-weight: 600; color: #2e7d32; }}
        .clear-btn {{
            padding: 6px 12px;
            background: #f44336;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 12px;
        }}
        .clear-btn:hover {{ background: #d32f2f; }}
        .date-chips {{ display: flex; flex-wrap: wrap; gap: 8px; max-height: 120px; overflow-y: auto; }}
        .date-chip {{
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 6px 12px;
            background: var(--primary);
            color: white;
            border-radius: 20px;
            font-size: 13px;
        }}
        .date-chip .remove {{ cursor: pointer; font-weight: bold; opacity: 0.9; }}
        .date-chip .remove:hover {{ opacity: 1; }}
        .form-row {{ display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-top: 20px; }}
        @media (max-width: 600px) {{ .form-row {{ grid-template-columns: 1fr; }} }}
        .form-group {{ margin-bottom: 16px; }}
        .form-label {{ display: block; margin-bottom: 6px; font-weight: 500; color: var(--gray-800); }}
        .form-input {{ width: 100%; padding: 12px; border: 2px solid var(--gray-300); border-radius: 6px; font-size: 16px; }}
        .form-input:focus {{ outline: none; border-color: var(--primary-light); }}
        .footer-note {{
            text-align: center;
            color: var(--gray-600);
            font-size: 14px;
            margin-top: 24px;
            padding: 16px;
            background: rgba(0,102,204,0.05);
            border-radius: 8px;
        }}
    </style>
</head>
<body>
    <div id="savingIndicator" class="saving-indicator">💾 Saving...</div>

    <div class="header">
        {get_external_header_with_logos()}
    </div>

    <div class="container">
        <div class="card">
            <div class="card-header">
                <h2>📅 Submit Your Availability</h2>
                <p style="margin-top: 6px; opacity: 0.9;">Select dates when you are available. Changes are saved automatically.</p>
            </div>

            <div class="card-body">
                <div class="info-banner">
                    <div class="info-row"><span class="info-label">Name:</span><span class="info-value">{speaker_name}</span></div>
                    <div class="info-row"><span class="info-label">Email:</span><span class="info-value">{speaker_email or 'N/A'}</span></div>
                    <div class="info-row"><span class="info-label">Affiliation:</span><span class="info-value">{speaker_affiliation or 'N/A'}</span></div>
                    <div class="info-row"><span class="info-label">Topic:</span><span class="info-value">{suggested_topic or 'TBD'}</span></div>
                    <div class="info-row"><span class="info-label">Semester:</span><span class="info-value">{semester_plan or 'TBD'}</span></div>
                </div>

                <div class="section">
                    <h3 class="section-title">Select Available Dates</h3>
                    <p class="section-hint">Click dates to select. Hold Shift and click to select a range.</p>

                    <div class="calendar-header">
                        <h3 id="currentMonth">January 2025</h3>
                        <div class="calendar-nav">
                            <button type="button" id="prevMonth">&lt; Prev</button>
                            <button type="button" id="nextMonth">Next &gt;</button>
                        </div>
                    </div>

                    <div class="weekdays">
                        <span class="weekday">Sun</span><span class="weekday">Mon</span><span class="weekday">Tue</span>
                        <span class="weekday">Wed</span><span class="weekday">Thu</span><span class="weekday">Fri</span><span class="weekday">Sat</span>
                    </div>
                    <div class="calendar-grid" id="calendarGrid"></div>

                    <div class="selected-summary" id="selectedSummary" style="display: none;">
                        <div class="selected-summary-header">
                            <span class="selected-summary-title">✓ Selected Dates (<span id="selectedCount">0</span>)</span>
                            <button type="button" class="clear-btn" id="clearAllBtn">Clear All</button>
                        </div>
                        <div class="date-chips" id="dateChips"></div>
                    </div>
                </div>

                <div class="footer-note">
                    💾 All changes are saved automatically. You can return anytime to update your availability.
                </div>
            </div>
        </div>
    </div>

    <script>
        const TOKEN = '{token}';
        const API_BASE = '/api/v1/seminars/speaker-tokens';
        const SEMESTER_START = new Date('{semester_start}');
        const SEMESTER_END = new Date('{semester_end}');

        const monthNames = ['January','February','March','April','May','June','July','August','September','October','November','December'];
        const weekDays = ['Sun','Mon','Tue','Wed','Thu','Fri','Sat'];

        let currentMonth = new Date(SEMESTER_START);
        let selectedDates = new Set();
        let lastSelectedDate = null;
        let isShiftPressed = false;
        let saveTimeout = null;

        function formatDate(d) {{
            const y = d.getFullYear();
            const m = String(d.getMonth() + 1).padStart(2, '0');
            const day = String(d.getDate()).padStart(2, '0');
            return `${{y}}-${{m}}-${{day}}`;
        }}

        function parseDateStr(s) {{
            const [y, m, d] = s.split('-').map(Number);
            return new Date(y, m - 1, d);
        }}

        function isInSemester(d) {{
            const t = d.getTime();
            return t >= SEMESTER_START.getTime() && t <= SEMESTER_END.getTime();
        }}

        function eachDay(start, end) {{
            const days = [];
            const cur = new Date(start);
            while (cur <= end) {{
                days.push(new Date(cur));
                cur.setDate(cur.getDate() + 1);
            }}
            return days;
        }}

        async function loadData() {{
            try {{
                const res = await fetch(`${{API_BASE}}/${{TOKEN}}/availability`);
                if (!res.ok) return;
                const data = await res.json();
                selectedDates.clear();
                (data.availability || []).forEach(a => {{
                    if (a.date) selectedDates.add(a.date);
                }});
                updateDisplay();
                renderCalendar();
            }} catch (e) {{ console.error('Load failed:', e); }}
        }}

        function scheduleSave() {{
            clearTimeout(saveTimeout);
            saveTimeout = setTimeout(saveToServer, 600);
        }}

        async function saveToServer() {{
            const indicator = document.getElementById('savingIndicator');
            indicator.textContent = '💾 Saving...';
            indicator.className = 'saving-indicator saving show';

            const sorted = Array.from(selectedDates).sort();
            const availabilities = sorted.map(d => ({{ date: d, preference: 'available' }}));

            try {{
                const res = await fetch(`${{API_BASE}}/${{TOKEN}}/submit-availability`, {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{ availabilities }})
                }});

                if (res.ok) {{
                    indicator.textContent = '✓ Saved';
                    indicator.className = 'saving-indicator show';
                    setTimeout(() => indicator.classList.remove('show'), 1500);
                }} else {{
                    const err = await res.text();
                    indicator.textContent = '✗ Error';
                    indicator.className = 'saving-indicator error show';
                    console.error('Save failed:', err);
                }}
            }} catch (e) {{
                indicator.textContent = '✗ Error';
                indicator.className = 'saving-indicator error show';
                console.error('Save error:', e);
            }}
        }}

        function toggleDate(dateStr) {{
            if (!isInSemester(parseDateStr(dateStr))) return;
            if (selectedDates.has(dateStr)) {{
                selectedDates.delete(dateStr);
            }} else {{
                selectedDates.add(dateStr);
            }}
            lastSelectedDate = parseDateStr(dateStr);
            updateDisplay();
            renderCalendar();
            scheduleSave();
        }}

        function toggleDateWithShift(dateStr) {{
            const d = parseDateStr(dateStr);
            if (!isInSemester(d)) return;

            if (isShiftPressed && lastSelectedDate) {{
                const start = lastSelectedDate < d ? lastSelectedDate : d;
                const end = lastSelectedDate < d ? d : lastSelectedDate;
                eachDay(start, end).forEach(day => {{
                    if (isInSemester(day)) selectedDates.add(formatDate(day));
                }});
                lastSelectedDate = d;
            }} else if (selectedDates.has(dateStr)) {{
                selectedDates.delete(dateStr);
                lastSelectedDate = null;
            }} else {{
                selectedDates.add(dateStr);
                lastSelectedDate = d;
            }}
            updateDisplay();
            renderCalendar();
            scheduleSave();
        }}

        function clearAll() {{
            if (selectedDates.size === 0) return;
            if (!confirm('Clear all ' + selectedDates.size + ' selected dates?')) return;
            selectedDates.clear();
            lastSelectedDate = null;
            updateDisplay();
            renderCalendar();
            scheduleSave();
        }}

        function removeDate(dateStr) {{
            selectedDates.delete(dateStr);
            updateDisplay();
            renderCalendar();
            scheduleSave();
        }}

        function removeRange(startStr, endStr) {{
            const start = parseDateStr(startStr);
            const end = parseDateStr(endStr);
            eachDay(start, end).forEach(day => selectedDates.delete(formatDate(day)));
            updateDisplay();
            renderCalendar();
            scheduleSave();
        }}

        function updateDisplay() {{
            const summary = document.getElementById('selectedSummary');
            const countEl = document.getElementById('selectedCount');
            const chipsEl = document.getElementById('dateChips');

            const sorted = Array.from(selectedDates).sort();
            if (sorted.length === 0) {{
                summary.style.display = 'none';
                return;
            }}

            summary.style.display = 'block';
            countEl.textContent = sorted.length;

            const groups = [];
            let cur = [sorted[0]];
            for (let i = 1; i < sorted.length; i++) {{
                const prev = parseDateStr(sorted[i-1]);
                const curr = parseDateStr(sorted[i]);
                if ((curr - prev) / 86400000 === 1) cur.push(sorted[i]);
                else {{ groups.push(cur); cur = [sorted[i]]; }}
            }}
            groups.push(cur);

            chipsEl.innerHTML = groups.map(g => {{
                if (g.length === 1) {{
                    const d = parseDateStr(g[0]);
                    const fmt = d.toLocaleDateString('en-US', {{ weekday: 'short', month: 'short', day: 'numeric' }});
                    return `<span class="date-chip">${{fmt}} <span class="remove" onclick="removeDate('${{g[0]}}')">×</span></span>`;
                }} else {{
                    const s = parseDateStr(g[0]);
                    const e = parseDateStr(g[g.length-1]);
                    const fmt = `${{s.toLocaleDateString('en-US',{{month:'short',day:'numeric'}})}} - ${{e.toLocaleDateString('en-US',{{month:'short',day:'numeric'}})}}`;
                    return `<span class="date-chip">${{fmt}} <span class="remove" onclick="removeRange('${{g[0]}}','${{g[g.length-1]}}')">×</span></span>`;
                }}
            }}).join('');
        }}

        function renderCalendar() {{
            const grid = document.getElementById('calendarGrid');
            const header = document.getElementById('currentMonth');
            header.textContent = monthNames[currentMonth.getMonth()] + ' ' + currentMonth.getFullYear();

            const first = new Date(currentMonth.getFullYear(), currentMonth.getMonth(), 1);
            const last = new Date(currentMonth.getFullYear(), currentMonth.getMonth() + 1, 0);
            const startPad = first.getDay();
            const prevLast = new Date(currentMonth.getFullYear(), currentMonth.getMonth(), 0);

            let html = '';
            for (let i = 0; i < startPad; i++) {{
                const d = prevLast.getDate() - startPad + i + 1;
                html += `<div class="cal-day other-month disabled">${{d}}</div>`;
            }}

            const sorted = Array.from(selectedDates).sort();
            for (let day = 1; day <= last.getDate(); day++) {{
                const d = new Date(currentMonth.getFullYear(), currentMonth.getMonth(), day);
                const dateStr = formatDate(d);
                const disabled = !isInSemester(d);
                const selected = selectedDates.has(dateStr);

                let rangeClass = '';
                if (selected && sorted.length > 0) {{
                    const idx = sorted.indexOf(dateStr);
                    const prevStr = idx > 0 ? sorted[idx-1] : null;
                    const nextStr = idx < sorted.length - 1 ? sorted[idx+1] : null;
                    const prevConsec = prevStr && (parseDateStr(dateStr) - parseDateStr(prevStr)) / 86400000 === 1;
                    const nextConsec = nextStr && (parseDateStr(nextStr) - parseDateStr(dateStr)) / 86400000 === 1;
                    if (prevConsec && nextConsec) rangeClass = ' range-mid';
                    else if (prevConsec) rangeClass = ' range-end';
                    else if (nextConsec) rangeClass = ' range-start';
                }}

                const cls = 'cal-day' + (selected ? ' selected' + rangeClass : '') + (disabled ? ' disabled' : '') + (!selected && !disabled ? '' : '');
                const onclick = disabled ? '' : `onclick="toggleDateWithShift('${{dateStr}}')"`;
                html += `<div class="${{cls}}" ${{onclick}}>${{day}}</div>`;
            }}

            const total = 42;
            const remaining = total - (startPad + last.getDate());
            for (let i = 1; i <= remaining; i++) {{
                html += `<div class="cal-day other-month disabled">${{i}}</div>`;
            }}

            grid.innerHTML = html;
        }}

        function prevMonth() {{
            currentMonth.setMonth(currentMonth.getMonth() - 1);
            renderCalendar();
        }}

        function nextMonth() {{
            currentMonth.setMonth(currentMonth.getMonth() + 1);
            renderCalendar();
        }}

        document.addEventListener('DOMContentLoaded', function() {{
            loadData();
            document.getElementById('prevMonth').addEventListener('click', prevMonth);
            document.getElementById('nextMonth').addEventListener('click', nextMonth);
            document.getElementById('clearAllBtn').addEventListener('click', clearAll);

            window.addEventListener('keydown', e => {{ if (e.key === 'Shift') isShiftPressed = true; }});
            window.addEventListener('keyup', e => {{ if (e.key === 'Shift') isShiftPressed = false; }});
        }});
    </script>
</body>
</html>"""
