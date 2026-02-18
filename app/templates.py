"""
UM-Branded HTML Templates for Public Pages
"""

def get_um_styles():
    return """
    <style>
        :root {
            --um-blue: #003366;
            --um-gold: #FFD700;
            --um-light-blue: #0066CC;
        }
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .um-header {
            background: var(--um-blue);
            color: white;
            padding: 20px;
            text-align: center;
            margin: -20px -20px 30px -20px;
        }
        .um-header h1 { font-size: 24px; margin: 0; }
        .um-header .subtitle { font-size: 14px; opacity: 0.9; margin-top: 5px; }
        .container {
            max-width: 800px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        .content { padding: 40px; }
        .welcome {
            background: linear-gradient(135deg, var(--um-blue) 0%, var(--um-light-blue) 100%);
            color: white;
            padding: 30px;
            margin: -40px -40px 30px -40px;
        }
        .welcome h2 { font-size: 28px; margin-bottom: 10px; }
        .info-card {
            background: #f8f9fa;
            border-left: 4px solid var(--um-gold);
            padding: 20px;
            margin-bottom: 30px;
        }
        .info-card h3 { color: var(--um-blue); margin-bottom: 15px; }
        .info-row { display: flex; margin-bottom: 10px; }
        .info-label { font-weight: 600; color: var(--um-blue); width: 150px; }
        .form-section { margin-bottom: 30px; }
        .form-section h3 {
            color: var(--um-blue);
            font-size: 20px;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid var(--um-gold);
        }
        .form-group { margin-bottom: 20px; }
        label { display: block; margin-bottom: 8px; font-weight: 500; color: var(--um-blue); }
        input, textarea, select {
            width: 100%;
            padding: 12px 16px;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            font-size: 16px;
        }
        input:focus, textarea:focus, select:focus {
            outline: none;
            border-color: var(--um-light-blue);
        }
        .form-row { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
        @media (max-width: 600px) { .form-row { grid-template-columns: 1fr; } }
        .checkbox-group { display: flex; align-items: center; gap: 10px; margin-bottom: 15px; }
        .btn-submit {
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
        }
        .btn-submit:hover { transform: translateY(-2px); box-shadow: 0 4px 15px rgba(0,51,102,0.3); }
        .message {
            margin-top: 20px;
            padding: 15px 20px;
            border-radius: 8px;
            text-align: center;
            display: none;
        }
        .message.success { background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
        .message.error { background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
        .um-footer {
            text-align: center;
            padding: 20px;
            background: #f5f5f5;
            color: #666;
            font-size: 14px;
            margin: 40px -40px -40px -40px;
        }
    </style>
    """

def get_availability_page_html(speaker_name, speaker_email, speaker_affiliation, suggested_topic, semester_plan, token):
    styles = get_um_styles()
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
                <p>We look forward to hosting you for our seminar series!</p>
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
                    <h3>Availability Preferences</h3>
                    <div class="form-group">
                        <label for="dateRanges">Available Date Ranges</label>
                        <textarea id="dateRanges" rows="4" placeholder="2025-03-15 to 2025-03-20&#10;2025-04-01, 2025-04-05"></textarea>
                    </div>
                    <div class="form-row">
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
                        <textarea id="notes" rows="3" placeholder="Any constraints or preferences..."></textarea>
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
        document.getElementById('availabilityForm').addEventListener('submit', async (e) => {{
            e.preventDefault();
            const btn = document.querySelector('.btn-submit');
            btn.disabled = true;
            btn.textContent = 'Submitting...';
            const dateRanges = document.getElementById('dateRanges').value.trim();
            const availabilities = [];
            for (const line of dateRanges.split('\n')) {{
                const trimmed = line.trim();
                if (!trimmed) continue;
                if (trimmed.includes('to')) {{
                    const [start, end] = trimmed.split('to').map(s => s.trim());
                    availabilities.push({{start_date: start, end_date: end, preference: 'available'}});
                }} else {{
                    availabilities.push({{start_date: trimmed, end_date: trimmed, preference: 'available'}});
                }}
            }}
            try {{
                const response = await fetch('/api/v1/seminars/speaker-tokens/{token}/submit-availability', {{
                    method: 'POST',
                    headers: {{'Content-Type': 'application/json'}},
                    body: JSON.stringify({{
                        availabilities,
                        earliest_time: document.getElementById('earliestTime').value,
                        latest_time: document.getElementById('latestTime').value,
                        general_notes: document.getElementById('notes').value
                    }})
                }});
                const msg = document.getElementById('message');
                msg.style.display = 'block';
                if (response.ok) {{
                    msg.className = 'message success';
                    msg.innerHTML = '<strong>✅ Thank you!</strong><br>Your availability has been submitted.';
                    document.getElementById('availabilityForm').reset();
                }} else {{
                    msg.className = 'message error';
                    msg.innerHTML = '<strong>❌ Error</strong><br>Please try again.';
                }}
            }} catch (err) {{
                const msg = document.getElementById('message');
                msg.style.display = 'block';
                msg.className = 'message error';
                msg.innerHTML = '<strong>❌ Network Error</strong><br>Please check your connection.';
            }} finally {{
                btn.disabled = false;
                btn.textContent = 'Submit Availability';
            }}
        }});
    </script>
</body>
</html>"""

def get_speaker_info_page_html(speaker_name, speaker_email, speaker_affiliation, seminar_title, seminar_date, token):
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
                <p>Please provide your details for our records and arrangements.</p>
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
                </div>
                <div class="form-section">
                    <h3>Payment Information</h3>
                    <div class="form-group">
                        <label for="paymentEmail">Payment Email *</label>
                        <input type="email" id="paymentEmail" required placeholder="your@email.com">
                    </div>
                    <div class="form-group">
                        <label for="beneficiaryName">Beneficiary Name *</label>
                        <input type="text" id="beneficiaryName" required placeholder="Full name">
                    </div>
                    <div class="form-row">
                        <div class="form-group">
                            <label for="bankName">Bank Name *</label>
                            <input type="text" id="bankName" required placeholder="Your bank">
                        </div>
                        <div class="form-group">
                            <label for="swiftCode">SWIFT Code *</label>
                            <input type="text" id="swiftCode" required placeholder="e.g., CHASUS33">
                        </div>
                    </div>
                    <div class="form-group">
                        <label for="currency">Currency *</label>
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
                </div>
                <button type="submit" class="btn-submit">Submit Information</button>
            </form>
            <div id="message" class="message"></div>
        </div>
        <div class="um-footer">
            <p>University of Macau · Faculty of Science and Technology · Department of Computer Science</p>
        </div>
    </div>
    <script>
        document.getElementById('infoForm').addEventListener('submit', async (e) => {{
            e.preventDefault();
            const btn = document.querySelector('.btn-submit');
            btn.disabled = true;
            btn.textContent = 'Submitting...';
            const data = {{
                passport_number: document.getElementById('passportNumber').value,
                passport_country: document.getElementById('passportCountry').value,
                departure_city: document.getElementById('departureCity').value,
                travel_method: document.getElementById('travelMethod').value,
                payment_email: document.getElementById('paymentEmail').value,
                beneficiary_name: document.getElementById('beneficiaryName').value,
                bank_name: document.getElementById('bankName').value,
                swift_code: document.getElementById('swiftCode').value,
                currency: document.getElementById('currency').value,
                talk_title: document.getElementById('talkTitle').value,
                abstract: document.getElementById('abstract').value
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
                    msg.innerHTML = '<strong>✅ Thank you!</strong><br>Your information has been submitted.';
                }} else {{
                    msg.className = 'message error';
                    msg.innerHTML = '<strong>❌ Error</strong><br>Please try again.';
                }}
            }} catch (err) {{
                const msg = document.getElementById('message');
                msg.style.display = 'block';
                msg.className = 'message error';
                msg.innerHTML = '<strong>❌ Network Error</strong><br>Please check your connection.';
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
        body { font-family: -apple-system, BlinkMacSystemFont, sans-serif; background: #f5f5f5; text-align: center; padding: 50px; }
        .container { max-width: 600px; margin: 0 auto; background: white; padding: 40px; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.1); }
        h1 { color: #003366; font-size: 48px; margin-bottom: 20px; }
        p { font-size: 18px; color: #666; }
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
