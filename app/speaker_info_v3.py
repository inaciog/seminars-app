"""
Speaker Info Page - Continuous Save Version
All changes are saved immediately to the server. No draft vs final distinction.
"""

def get_speaker_info_page_v3(speaker_name, speaker_email, speaker_affiliation, seminar_title, seminar_date, token, seminar_id=None):
    """
    Generate speaker information page with continuous server-side saving.
    """
    
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Speaker Information - University of Macau</title>
    <style>
        :root {{
            --primary: #003366;
            --primary-light: #0066CC;
            --accent: #FFD700;
            --success: #28a745;
            --error: #dc3545;
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
            padding: 20px;
            text-align: center;
        }}
        .header h1 {{ font-size: 24px; font-weight: 600; }}
        .header .subtitle {{ font-size: 14px; opacity: 0.9; margin-top: 5px; }}
        
        .container {{
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
        }}
        
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
            padding: 20px;
        }}
        
        .card-body {{ padding: 24px; }}
        
        .info-grid {{
            display: grid;
            grid-template-columns: 120px 1fr;
            gap: 12px 16px;
            margin-bottom: 20px;
        }}
        
        .info-label {{ color: var(--gray-600); font-size: 14px; font-weight: 500; }}
        .info-value {{ color: var(--gray-800); font-weight: 500; }}
        
        .form-group {{ margin-bottom: 20px; }}
        
        .form-label {{
            display: block;
            margin-bottom: 6px;
            font-weight: 500;
            color: var(--gray-800);
        }}
        
        .form-label .required {{ color: var(--error); margin-left: 2px; }}
        
        .form-input,
        .form-textarea,
        .form-select {{
            width: 100%;
            padding: 12px 16px;
            border: 2px solid var(--gray-300);
            border-radius: 8px;
            font-size: 16px;
            transition: border-color 0.2s, box-shadow 0.2s;
        }}
        
        .form-input:focus,
        .form-textarea:focus,
        .form-select:focus {{
            outline: none;
            border-color: var(--primary-light);
            box-shadow: 0 0 0 3px rgba(0,102,204,0.1);
        }}
        
        .form-textarea {{ min-height: 120px; resize: vertical; }}
        
        .saving-indicator {{
            position: fixed;
            top: 20px;
            right: 20px;
            background: var(--success);
            color: white;
            padding: 8px 16px;
            border-radius: 8px;
            font-size: 14px;
            opacity: 0;
            transition: opacity 0.3s;
            pointer-events: none;
        }}
        
        .saving-indicator.show {{ opacity: 1; }}
        
        .section-title {{
            font-size: 18px;
            font-weight: 600;
            color: var(--primary);
            margin-bottom: 16px;
            padding-bottom: 8px;
            border-bottom: 2px solid var(--gray-200);
        }}
        
        .checkbox-group {{
            display: flex;
            align-items: center;
            gap: 8px;
            margin-bottom: 12px;
            cursor: pointer;
        }}
        
        .checkbox-group input[type="checkbox"] {{
            width: 20px;
            height: 20px;
            cursor: pointer;
        }}
        
        .btn {{
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
            padding: 12px 24px;
            border: none;
            border-radius: 8px;
            font-size: 16px;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.2s;
        }}
        
        .btn-primary {{
            background: var(--primary);
            color: white;
        }}
        
        .btn-primary:hover:not(:disabled) {{
            background: var(--primary-light);
        }}
        
        .btn:disabled {{
            opacity: 0.6;
            cursor: not-allowed;
        }}
        
        .status-message {{
            padding: 16px;
            border-radius: 8px;
            margin-bottom: 20px;
            display: none;
        }}
        
        .status-message.show {{ display: block; }}
        .status-message.success {{ background: rgba(40,167,69,0.1); border: 1px solid var(--success); color: #155724; }}
        .status-message.error {{ background: rgba(220,53,69,0.1); border: 1px solid var(--error); color: #721c24; }}
        
        @media (max-width: 600px) {{
            .container {{ padding: 12px; }}
            .card-body {{ padding: 16px; }}
            .info-grid {{ grid-template-columns: 1fr; }}
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🏛️ University of Macau</h1>
        <div class="subtitle">Department of Economics · Faculty of Social Sciences</div>
    </div>
    
    <div class="container">
        <div id="savingIndicator" class="saving-indicator">💾 Saving...</div>
        <div id="statusMessage" class="status-message"></div>
        
        <div class="card">
            <div class="card-header">
                <h2>📝 Speaker Information</h2>
                <p>Your changes are saved automatically as you type.</p>
            </div>
            <div class="card-body">
                <div class="info-grid">
                    <div class="info-label">Seminar:</div>
                    <div class="info-value">{seminar_title or 'TBD'}</div>
                    <div class="info-label">Date:</div>
                    <div class="info-value">{seminar_date or 'To be confirmed'}</div>
                </div>
            </div>
        </div>
        
        <form id="speakerForm" class="card">
            <div class="card-body">
                <h3 class="section-title">Basic Information</h3>
                
                <div class="form-group">
                    <label class="form-label">Speaker Name <span class="required">*</span></label>
                    <input type="text" id="speakerName" class="form-input" value="{speaker_name or ''}" required>
                </div>
                
                <div class="form-group">
                    <label class="form-label">Final Talk Title <span class="required">*</span></label>
                    <input type="text" id="talkTitle" class="form-input" required>
                </div>
                
                <div class="form-group">
                    <label class="form-label">Abstract</label>
                    <textarea id="abstract" class="form-textarea" rows="6"
                              placeholder="Brief description of your talk"></textarea>
                </div>
                
                <h3 class="section-title" style="margin-top: 32px;">Travel Information</h3>
                
                <div class="form-group">
                    <label class="form-label">Passport Number</label>
                    <input type="text" id="passportNumber" class="form-input"
                           placeholder="For travel arrangements">
                </div>
                
                <div class="form-group">
                    <label class="form-label">Passport Country</label>
                    <input type="text" id="passportCountry" class="form-input"
                           placeholder="Country of issuance">
                </div>
                
                <div class="form-group">
                    <label class="form-label">Departure City</label>
                    <input type="text" id="departureCity" class="form-input"
                           placeholder="Where will you be traveling from?">
                </div>
                
                <div class="form-group">
                    <label class="form-label">Travel Method</label>
                    <select id="travelMethod" class="form-select">
                        <option value="">Select...</option>
                        <option value="flight">Flight</option>
                        <option value="train">Train</option>
                        <option value="other">Other</option>
                    </select>
                </div>
                
                <label class="checkbox-group">
                    <input type="checkbox" id="needsAccommodation">
                    <span>I need accommodation</span>
                </label>
                
                <div id="accommodationDates" style="display: none; margin-top: 16px;">
                    <div class="form-group">
                        <label class="form-label">Check-in Date</label>
                        <input type="date" id="checkInDate" class="form-input">
                    </div>
                    <div class="form-group">
                        <label class="form-label">Check-out Date</label>
                        <input type="date" id="checkOutDate" class="form-input">
                    </div>
                </div>
                
                <h3 class="section-title" style="margin-top: 32px;">Payment Information</h3>
                
                <div class="form-group">
                    <label class="form-label">Payment Email</label>
                    <input type="email" id="paymentEmail" class="form-input"
                           placeholder="For reimbursement/invoice">
                </div>
                
                <div class="form-group">
                    <label class="form-label">Beneficiary Name</label>
                    <input type="text" id="beneficiaryName" class="form-input">
                </div>
                
                <div class="form-group">
                    <label class="form-label">Bank Name</label>
                    <input type="text" id="bankName" class="form-input">
                </div>
                
                <div class="form-group">
                    <label class="form-label">SWIFT Code</label>
                    <input type="text" id="swiftCode" class="form-input">
                </div>
                
                <div class="form-group">
                    <label class="form-label">Bank Account Number</label>
                    <input type="text" id="bankAccount" class="form-input">
                </div>
                
                <div class="form-group">
                    <label class="form-label">Currency</label>
                    <select id="currency" class="form-select">
                        <option value="">Select...</option>
                        <option value="USD">USD</option>
                        <option value="EUR">EUR</option>
                        <option value="CNY">CNY</option>
                        <option value="MOP">MOP</option>
                    </select>
                </div>
                
                <h3 class="section-title" style="margin-top: 32px;">Technical Requirements</h3>
                
                <div class="form-group">
                    <label class="form-label">Special Requirements</label>
                    <textarea id="specialRequirements" class="form-textarea"
                              placeholder="Any requirements for your talk? (projector, microphone, etc.)"></textarea>
                </div>
                
                <div style="margin-top: 32px; text-align: center; color: var(--gray-600); font-size: 14px;">
                    <p>💾 All changes are saved automatically</p>
                </div>
            </div>
        </form>
    </div>
    
    <script>
        const TOKEN = '{token}';
        const API_BASE = '/api/v1/seminars/speaker-tokens';
        let saveTimeout = null;
        
        // Initialize
        document.addEventListener('DOMContentLoaded', function() {{
            loadData();
            setupAutoSave();
            setupEventListeners();
        }});
        
        // Load data from server
        async function loadData() {{
            try {{
                const response = await fetch(`${{API_BASE}}/${{TOKEN}}/info`);
                if (!response.ok) {{
                    const error = await response.text();
                    showStatus('Error loading data: ' + error, 'error');
                    return;
                }}
                
                const data = await response.json();
                populateForm(data);
            }} catch (e) {{
                console.error('Failed to load data:', e);
                showStatus('Failed to load data. Please refresh the page.', 'error');
            }}
        }}
        
        function populateForm(data) {{
            if (data.speaker_name) document.getElementById('speakerName').value = data.speaker_name;
            if (data.final_talk_title) document.getElementById('talkTitle').value = data.final_talk_title;
            if (data.abstract) document.getElementById('abstract').value = data.abstract;
            if (data.passport_number) document.getElementById('passportNumber').value = data.passport_number;
            if (data.passport_country) document.getElementById('passportCountry').value = data.passport_country;
            if (data.departure_city) document.getElementById('departureCity').value = data.departure_city;
            if (data.travel_method) document.getElementById('travelMethod').value = data.travel_method;
            if (data.needs_accommodation) {{
                document.getElementById('needsAccommodation').checked = true;
                document.getElementById('accommodationDates').style.display = 'block';
            }}
            if (data.check_in_date) document.getElementById('checkInDate').value = data.check_in_date;
            if (data.check_out_date) document.getElementById('checkOutDate').value = data.check_out_date;
            if (data.payment_email) document.getElementById('paymentEmail').value = data.payment_email;
            if (data.beneficiary_name) document.getElementById('beneficiaryName').value = data.beneficiary_name;
            if (data.bank_name) document.getElementById('bankName').value = data.bank_name;
            if (data.swift_code) document.getElementById('swiftCode').value = data.swift_code;
            if (data.bank_account_number) document.getElementById('bankAccount').value = data.bank_account_number;
            if (data.currency) document.getElementById('currency').value = data.currency;
            if (data.special_requirements) document.getElementById('specialRequirements').value = data.special_requirements;
        }}
        
        function setupAutoSave() {{
            document.querySelectorAll('input, textarea, select').forEach(input => {{
                input.addEventListener('change', () => {{
                    clearTimeout(saveTimeout);
                    saveTimeout = setTimeout(saveToServer, 500);
                }});
                
                input.addEventListener('blur', () => {{
                    clearTimeout(saveTimeout);
                    saveToServer();
                }});
            }});
        }}
        
        function setupEventListeners() {{
            document.getElementById('needsAccommodation').addEventListener('change', function() {{
                document.getElementById('accommodationDates').style.display = 
                    this.checked ? 'block' : 'none';
                saveToServer();
            }});
        }}
        
        async function saveToServer() {{
            const indicator = document.getElementById('savingIndicator');
            indicator.textContent = '💾 Saving...';
            indicator.classList.add('show');
            
            const data = gatherFormData();
            
            try {{
                const response = await fetch(`${{API_BASE}}/${{TOKEN}}/submit-info`, {{
                    method: 'POST',
                    headers: {{'Content-Type': 'application/json'}},
                    body: JSON.stringify(data)
                }});
                
                if (response.ok) {{
                    indicator.textContent = '✓ Saved';
                    setTimeout(() => indicator.classList.remove('show'), 1000);
                }} else {{
                    const error = await response.text();
                    indicator.textContent = '✗ Error';
                    console.error('Save failed:', error);
                }}
            }} catch (err) {{
                indicator.textContent = '✗ Error';
                console.error('Save error:', err);
            }}
        }}
        
        function gatherFormData() {{
            return {{
                speaker_name: document.getElementById('speakerName').value,
                final_talk_title: document.getElementById('talkTitle').value,
                abstract: document.getElementById('abstract').value,
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
                currency: document.getElementById('currency').value,
                special_requirements: document.getElementById('specialRequirements').value
            }};
        }}
        
        function showStatus(message, type) {{
            const statusDiv = document.getElementById('statusMessage');
            statusDiv.textContent = message;
            statusDiv.className = 'status-message ' + type + ' show';
            setTimeout(() => statusDiv.classList.remove('show'), 5000);
        }}
    </script>
</body>
</html>
"""
