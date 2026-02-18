"""
UM-Branded HTML Templates for Public Pages
"""

def get_um_styles():
    return """
    <style>
        :root {{
            --um-blue: #003366;
            --um-gold: #FFD700;
            --um-light-blue: #0066CC;
        }}
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            min-height: 100vh;
            padding: 20px;
        }}
        .um-header {{
            background: var(--um-blue);
            color: white;
            padding: 20px;
            text-align: center;
            margin: -20px -20px 30px -20px;
        }}
        .um-header h1 {{ font-size: 24px; margin: 0; }}
        .um-header .subtitle {{ font-size: 14px; opacity: 0.9; margin-top: 5px; }}
        .container {{
            max-width: 900px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        .content {{ padding: 40px; }}
        .welcome {{
            background: linear-gradient(135deg, var(--um-blue) 0%, var(--um-light-blue) 100%);
            color: white;
            padding: 30px;
            margin: -40px -40px 30px -40px;
        }}
        .welcome h2 {{ font-size: 28px; margin-bottom: 10px; }}
        .info-card {{
            background: #f8f9fa;
            border-left: 4px solid var(--um-gold);
            padding: 20px;
            margin-bottom: 30px;
            border-radius: 0 8px 8px 0;
        }}
        .info-card h3 {{ color: var(--um-blue); margin-bottom: 15px; font-size: 18px; }}
        .info-row {{ display: flex; margin-bottom: 10px; }}
        .info-label {{ font-weight: 600; color: var(--um-blue); width: 150px; flex-shrink: 0; }}
        .form-section {{ margin-bottom: 30px; }}
        .form-section h3 {{
            color: var(--um-blue);
            font-size: 20px;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid var(--um-gold);
        }}
        .form-group {{ margin-bottom: 20px; }}
        label {{ display: block; margin-bottom: 8px; font-weight: 500; color: var(--um-blue); }}
        input, textarea, select {{
            width: 100%;
            padding: 12px 16px;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            font-size: 16px;
        }}
        input:focus, textarea:focus, select:focus {{
            outline: none;
            border-color: var(--um-light-blue);
            box-shadow: 0 0 0 3px rgba(0, 102, 204, 0.1);
        }}
        .form-row {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }}
        @media (max-width: 600px) {{ .form-row {{ grid-template-columns: 1fr; }} }}
        .checkbox-group {{ display: flex; align-items: center; gap: 10px; margin-bottom: 15px; }}
        .btn-submit {{
            background: linear-gradient(135deg, var(--um-blue) 0%, var(--um-light-blue) 100%);
            color: white;
            border: none;
            padding: 16px 40px;
            border-radius: 8px;
            font-size: 18px;
            font-weight: 600;
            cursor: pointer;
            display: block;
            margin: 40px auto 0;
        }}
        .btn-submit:hover {{ transform: translateY(-2px); box-shadow: 0 4px 15px rgba(0,51,102,0.3); }}
        .btn-submit:disabled {{ background: #ccc; cursor: not-allowed; transform: none; }}
        .message {{
            margin-top: 20px;
            padding: 15px 20px;
            border-radius: 8px;
            text-align: center;
            display: none;
        }}
        .message.success {{ background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }}
        .message.error {{ background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }}
        .um-footer {{
            text-align: center;
            padding: 20px;
            background: #f5f5f5;
            color: #666;
            font-size: 14px;
            margin: 40px -40px -40px -40px;
        }}
        
        /* Calendar Styles */
        .calendar-container {{
            background: #f8f9fa;
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 20px;
        }}
        .calendar-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        }}
        .calendar-header button {{
            background: var(--um-blue);
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 6px;
            cursor: pointer;
        }}
        .calendar-grid {{
            display: grid;
            grid-template-columns: repeat(7, 1fr);
            gap: 5px;
        }}
        .calendar-day-header {{
            text-align: center;
            font-weight: 600;
            color: var(--um-blue);
            padding: 10px;
            font-size: 14px;
        }}
        .calendar-day {{
            aspect-ratio: 1;
            display: flex;
            align-items: center;
            justify-content: center;
            border-radius: 8px;
            cursor: pointer;
            font-size: 14px;
            transition: all 0.2s;
            background: white;
            border: 2px solid transparent;
        }}
        .calendar-day:hover:not(.disabled) {{
            background: #e3f2fd;
            border-color: var(--um-light-blue);
        }}
        .calendar-day.selected {{
            background: var(--um-blue);
            color: white;
        }}
        .calendar-day.in-range {{
            background: #90caf9;
            color: white;
        }}
        .calendar-day.disabled {{
            color: #ccc;
            cursor: not-allowed;
            background: #f5f5f5;
        }}
        .calendar-day.other-month {{
            color: #999;
        }}
        .selected-dates {{
            background: #e8f5e9;
            border: 1px solid #4caf50;
            border-radius: 8px;
            padding: 15px;
            margin-top: 15px;
        }}
        .selected-dates h4 {{
            color: #2e7d32;
            margin-bottom: 10px;
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
        .date-chip .remove {{
            margin-left: 8px;
            cursor: pointer;
            font-weight: bold;
        }}
        
        /* File upload styles */
        .file-upload-area {{
            border: 2px dashed #ccc;
            border-radius: 8px;
            padding: 30px;
            text-align: center;
            background: #fafafa;
            transition: all 0.3s;
            cursor: pointer;
        }}
        .file-upload-area:hover {{
            border-color: var(--um-light-blue);
            background: #f0f7ff;
        }}
        .file-upload-area.dragover {{
            border-color: var(--um-blue);
            background: #e3f2fd;
        }}
        .uploaded-files {{
            margin-top: 15px;
        }}
        .file-item {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            background: #f5f5f5;
            padding: 10px 15px;
            border-radius: 6px;
            margin-bottom: 8px;
        }}
        .file-item .file-name {{
            flex: 1;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }}
        .file-item .file-status {{
            margin-left: 10px;
            font-size: 12px;
            color: #666;
        }}
        .file-item .remove-file {{
            margin-left: 10px;
            color: #d32f2f;
            cursor: pointer;
            font-weight: bold;
        }}
        .save-indicator {{
            position: fixed;
            top: 20px;
            right: 20px;
            background: #4caf50;
            color: white;
            padding: 12px 20px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.2);
            display: none;
            z-index: 1000;
        }}
        .btn-secondary {{
            background: #757575;
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 6px;
            font-size: 14px;
            cursor: pointer;
            margin-right: 10px;
        }}
        .btn-secondary:hover {{
            background: #616161;
        }}
        .button-group {{
            display: flex;
            justify-content: center;
            gap: 15px;
            margin-top: 30px;
        }}
    </style>
    """

def get_availability_page_html(speaker_name, speaker_email, speaker_affiliation, suggested_topic, semester_plan, token, semester_start=None, semester_end=None):
    """Generate UM-branded speaker availability page with calendar widgets."""
    styles = get_um_styles()
    
    # Default semester dates if not provided
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
    {styles}
</head>
<body>
    <div class="um-header">
        <h1>🏛️ University of Macau</h1>
        <div class="subtitle">Department of Computer Science · Faculty of Science and Technology</div>
    </div>
    
    <div class="container">
        <div class="content">
            <div class="welcome">
                <h2>📅 Submit Your Availability</h2>
                <p>Select the dates when you are available to present. You can select individual dates or date ranges.</p>
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
                    <p style="margin-bottom: 15px; color: #666;">Click on dates to select them. Click and drag to select a range. Click again to deselect.</p>
                    
                    <div class="calendar-container">
                        <div class="calendar-header">
                            <button type="button" id="prevMonth">&lt; Previous</button>
                            <h3 id="currentMonth">January 2025</h3>
                            <button type="button" id="nextMonth">Next &gt;</button>
                        </div>
                        <div class="calendar-grid" id="calendarGrid">
                            <!-- Calendar will be generated by JavaScript -->
                        </div>
                    </div>
                    
                    <div class="selected-dates" id="selectedDatesContainer" style="display: none;">
                        <h4>✓ Selected Dates:</h4>
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
                
                <button type="submit" class="btn-submit">Submit Availability</button>
            </form>
            
            <div id="message" class="message"></div>
        </div>
        <div class="um-footer">
            <p>University of Macau · Faculty of Science and Technology · Department of Computer Science</p>
        </div>
    </div>
    
    <script>
        // Calendar functionality
        const semesterStart = new Date('{semester_start}');
        const semesterEnd = new Date('{semester_end}');
        let currentDate = new Date(semesterStart);
        let selectedDates = new Set();
        let isDragging = false;
        let dragStart = null;
        
        const monthNames = ['January', 'February', 'March', 'April', 'May', 'June',
                          'July', 'August', 'September', 'October', 'November', 'December'];
        const dayNames = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
        
        function renderCalendar() {{
            const grid = document.getElementById('calendarGrid');
            const monthHeader = document.getElementById('currentMonth');
            
            monthHeader.textContent = monthNames[currentDate.getMonth()] + ' ' + currentDate.getFullYear();
            
            // Clear grid
            grid.innerHTML = '';
            
            // Add day headers
            dayNames.forEach(day => {{
                const header = document.createElement('div');
                header.className = 'calendar-day-header';
                header.textContent = day;
                grid.appendChild(header);
            }});
            
            // Get first day of month and number of days
            const firstDay = new Date(currentDate.getFullYear(), currentDate.getMonth(), 1);
            const lastDay = new Date(currentDate.getFullYear(), currentDate.getMonth() + 1, 0);
            const prevLastDay = new Date(currentDate.getFullYear(), currentDate.getMonth(), 0);
            
            // Previous month days
            for (let i = firstDay.getDay() - 1; i >= 0; i--) {{
                const day = prevLastDay.getDate() - i;
                const dayEl = createDayElement(day, true);
                grid.appendChild(dayEl);
            }}
            
            // Current month days
            for (let day = 1; day <= lastDay.getDate(); day++) {{
                const date = new Date(currentDate.getFullYear(), currentDate.getMonth(), day);
                const dayEl = createDayElement(day, false, date);
                grid.appendChild(dayEl);
            }}
            
            // Next month days
            const remainingCells = 42 - (firstDay.getDay() + lastDay.getDate());
            for (let day = 1; day <= remainingCells; day++) {{
                const dayEl = createDayElement(day, true);
                grid.appendChild(dayEl);
            }}
        }}
        
        function createDayElement(day, isOtherMonth, date) {{
            const el = document.createElement('div');
            el.className = 'calendar-day';
            el.textContent = day;
            
            if (isOtherMonth) {{
                el.classList.add('other-month');
            }} else if (date) {{
                const dateStr = formatDate(date);
                
                // Check if within semester
                if (date < semesterStart || date > semesterEnd) {{
                    el.classList.add('disabled');
                }} else {{
                    if (selectedDates.has(dateStr)) {{
                        el.classList.add('selected');
                    }}
                    
                    el.addEventListener('mousedown', () => startDrag(dateStr));
                    el.addEventListener('mouseenter', () => dragOver(dateStr));
                    el.addEventListener('mouseup', () => endDrag());
                }}
            }}
            
            return el;
        }}
        
        function formatDate(date) {{
            return date.toISOString().split('T')[0];
        }}
        
        function startDrag(dateStr) {{
            isDragging = true;
            dragStart = dateStr;
            toggleDate(dateStr);
        }}
        
        function dragOver(dateStr) {{
            if (!isDragging || !dragStart) return;
            
            // Select range
            const start = new Date(Math.min(new Date(dragStart), new Date(dateStr)));
            const end = new Date(Math.max(new Date(dragStart), new Date(dateStr)));
            
            for (let d = new Date(start); d <= end; d.setDate(d.getDate() + 1)) {{
                const dateStr = formatDate(d);
                if (d >= semesterStart && d <= semesterEnd) {{
                    selectedDates.add(dateStr);
                }}
            }}
            
            renderCalendar();
            updateSelectedDates();
        }}
        
        function endDrag() {{
            isDragging = false;
            dragStart = null;
        }}
        
        function toggleDate(dateStr) {{
            if (selectedDates.has(dateStr)) {{
                selectedDates.delete(dateStr);
            }} else {{
                selectedDates.add(dateStr);
            }}
            renderCalendar();
            updateSelectedDates();
        }}
        
        function updateSelectedDates() {{
            const container = document.getElementById('selectedDatesContainer');
            const list = document.getElementById('selectedDatesList');
            const input = document.getElementById('selectedDatesInput');
            
            const sortedDates = Array.from(selectedDates).sort();
            
            if (sortedDates.length === 0) {{
                container.style.display = 'none';
                input.value = '';
                return;
            }}
            
            container.style.display = 'block';
            input.value = sortedDates.join(',');
            
            list.innerHTML = sortedDates.map(date => {{
                const d = new Date(date);
                const formatted = d.toLocaleDateString('en-US', {{ 
                    weekday: 'short', 
                    month: 'short', 
                    day: 'numeric' 
                }});
                return '<span class="date-chip">' + formatted + '<span class="remove" onclick="removeDate(\'' + date + '\')">×</span></span>';
            }}).join('');
        }}
        
        function removeDate(dateStr) {{
            selectedDates.delete(dateStr);
            renderCalendar();
            updateSelectedDates();
        }}
        
        // Navigation
        document.getElementById('prevMonth').addEventListener('click', () => {{
            currentDate.setMonth(currentDate.getMonth() - 1);
            renderCalendar();
        }});
        
        document.getElementById('nextMonth').addEventListener('click', () => {{
            currentDate.setMonth(currentDate.getMonth() + 1);
            renderCalendar();
        }});
        
        // Form submission
        document.getElementById('availabilityForm').addEventListener('submit', async (e) => {{
            e.preventDefault();
            
            const btn = document.querySelector('.btn-submit');
            btn.disabled = true;
            btn.textContent = 'Submitting...';
            
            const sortedDates = Array.from(selectedDates).sort();
            
            if (sortedDates.length === 0) {{
                const msg = document.getElementById('message');
                msg.style.display = 'block';
                msg.className = 'message error';
                msg.innerHTML = '<strong>❌ Please select at least one date</strong>';
                btn.disabled = false;
                btn.textContent = 'Submit Availability';
                return;
            }}
            
            // Convert to availabilities
            const availabilities = sortedDates.map(date => ({{
                start_date: date,
                end_date: date,
                preference: 'available'
            }}));
            
            try {{
                const response = await fetch('/api/v1/seminars/speaker-tokens/{token}/submit-availability', {{
                    method: 'POST',
                    headers: {{'Content-Type': 'application/json'}},
                    body: JSON.stringify({{
                        availabilities: availabilities,
                        earliest_time: document.getElementById('earliestTime').value,
                        latest_time: document.getElementById('latestTime').value,
                        general_notes: document.getElementById('notes').value
                    }})
                }});
                
                const msg = document.getElementById('message');
                msg.style.display = 'block';
                
                if (response.ok) {{
                    msg.className = 'message success';
                    msg.innerHTML = '<strong>✅ Thank you!</strong><br>Your availability has been submitted successfully. We will contact you soon to confirm the date.';
                    document.getElementById('availabilityForm').reset();
                    selectedDates.clear();
                    renderCalendar();
                    updateSelectedDates();
                }} else {{
                    const error = await response.text();
                    msg.className = 'message error';
                    msg.innerHTML = '<strong>❌ Error</strong><br>' + error;
                }}
            }} catch (err) {{
                const msg = document.getElementById('message');
                msg.style.display = 'block';
                msg.className = 'message error';
                msg.innerHTML = '<strong>❌ Network Error</strong><br>Please check your connection and try again.';
            }} finally {{
                btn.disabled = false;
                btn.textContent = 'Submit Availability';
            }}
        }});
        
        // Initialize calendar
        renderCalendar();
    </script>
</body>
</html>"""

def get_speaker_info_page_html(speaker_name, speaker_email, speaker_affiliation, seminar_title, seminar_date, token, seminar_id=None):
    """Generate UM-branded speaker information page with file uploads and save/resume capability."""
    styles = get_um_styles()
    
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Speaker Information - University of Macau</title>
    {styles}
</head>
<body>
    <div class="um-header">
        <h1>🏛️ University of Macau</h1>
        <div class="subtitle">Department of Computer Science · Faculty of Science and Technology</div>
    </div>
    
    <div class="container">
        <div class="content">
            <div class="welcome">
                <h2>📝 Speaker Information Form</h2>
                <p>Please provide your details and upload required documents. You can save your progress and return later to complete.</p>
            </div>
            
            <div class="info-card">
                <h3>Seminar Details</h3>
                <div class="info-row"><div class="info-label">Speaker:</div><div class="info-value">{speaker_name}</div></div>
                <div class="info-row"><div class="info-label">Title:</div><div class="info-value">{seminar_title or 'TBD'}</div></div>
                <div class="info-row"><div class="info-label">Date:</div><div class="info-value">{seminar_date or 'To be confirmed'}</div></div>
            </div>
            
            <form id="infoForm">
                <div class="form-section">
                    <h3>Personal Information</h3>
                    
                    <div class="form-row">
                        <div class="form-group">
                            <label for="passportNumber">Passport Number *</label>
                            <input type="text" id="passportNumber" required placeholder="e.g., A12345678">
                        </div>
                        
                        <div class="form-group">
                            <label for="passportCountry">Passport Country *</label>
                            <input type="text" id="passportCountry" required placeholder="e.g., United States">
                        </div>
                    </div>
                </div>
                
                <div class="form-section">
                    <h3>Travel Information</h3>
                    
                    <div class="form-row">
                        <div class="form-group">
                            <label for="departureCity">Departure City *</label>
                            <input type="text" id="departureCity" required placeholder="e.g., New York">
                        </div>
                        
                        <div class="form-group">
                            <label for="travelMethod">Travel Method *</label>
                            <select id="travelMethod" required>
                                <option value="">Select...</option>
                                <option value="flight">Flight</option>
                                <option value="train">Train</option>
                                <option value="other">Other</option>
                            </select>
                        </div>
                    </div>
                    
                    <div class="checkbox-group">
                        <input type="checkbox" id="needsAccommodation" checked>
                        <label for="needsAccommodation" style="margin: 0;">I need accommodation at the university guesthouse</label>
                    </div>
                    
                    <div class="form-row" id="accommodationDates">
                        <div class="form-group">
                            <label for="checkInDate">Check-in Date</label>
                            <input type="date" id="checkInDate">
                        </div>
                        
                        <div class="form-group">
                            <label for="checkOutDate">Check-out Date</label>
                            <input type="date" id="checkOutDate">
                        </div>
                    </div>
                </div>
                
                <div class="form-section">
                    <h3>Payment Information</h3>
                    
                    <div class="form-group">
                        <label for="paymentEmail">Payment Email *</label>
                        <input type="email" id="paymentEmail" required placeholder="your@email.com">
                    </div>
                    
                    <div class="form-group">
                        <label for="beneficiaryName">Beneficiary Name (as on bank account) *</label>
                        <input type="text" id="beneficiaryName" required placeholder="Full name">
                    </div>
                    
                    <div class="form-row">
                        <div class="form-group">
                            <label for="bankName">Bank Name *</label>
                            <input type="text" id="bankName" required placeholder="Your bank">
                        </div>
                        
                        <div class="form-group">
                            <label for="swiftCode">SWIFT/BIC Code *</label>
                            <input type="text" id="swiftCode" required placeholder="e.g., CHASUS33">
                        </div>
                    </div>
                    
                    <div class="form-group">
                        <label for="bankAccount">Bank Account Number *</label>
                        <input type="text" id="bankAccount" required placeholder="Your account number">
                    </div>
                    
                    <div class="form-group">
                        <label for="bankAddress">Bank Address</label>
                        <textarea id="bankAddress" rows="2" placeholder="Full bank address..."></textarea>
                    </div>
                    
                    <div class="form-group">
                        <label for="currency">Payment Currency *</label>
                        <select id="currency" required>
                            <option value="">Select...</option>
                            <option value="USD">USD</option>
                            <option value="EUR">EUR</option>
                            <option value="GBP">GBP</option>
                            <option value="CNY">CNY</option>
                            <option value="MOP">MOP</option>
                            <option value="HKD">HKD</option>
                        </select>
                    </div>
                </div>
                
                <div class="form-section">
                    <h3>Talk Information</h3>
                    
                    <div class="form-group">
                        <label for="talkTitle">Final Talk Title *</label>
                        <input type="text" id="talkTitle" required placeholder="Title of your presentation">
                    </div>
                    
                    <div class="form-group">
                        <label for="abstract">Abstract *</label>
                        <textarea id="abstract" rows="5" required placeholder="Abstract (150-300 words)..."></textarea>
                    </div>
                    
                    <div class="checkbox-group">
                        <input type="checkbox" id="needsProjector" checked>
                        <label for="needsProjector" style="margin: 0;">I need a projector</label>
                    </div>
                    
                    <div class="checkbox-group">
                        <input type="checkbox" id="needsMicrophone">
                        <label for="needsMicrophone" style="margin: 0;">I need a microphone</label>
                    </div>
                    
                    <div class="form-group">
                        <label for="specialRequirements">Special Requirements</label>
                        <textarea id="specialRequirements" rows="2" placeholder="Any special equipment or setup needs..."></textarea>
                    </div>
                </div>
                
                <div class="form-section">
                    <h3>Document Uploads</h3>
                    
                    <div class="form-group">
                        <label>CV / Resume *</label>
                        <div class="file-upload-area" id="cvUpload" onclick="document.getElementById('cvFile').click()">
                            <p>📄 Click to upload or drag and drop</p>
                            <p style="font-size: 12px; color: #666;">PDF, DOC, DOCX up to 10MB</p>
                            <input type="file" id="cvFile" accept=".pdf,.doc,.docx" style="display: none;">
                        </div>
                        <div class="uploaded-files" id="cvFiles"></div>
                    </div>
                    
                    <div class="form-group">
                        <label>Photo (for badge) *</label>
                        <div class="file-upload-area" id="photoUpload" onclick="document.getElementById('photoFile').click()">
                            <p>🖼️ Click to upload or drag and drop</p>
                            <p style="font-size: 12px; color: #666;">JPG, PNG up to 5MB</p>
                            <input type="file" id="photoFile" accept=".jpg,.jpeg,.png" style="display: none;">
                        </div>
                        <div class="uploaded-files" id="photoFiles"></div>
                    </div>
                    
                    <div class="form-group">
                        <label>Passport Copy (for hotel booking)</label>
                        <div class="file-upload-area" id="passportUpload" onclick="document.getElementById('passportFile').click()">
                            <p>🛂 Click to upload or drag and drop</p>
                            <p style="font-size: 12px; color: #666;">PDF, JPG, PNG up to 10MB</p>
                            <input type="file" id="passportFile" accept=".pdf,.jpg,.jpeg,.png" style="display: none;">
                        </div>
                        <div class="uploaded-files" id="passportFiles"></div>
                    </div>
                </div>
                
                <div class="button-group">
                    <button type="button" class="btn-secondary" onclick="saveDraft()">💾 Save Draft</button>
                    <button type="submit" class="btn-submit">Submit Information</button>
                </div>
            </form>
            
            <div id="message" class="message"></div>
        </div>
        <div class="um-footer">
            <p>University of Macau · Faculty of Science and Technology · Department of Computer Science</p>
            <p style="margin-top: 10px; font-size: 12px;">You can save your progress and return to this page using the same link.</p>
        </div>
    </div>
    
    <div class="save-indicator" id="saveIndicator">✓ Saved successfully!</div>
    
    <script>
        // File upload handling
        const uploadedFiles = {{}};
        
        function setupFileUpload(inputId, containerId, category) {{
            const input = document.getElementById(inputId);
            const container = document.getElementById(containerId);
            const uploadArea = input.parentElement;
            
            uploadArea.addEventListener('dragover', (e) => {{
                e.preventDefault();
                uploadArea.classList.add('dragover');
            }});
            
            uploadArea.addEventListener('dragleave', () => {{
                uploadArea.classList.remove('dragover');
            }});
            
            uploadArea.addEventListener('drop', (e) => {{
                e.preventDefault();
                uploadArea.classList.remove('dragover');
                handleFiles(e.dataTransfer.files, container, category);
            }});
            
            input.addEventListener('change', (e) => {{
                handleFiles(e.target.files, container, category);
            }});
        }}
        
        function handleFiles(files, container, category) {{
            for (const file of files) {{
                const fileId = Date.now() + '_' + Math.random().toString(36).substr(2, 9);
                uploadedFiles[fileId] = {{ file: file, category: category, uploaded: false }};
                
                const fileEl = document.createElement('div');
                fileEl.className = 'file-item';
                fileEl.id = 'file_' + fileId;
                fileEl.innerHTML = '<span class="file-name">' + file.name + '</span><span class="file-status">Ready to upload</span><span class="remove-file" onclick="removeFile(\'' + fileId + '\')">×</span>';
                container.appendChild(fileEl);
            }}
        }}
        
        function removeFile(fileId) {{
            delete uploadedFiles[fileId];
            const el = document.getElementById('file_' + fileId);
            if (el) el.remove();
        }}
        
        async function uploadFiles() {{
            const fileIds = Object.keys(uploadedFiles).filter(id => !uploadedFiles[id].uploaded);
            
            for (const fileId of fileIds) {{
                const fileData = uploadedFiles[fileId];
                const formData = new FormData();
                formData.append('file', fileData.file);
                formData.append('category', fileData.category);
                
                try {{
                    const response = await fetch('/api/v1/seminars/seminars/{seminar_id or 0}/upload', {{
                        method: 'POST',
                        body: formData
                    }});
                    
                    if (response.ok) {{
                        uploadedFiles[fileId].uploaded = true;
                        const el = document.getElementById('file_' + fileId);
                        if (el) {{
                            el.querySelector('.file-status').textContent = '✓ Uploaded';
                            el.querySelector('.file-status').style.color = '#4caf50';
                        }}
                    }}
                }} catch (err) {{
                    console.error('Upload failed:', err);
                }}
            }}
        }}
        
        setupFileUpload('cvFile', 'cvFiles', 'cv');
        setupFileUpload('photoFile', 'photoFiles', 'photo');
        setupFileUpload('passportFile', 'passportFiles', 'passport');
        
        document.getElementById('needsAccommodation').addEventListener('change', (e) => {{
            const datesDiv = document.getElementById('accommodationDates');
            datesDiv.style.opacity = e.target.checked ? '1' : '0.5';
            datesDiv.querySelectorAll('input').forEach(input => {{
                input.disabled = !e.target.checked;
            }});
        }});
        
        function saveDraft() {{
            const formData = {{
                passport_number: document.getElementById('passportNumber').value,
                passport_country: document.getElementById('passportCountry').value,
                departure_city: document.getElementById('departureCity').value,
                travel_method: document.getElementById('travelMethod').value,
                needs_accommodation: document.getElementById('needsAccommodation').checked,
                check_in_date: document.getElementById('checkInDate').value,
                check_out_date: document.getElementById('checkOutDate').value,
                payment_email: document.getElementById('paymentEmail').value,
                beneficiary_name: document.getElementById('beneficiaryName').value,
                bank_name: document.getElementById('bankName').value,
                swift_code: document.getElementById('swiftCode').value,
                bank_account_number: document.getElementById('bankAccount').value,
                bank_address: document.getElementById('bankAddress').value,
                currency: document.getElementById('currency').value,
                talk_title: document.getElementById('talkTitle').value,
                abstract: document.getElementById('abstract').value,
                needs_projector: document.getElementById('needsProjector').checked,
                needs_microphone: document.getElementById('needsMicrophone').checked,
                special_requirements: document.getElementById('specialRequirements').value
            }};
            
            localStorage.setItem('speaker_info_draft_{token}', JSON.stringify(formData));
            
            const indicator = document.getElementById('saveIndicator');
            indicator.style.display = 'block';
            setTimeout(() => {{
                indicator.style.display = 'none';
            }}, 2000);
        }}
        
        function loadDraft() {{
            const draft = localStorage.getItem('speaker_info_draft_{token}');
            if (!draft) return;
            
            try {{
                const data = JSON.parse(draft);
                document.getElementById('passportNumber').value = data.passport_number || '';
                document.getElementById('passportCountry').value = data.passport_country || '';
                document.getElementById('departureCity').value = data.departure_city || '';
                document.getElementById('travelMethod').value = data.travel_method || '';
                document.getElementById('needsAccommodation').checked = data.needs_accommodation !== false;
                document.getElementById('checkInDate').value = data.check_in_date || '';
                document.getElementById('checkOutDate').value = data.check_out_date || '';
                document.getElementById('paymentEmail').value = data.payment_email || '';
                document.getElementById('beneficiaryName').value = data.beneficiary_name || '';
                document.getElementById('bankName').value = data.bank_name || '';
                document.getElementById('swiftCode').value = data.swift_code || '';
                document.getElementById('bankAccount').value = data.bank_account_number || '';
                document.getElementById('bankAddress').value = data.bank_address || '';
                document.getElementById('currency').value = data.currency || '';
                document.getElementById('talkTitle').value = data.talk_title || '';
                document.getElementById('abstract').value = data.abstract || '';
                document.getElementById('needsProjector').checked = data.needs_projector !== false;
                document.getElementById('needsMicrophone').checked = data.needs_microphone || false;
                document.getElementById('specialRequirements').value = data.special_requirements || '';
                
                document.getElementById('needsAccommodation').dispatchEvent(new Event('change'));
            }} catch (e) {{
                console.error('Failed to load draft:', e);
            }}
        }}
        
        setInterval(saveDraft, 30000);
        loadDraft();
        
        document.getElementById('infoForm').addEventListener('submit', async (e) => {{
            e.preventDefault();
            
            const btn = document.querySelector('.btn-submit');
            btn.disabled = true;
            btn.textContent = 'Submitting...';
            
            await uploadFiles();
            
            const data = {{
                passport_number: document.getElementById('passportNumber').value,
                passport_country: document.getElementById('passportCountry').value,
                departure_city: document.getElementById('departureCity').value,
                travel_method: document.getElementById('travelMethod').value,
                needs_accommodation: document.getElementById('needsAccommodation').checked,
                check_in_date: document.getElementById('checkInDate').value || null,
                check_out_date: document.getElementById('checkOutDate').value || null,
                payment_email: document.getElementById('paymentEmail').value,
                beneficiary_name: document.getElementById('beneficiaryName').value,
                bank_name: document.getElementById('bankName').value,
                swift_code: document.getElementById('swiftCode').value,
                bank_account_number: document.getElementById('bankAccount').value,
                bank_address: document.getElementById('bankAddress').value,
                currency: document.getElementById('currency').value,
                talk_title: document.getElementById('talkTitle').value,
                abstract: document.getElementById('abstract').value,
                needs_projector: document.getElementById('needsProjector').checked,
                needs_microphone: document.getElementById('needsMicrophone').checked,
                special_requirements: document.getElementById('specialRequirements').value
            }};
            
            try {{
                const response = await fetch('/api/v1/seminars/speaker-tokens/{token}/submit-info', {{
                    method: 'POST',
                    headers: {{'Content-Type': 'application/json'}},
                    body: JSON.stringify(data)
                }});
                
                const msg = document.getElementById('message');
                msg.style.display = 'block';
                
                if (response.ok) {{
                    msg.className = 'message success';
                    msg.innerHTML = '<strong>✅ Thank you!</strong><br>Your information has been submitted successfully.';
                    localStorage.removeItem('speaker_info_draft_{token}');
                }} else {{
                    const error = await response.text();
                    msg.className = 'message error';
                    msg.innerHTML = '<strong>❌ Error</strong><br>' + error;
                }}
            }} catch (err) {{
                const msg = document.getElementById('message');
                msg.style.display = 'block';
                msg.className = 'message error';
                msg.innerHTML = '<strong>❌ Network Error</strong><br>Please check your connection and try again.';
            }} finally {{
                btn.disabled = false;
                btn.textContent = 'Submit Information';
            }}
        }});
    </script>
</body>
</html>"""

def get_invalid_token_html():
    return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Invalid Link - University of Macau</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, sans-serif; background: #f5f5f5; text-align: center; padding: 50px; }}
        .container {{ max-width: 600px; margin: 0 auto; background: white; padding: 40px; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.1); }}
        h1 {{ color: #003366; font-size: 48px; margin-bottom: 20px; }}
        p {{ font-size: 18px; color: #666; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>❌ Invalid Link</h1>
        <p>This link is no longer valid or has expired.</p>
        <p style="margin-top: 20px;">If you believe this is an error, please contact the seminar coordinator.</p>
    </div>
</body>
</html>"""
