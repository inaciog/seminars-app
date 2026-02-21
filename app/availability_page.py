"""
Simple, reliable availability page using native date inputs and a clean calendar.
"""

def get_availability_page_html(speaker_name, speaker_email, speaker_affiliation, suggested_topic, semester_plan, token, semester_start=None, semester_end=None):
    """Generate a simple, reliable speaker availability page."""
    
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
            --um-blue: #003366;
            --um-light-blue: #0066CC;
            --um-gold: #FFD700;
        }}
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            min-height: 100vh;
            line-height: 1.6;
        }}
        .um-header {{
            background: var(--um-blue);
            color: white;
            padding: 25px 20px;
            text-align: center;
        }}
        .um-header h1 {{ font-size: 26px; font-weight: 600; }}
        .um-header .subtitle {{ font-size: 14px; opacity: 0.9; margin-top: 5px; }}
        .container {{ max-width: 800px; margin: 0 auto; padding: 20px; }}
        .content {{ background: white; border-radius: 12px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); overflow: hidden; }}
        .welcome {{ background: linear-gradient(135deg, var(--um-blue) 0%, var(--um-light-blue) 100%); color: white; padding: 30px; }}
        .welcome h2 {{ font-size: 24px; margin-bottom: 10px; }}
        .info-card {{
            background: #f8f9fa;
            border-left: 4px solid var(--um-blue);
            padding: 20px;
            margin: 20px;
            border-radius: 8px;
        }}
        .info-card h3 {{ color: var(--um-blue); margin-bottom: 15px; }}
        .info-row {{ display: flex; margin-bottom: 8px; }}
        .info-label {{ width: 100px; font-weight: 500; color: #666; }}
        .info-value {{ flex: 1; color: #333; }}
        .form-section {{ padding: 30px; border-top: 1px solid #eee; }}
        .form-section h3 {{ color: var(--um-blue); margin-bottom: 20px; font-size: 20px; }}
        .form-group {{ margin-bottom: 20px; }}
        .form-group label {{ display: block; margin-bottom: 6px; font-weight: 500; color: #333; }}
        .form-group input,
        .form-group textarea,
        .form-group select {{
            width: 100%;
            padding: 12px;
            border: 2px solid #ddd;
            border-radius: 6px;
            font-size: 16px;
        }}
        .form-group input:focus,
        .form-group textarea:focus {{
            outline: none;
            border-color: var(--um-light-blue);
        }}
        .form-row {{ display: flex; gap: 15px; }}
        .form-row .form-group {{ flex: 1; }}
        .date-inputs {{ display: flex; gap: 10px; align-items: center; flex-wrap: wrap; }}
        .date-inputs input {{ width: 150px; }}
        .btn {{
            padding: 12px 24px;
            border: none;
            border-radius: 6px;
            font-size: 16px;
            cursor: pointer;
            transition: all 0.2s;
        }}
        .btn-primary {{ background: var(--um-blue); color: white; }}
        .btn-primary:hover {{ background: var(--um-light-blue); }}
        .btn-secondary {{ background: #757575; color: white; }}
        .btn-secondary:hover {{ background: #616161; }}
        .btn-danger {{ background: #f44336; color: white; font-size: 12px; padding: 6px 12px; }}
        .selected-dates {{
            background: #e8f5e9;
            border: 1px solid #4caf50;
            border-radius: 8px;
            padding: 15px;
            margin-top: 15px;
        }}
        .date-chip {{
            display: inline-block;
            background: var(--um-blue);
            color: white;
            padding: 5px 12px;
            border-radius: 20px;
            margin: 3px;
            font-size: 13px;
        }}
        .date-chip .remove {{ margin-left: 8px; cursor: pointer; font-weight: bold; }}
        .date-chip.range {{ background: #4caf50; }}
        .message {{
            padding: 15px;
            border-radius: 6px;
            margin: 20px;
            display: none;
        }}
        .message.success {{ background: #d4edda; border: 1px solid #28a745; color: #155724; }}
        .message.error {{ background: #f8d7da; border: 1px solid #dc3545; color: #721c24; }}
        .um-footer {{
            background: #f8f9fa;
            padding: 20px;
            text-align: center;
            color: #666;
            font-size: 14px;
            border-top: 1px solid #eee;
        }}
        .calendar-grid {{
            display: grid;
            grid-template-columns: repeat(7, 1fr);
            gap: 5px;
            margin-top: 15px;
        }}
        .calendar-day-header {{
            text-align: center;
            font-weight: 600;
            color: #666;
            padding: 10px 5px;
            font-size: 12px;
        }}
        .calendar-day {{
            aspect-ratio: 1;
            display: flex;
            align-items: center;
            justify-content: center;
            border: 1px solid #e0e0e0;
            border-radius: 4px;
            cursor: pointer;
            font-size: 14px;
            background: white;
            transition: all 0.2s;
        }}
        .calendar-day:hover:not(.disabled) {{ background: #e3f2fd; }}
        .calendar-day.selected {{ background: var(--um-blue); color: white; }}
        .calendar-day.disabled {{ color: #ccc; cursor: not-allowed; background: #f5f5f5; }}
        .calendar-day.other-month {{ color: #999; background: #fafafa; }}
        .calendar-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
        }}
        .calendar-header button {{
            background: var(--um-blue);
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
            cursor: pointer;
        }}
    </style>
</head>
<body>
    <div class="um-header">
        <h1>🏛️ University of Macau</h1>
        <div class="subtitle">Department of Economics · Faculty of Social Sciences</div>
    </div>
    
    <div class="container">
        <div class="content">
            <div class="welcome">
                <h2>📅 Submit Your Availability</h2>
                <p>Select the dates when you are available to present.</p>
            </div>
            
            <div class="info-card">
                <h3>Speaker Information</h3>
                <div class="info-row"><div class="info-label">Name:</div><div class="info-value">{speaker_name}</div></div>
                <div class="info-row"><div class="info-label">Email:</div><div class="info-value">{speaker_email or 'N/A'}</div></div>
                <div class="info-row"><div class="info-label">Affiliation:</div><div class="info-value">{speaker_affiliation or 'N/A'}</div></div>
                <div class="info-row"><div class="info-label">Topic:</div><div class="info-value">{suggested_topic or 'TBD'}</div></div>
                <div class="info-row"><div class="info-label">Semester:</div><div class="info-value">{semester_plan or 'TBD'}</div></div>
            </div>
            
            <form id="availabilityForm">
                <div class="form-section">
                    <h3>Select Available Dates</h3>
                    
                    <!-- Simple date range adder -->
                    <div class="form-group" style="background: #f5f5f5; padding: 15px; border-radius: 8px;">
                        <label>Add Date Range</label>
                        <div class="date-inputs">
                            <input type="date" id="rangeStart" min="{semester_start}" max="{semester_end}">
                            <span>to</span>
                            <input type="date" id="rangeEnd" min="{semester_start}" max="{semester_end}">
                            <button type="button" class="btn btn-primary" onclick="addRange()">Add</button>
                        </div>
                    </div>
                    
                    <!-- Calendar -->
                    <div style="margin-top: 20px;">
                        <div class="calendar-header">
                            <button type="button" onclick="prevMonth()">&lt; Prev</button>
                            <h3 id="currentMonth"></h3>
                            <button type="button" onclick="nextMonth()">Next &gt;</button>
                        </div>
                        <div class="calendar-grid" id="calendarGrid"></div>
                    </div>
                    
                    <!-- Selected dates display -->
                    <div class="selected-dates" id="selectedDatesBox" style="display: none;">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                            <h4 style="color: #2e7d32;">✓ Selected Dates (<span id="selectedCount">0</span>)</h4>
                            <button type="button" class="btn btn-danger" onclick="clearAll()">Clear All</button>
                        </div>
                        <div id="selectedDatesList"></div>
                    </div>
                    
                    <input type="hidden" id="selectedDatesInput" name="selected_dates">
                    
                    <div class="form-row" style="margin-top: 20px;">
                        <div class="form-group">
                            <label for="earliestTime">Earliest Start Time</label>
                            <input type="time" id="earliestTime" value="09:00">
                        </div>
                        <div class="form-group">
                            <label for="latestTime">Latest Start Time</label>
                            <input type="time" id="latestTime" value="17:00">
                        </div>
                    </div>
                    
                    <div class="form-group">
                        <label for="notes">Additional Notes</label>
                        <textarea id="notes" rows="3" placeholder="Any constraints, preferences, or special requirements..."></textarea>
                    </div>
                </div>
                
                <div style="padding: 0 30px 30px;">
                    <button type="submit" class="btn btn-primary" style="width: 100%;">Submit Availability</button>
                </div>
            </form>
            
            <div id="message" class="message"></div>
        </div>
        
        <div class="um-footer">
            <p>University of Macau · Faculty of Social Sciences · Department of Economics</p>
        </div>
    </div>
    
    <script>
        const semesterStart = new Date('{semester_start}');
        const semesterEnd = new Date('{semester_end}');
        let currentDate = new Date(semesterStart);
        let selectedDates = new Set();
        
        const monthNames = ['January', 'February', 'March', 'April', 'May', 'June',
                          'July', 'August', 'September', 'October', 'November', 'December'];
        const dayNames = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
        
        function formatDate(date) {{
            const year = date.getFullYear();
            const month = String(date.getMonth() + 1).padStart(2, '0');
            const day = String(date.getDate()).padStart(2, '0');
            return `${{year}}-${{month}}-${{day}}`;
        }}
        
        function renderCalendar() {{
            const grid = document.getElementById('calendarGrid');
            const monthHeader = document.getElementById('currentMonth');
            
            monthHeader.textContent = monthNames[currentDate.getMonth()] + ' ' + currentDate.getFullYear();
            
            let html = '';
            
            // Day headers
            dayNames.forEach(day => {{
                html += `<div class="calendar-day-header">${{day}}</div>`;
            }});
            
            const firstDay = new Date(currentDate.getFullYear(), currentDate.getMonth(), 1);
            const lastDay = new Date(currentDate.getFullYear(), currentDate.getMonth() + 1, 0);
            const prevLastDay = new Date(currentDate.getFullYear(), currentDate.getMonth(), 0);
            
            // Previous month days
            for (let i = firstDay.getDay() - 1; i >= 0; i--) {{
                const day = prevLastDay.getDate() - i;
                html += `<div class="calendar-day other-month">${{day}}</div>`;
            }}
            
            // Current month days
            for (let day = 1; day <= lastDay.getDate(); day++) {{
                const date = new Date(currentDate.getFullYear(), currentDate.getMonth(), day);
                const dateStr = formatDate(date);
                let classes = 'calendar-day';
                
                if (date < semesterStart || date > semesterEnd) {{
                    classes += ' disabled';
                }} else if (selectedDates.has(dateStr)) {{
                    classes += ' selected';
                }}
                
                const onclick = (date >= semesterStart && date <= semesterEnd) 
                    ? `onclick="toggleDate('${{dateStr}}')"` 
                    : '';
                
                html += `<div class="${{classes}}" ${{onclick}}>${{day}}</div>`;
            }}
            
            // Next month days
            const remaining = 42 - (firstDay.getDay() + lastDay.getDate());
            for (let day = 1; day <= remaining; day++) {{
                html += `<div class="calendar-day other-month">${{day}}</div>`;
            }}
            
            grid.innerHTML = html;
        }}
        
        function toggleDate(dateStr) {{
            if (selectedDates.has(dateStr)) {{
                selectedDates.delete(dateStr);
            }} else {{
                selectedDates.add(dateStr);
            }}
            updateDisplay();
        }}
        
        function addRange() {{
            const startInput = document.getElementById('rangeStart').value;
            const endInput = document.getElementById('rangeEnd').value;
            
            if (!startInput || !endInput) {{
                alert('Please select both start and end dates');
                return;
            }}
            
            const start = new Date(startInput);
            const end = new Date(endInput);
            
            const actualStart = start <= end ? start : end;
            const actualEnd = start <= end ? end : start;
            
            let count = 0;
            for (let d = new Date(actualStart); d <= actualEnd; d.setDate(d.getDate() + 1)) {{
                if (d >= semesterStart && d <= semesterEnd) {{
                    selectedDates.add(formatDate(d));
                    count++;
                }}
            }}
            
            if (count > 0) {{
                document.getElementById('rangeStart').value = '';
                document.getElementById('rangeEnd').value = '';
                updateDisplay();
            }}
        }}
        
        function updateDisplay() {{
            const box = document.getElementById('selectedDatesBox');
            const list = document.getElementById('selectedDatesList');
            const input = document.getElementById('selectedDatesInput');
            const count = document.getElementById('selectedCount');
            
            const sorted = Array.from(selectedDates).sort();
            
            if (sorted.length === 0) {{
                box.style.display = 'none';
                input.value = '';
                return;
            }}
            
            box.style.display = 'block';
            input.value = sorted.join(',');
            count.textContent = sorted.length;
            
            // Group consecutive dates
            const groups = [];
            let current = [sorted[0]];
            
            for (let i = 1; i < sorted.length; i++) {{
                const prev = new Date(sorted[i-1]);
                const curr = new Date(sorted[i]);
                if ((curr - prev) / (1000*60*60*24) === 1) {{
                    current.push(sorted[i]);
                }} else {{
                    groups.push(current);
                    current = [sorted[i]];
                }}
            }}
            groups.push(current);
            
            list.innerHTML = groups.map(g => {{
                if (g.length === 1) {{
                    const d = new Date(g[0]);
                    const fmt = d.toLocaleDateString('en-US', {{ weekday: 'short', month: 'short', day: 'numeric' }});
                    return `<span class="date-chip">${{fmt}} <span class="remove" onclick="removeDate('${{g[0]}}')">×</span></span>`;
                }} else {{
                    const s = new Date(g[0]);
                    const e = new Date(g[g.length-1]);
                    const fmt = `${{s.toLocaleDateString('en-US', {{month:'short', day:'numeric'}})}} - ${{e.toLocaleDateString('en-US', {{month:'short', day:'numeric'}})}}`;
                    return `<span class="date-chip range">${{fmt}} <span style="font-size:11px;">(${{g.length}}d)</span> <span class="remove" onclick="removeRange('${{g[0]}}', '${{g[g.length-1]}}')">×</span></span>`;
                }}
            }}).join('');
            
            renderCalendar();
        }}
        
        function removeDate(dateStr) {{
            selectedDates.delete(dateStr);
            updateDisplay();
        }}
        
        function removeRange(startStr, endStr) {{
            const start = new Date(startStr);
            const end = new Date(endStr);
            for (let d = new Date(start); d <= end; d.setDate(d.getDate() + 1)) {{
                selectedDates.delete(formatDate(d));
            }}
            updateDisplay();
        }}
        
        function clearAll() {{
            if (selectedDates.size === 0) return;
            if (!confirm(`Clear all ${{selectedDates.size}} selected dates?`)) return;
            selectedDates.clear();
            updateDisplay();
        }}
        
        function prevMonth() {{
            currentDate.setMonth(currentDate.getMonth() - 1);
            renderCalendar();
        }}
        
        function nextMonth() {{
            currentDate.setMonth(currentDate.getMonth() + 1);
            renderCalendar();
        }}
        
        // Form submission
        document.getElementById('availabilityForm').addEventListener('submit', async function(e) {{
            e.preventDefault();
            
            const btn = e.target.querySelector('button[type="submit"]');
            btn.disabled = true;
            btn.textContent = 'Submitting...';
            
            const sorted = Array.from(selectedDates).sort();
            
            if (sorted.length === 0) {{
                showMessage('Please select at least one date', 'error');
                btn.disabled = false;
                btn.textContent = 'Submit Availability';
                return;
            }}
            
            try {{
                const response = await fetch('/api/v1/seminars/speaker-tokens/{token}/submit-availability', {{
                    method: 'POST',
                    headers: {{'Content-Type': 'application/json'}},
                    body: JSON.stringify({{
                        availabilities: sorted.map(function(d) {{ return {{ start_date: d, end_date: d, preference: 'available' }}; }}),
                        earliest_time: document.getElementById('earliestTime').value,
                        latest_time: document.getElementById('latestTime').value,
                        general_notes: document.getElementById('notes').value
                    }})
                }});
                
                if (response.ok) {{
                    showMessage('Thank you! Your availability has been submitted successfully.', 'success');
                    selectedDates.clear();
                    updateDisplay();
                }} else {{
                    const err = await response.text();
                    showMessage('Error: ' + err, 'error');
                }}
            }} catch (err) {{
                showMessage('Network error. Please try again.', 'error');
            }} finally {{
                btn.disabled = false;
                btn.textContent = 'Submit Availability';
            }}
        }});
        
        function showMessage(text, type) {{
            const msg = document.getElementById('message');
            msg.innerHTML = '<strong>' + text + '</strong>';
            msg.className = 'message ' + type;
            msg.style.display = 'block';
            setTimeout(function() {{ msg.style.display = 'none'; }}, 5000);
        }}
        
        // Initialize
        renderCalendar();
    </script>
</body>
</html>"""
