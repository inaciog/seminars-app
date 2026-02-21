"""
Speaker Info Page v5 - With Categorized File Upload Support
Matches internal seminar details page structure.
"""

def get_speaker_info_page_v5(speaker_name, speaker_email, speaker_affiliation, seminar_title, seminar_date, token, seminar_id=None):
    """
    Generate speaker information page with categorized file upload support.
    Categories: cv, photo, passport, flight
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
            z-index: 1000;
        }}
        
        .saving-indicator.show {{ opacity: 1; }}
        .saving-indicator.saving {{ background: var(--warning); color: var(--gray-800); }}
        .saving-indicator.error {{ background: var(--error); }}
        
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
        
        .btn-danger {{
            background: var(--error);
            color: white;
            padding: 6px 12px;
            font-size: 14px;
        }}
        
        .btn-danger:hover:not(:disabled) {{
            background: #c82333;
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
        
        /* Tab Navigation */
        .tabs {{
            display: flex;
            gap: 8px;
            padding: 16px 24px;
            background: var(--gray-100);
            border-bottom: 1px solid var(--gray-200);
            overflow-x: auto;
        }}
        
        .tab {{
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 10px 16px;
            border: none;
            border-radius: 8px;
            font-size: 14px;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.2s;
            background: transparent;
            color: var(--gray-600);
            white-space: nowrap;
        }}
        
        .tab:hover {{
            background: var(--gray-200);
        }}
        
        .tab.active {{
            background: white;
            color: var(--primary);
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }}
        
        .tab-icon {{
            font-size: 16px;
        }}
        
        /* Tab Content */
        .tab-content {{
            display: none;
        }}
        
        .tab-content.active {{
            display: block;
        }}
        
        /* Categorized File Upload Styles */
        .file-category {{
            border: 1px solid var(--gray-300);
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 16px;
            background: white;
        }}
        
        .file-category-header {{
            display: flex;
            align-items: center;
            gap: 12px;
            margin-bottom: 12px;
        }}
        
        .file-category-icon {{
            font-size: 24px;
            width: 40px;
            height: 40px;
            display: flex;
            align-items: center;
            justify-content: center;
            background: var(--gray-100);
            border-radius: 8px;
        }}
        
        .file-category-title {{
            font-weight: 600;
            color: var(--gray-800);
        }}
        
        .file-category-hint {{
            font-size: 12px;
            color: var(--gray-600);
            margin-top: 2px;
        }}
        
        .file-input-wrapper {{
            position: relative;
            margin-top: 12px;
        }}
        
        .file-input {{
            position: absolute;
            opacity: 0;
            width: 100%;
            height: 100%;
            cursor: pointer;
        }}
        
        .file-input-button {{
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
            padding: 10px 16px;
            background: var(--primary);
            color: white;
            border-radius: 8px;
            font-size: 14px;
            font-weight: 500;
            cursor: pointer;
            transition: background 0.2s;
        }}
        
        .file-input-button:hover {{
            background: var(--primary-light);
        }}
        
        .file-input-button:disabled {{
            opacity: 0.6;
            cursor: not-allowed;
        }}
        
        .file-list {{
            margin-top: 12px;
        }}
        
        .file-item {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 10px 12px;
            background: rgba(40,167,69,0.05);
            border: 1px solid rgba(40,167,69,0.2);
            border-radius: 8px;
            margin-bottom: 8px;
        }}
        
        .file-item.uploading {{
            opacity: 0.7;
            background: var(--gray-100);
            border-color: var(--gray-300);
        }}
        
        .file-item.error {{
            background: rgba(220,53,69,0.05);
            border-color: rgba(220,53,69,0.2);
        }}
        
        .file-info {{
            display: flex;
            align-items: center;
            gap: 10px;
            flex: 1;
            min-width: 0;
        }}
        
        .file-name {{
            font-size: 14px;
            color: var(--gray-800);
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }}
        
        .file-actions {{
            display: flex;
            gap: 8px;
            flex-shrink: 0;
        }}
        
        .file-btn {{
            padding: 6px 12px;
            border: none;
            border-radius: 6px;
            font-size: 13px;
            cursor: pointer;
            transition: all 0.2s;
            text-decoration: none;
        }}
        
        .file-btn-download {{
            background: var(--success);
            color: white;
        }}
        
        .file-btn-download:hover {{
            background: #218838;
        }}
        
        .file-btn-delete {{
            background: transparent;
            color: var(--error);
            border: 1px solid var(--error);
        }}
        
        .file-btn-delete:hover {{
            background: var(--error);
            color: white;
        }}
        
        .upload-progress {{
            width: 100%;
            height: 3px;
            background: var(--gray-200);
            border-radius: 2px;
            margin-top: 8px;
            overflow: hidden;
        }}
        
        .upload-progress-bar {{
            height: 100%;
            background: var(--primary);
            transition: width 0.3s;
        }}
        
        @media (max-width: 600px) {{
            .container {{ padding: 12px; }}
            .card-body {{ padding: 16px; }}
            .info-grid {{ grid-template-columns: 1fr; }}
            .tabs {{ padding: 12px; }}
            .tab {{ padding: 8px 12px; font-size: 13px; }}
            .file-item {{ flex-direction: column; align-items: flex-start; gap: 10px; }}
            .file-actions {{ width: 100%; justify-content: flex-end; }}
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
            
            <!-- Tab Navigation -->
            <div class="tabs">
                <button class="tab active" data-tab="talk">
                    <span class="tab-icon">📄</span>
                    <span>Talk Info</span>
                </button>
                <button class="tab" data-tab="accommodation">
                    <span class="tab-icon">🏨</span>
                    <span>Accommodation</span>
                </button>
                <button class="tab" data-tab="travel">
                    <span class="tab-icon">✈️</span>
                    <span>Travel</span>
                </button>
                <button class="tab" data-tab="payment">
                    <span class="tab-icon">💳</span>
                    <span>Payment</span>
                </button>
                <button class="tab" data-tab="documents">
                    <span class="tab-icon">📎</span>
                    <span>Documents</span>
                </button>
            </div>
            
            <div class="card-body">
                <!-- Talk Info Tab -->
                <div id="tab-talk" class="tab-content active">
                    <h3 class="section-title">Talk Information</h3>
                    
                    <div class="info-grid" style="margin-bottom: 24px;">
                        <div class="info-label">Seminar:</div>
                        <div class="info-value">{seminar_title or 'TBD'}</div>
                        <div class="info-label">Date:</div>
                        <div class="info-value">{seminar_date or 'To be confirmed'}</div>
                    </div>
                    
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
                        <textarea id="abstract" class="form-textarea" rows="6" placeholder="Brief description of your talk"></textarea>
                    </div>
                </div>
                
                <!-- Accommodation Tab -->
                <div id="tab-accommodation" class="tab-content">
                    <h3 class="section-title">Accommodation Details</h3>
                    
                    <label class="checkbox-group">
                        <input type="checkbox" id="needsAccommodation">
                        <span>I need hotel accommodation</span>
                    </label>
                    
                    <div id="accommodationFields" style="display: none;">
                        <div class="form-group">
                            <label class="form-label">Check-in Date</label>
                            <input type="date" id="checkInDate" class="form-input">
                        </div>
                        
                        <div class="form-group">
                            <label class="form-label">Check-out Date</label>
                            <input type="date" id="checkOutDate" class="form-input">
                        </div>
                        
                        <div class="form-group">
                            <label class="form-label">Number of Nights</label>
                            <input type="number" id="accommodationNights" class="form-input" value="2">
                        </div>
                        
                        <div class="form-group">
                            <label class="form-label">Estimated Hotel Cost</label>
                            <input type="number" id="estimatedHotelCost" class="form-input" placeholder="0.00" step="0.01">
                        </div>
                    </div>
                </div>
                
                <!-- Travel Tab -->
                <div id="tab-travel" class="tab-content">
                    <h3 class="section-title">Travel Details</h3>
                    
                    <div class="form-group">
                        <label class="form-label">Departure City</label>
                        <input type="text" id="departureCity" class="form-input" placeholder="City, Country">
                    </div>
                    
                    <div class="form-group">
                        <label class="form-label">Travel Method</label>
                        <select id="travelMethod" class="form-select">
                            <option value="flight">Flight</option>
                            <option value="train">Train</option>
                            <option value="bus">Bus</option>
                            <option value="car">Car</option>
                            <option value="other">Other</option>
                        </select>
                    </div>
                    
                    <div class="form-group">
                        <label class="form-label">Estimated Travel Cost</label>
                        <input type="number" id="estimatedTravelCost" class="form-input" placeholder="0.00" step="0.01">
                    </div>
                    
                    <h3 class="section-title" style="margin-top: 32px;">Passport Information</h3>
                    
                    <div class="form-group">
                        <label class="form-label">Passport Number</label>
                        <input type="text" id="passportNumber" class="form-input" placeholder="Enter passport number">
                    </div>
                    
                    <div class="form-group">
                        <label class="form-label">Passport Country</label>
                        <input type="text" id="passportCountry" class="form-input" placeholder="Country of issue">
                    </div>
                </div>
                
                <!-- Payment Tab -->
                <div id="tab-payment" class="tab-content">
                    <h3 class="section-title">Payment Information</h3>
                    
                    <div class="form-group">
                        <label class="form-label">Payment Email</label>
                        <input type="email" id="paymentEmail" class="form-input" placeholder="email@example.com">
                    </div>
                    
                    <div class="form-group">
                        <label class="form-label">Beneficiary Name</label>
                        <input type="text" id="beneficiaryName" class="form-input" placeholder="Full name as on bank account">
                    </div>
                    
                    <div class="form-group">
                        <label class="form-label">Bank Account Number</label>
                        <input type="text" id="bankAccount" class="form-input" placeholder="Account/IBAN number">
                    </div>
                    
                    <div class="form-group">
                        <label class="form-label">Bank Name</label>
                        <input type="text" id="bankName" class="form-input" placeholder="Bank name">
                    </div>
                    
                    <div class="form-group">
                        <label class="form-label">Bank Address</label>
                        <textarea id="bankAddress" class="form-textarea" rows="3" placeholder="Full bank address"></textarea>
                    </div>
                    
                    <div class="form-group">
                        <label class="form-label">SWIFT/BIC Code</label>
                        <input type="text" id="swiftCode" class="form-input" placeholder="SWIFT code">
                    </div>
                    
                    <div class="form-group">
                        <label class="form-label">Currency</label>
                        <select id="currency" class="form-select">
                            <option value="USD">USD - US Dollar</option>
                            <option value="EUR">EUR - Euro</option>
                            <option value="GBP">GBP - British Pound</option>
                            <option value="CNY">CNY - Chinese Yuan</option>
                            <option value="MOP">MOP - Macanese Pataca</option>
                            <option value="Other">Other</option>
                        </select>
                    </div>
                    
                    <div class="form-group">
                        <label class="form-label">Beneficiary Address</label>
                        <textarea id="beneficiaryAddress" class="form-textarea" rows="3" placeholder="Your address for banking purposes"></textarea>
                    </div>
                </div>
                
                <!-- Documents Tab -->
                <div id="tab-documents" class="tab-content">
                    <h3 class="section-title">Required Documents</h3>
                    
                    <!-- CV Upload -->
                    <div class="file-category">
                        <div class="file-category-header">
                            <div class="file-category-icon">📄</div>
                            <div>
                                <div class="file-category-title">CV / Resume</div>
                                <div class="file-category-hint">Please upload your CV (PDF, DOC, DOCX)</div>
                            </div>
                        </div>
                        <div id="cv-file-list" class="file-list"></div>
                        
                        <div class="file-input-wrapper">
                            <input type="file" id="cv-upload" class="file-input" accept=".pdf,.doc,.docx"
                                   onchange="handleFileUpload(this, 'cv')">
                            <div class="file-input-button" id="cv-upload-btn">
                                <span>📤</span>
                                <span>Choose File</span>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Photo Upload -->
                    <div class="file-category">
                        <div class="file-category-header">
                            <div class="file-category-icon">🖼️</div>
                            <div>
                                <div class="file-category-title">High-Definition Photo</div>
                                <div class="file-category-hint">For the poster of your talk (JPG, PNG)</div>
                            </div>
                        </div>
                        <div id="photo-file-list" class="file-list"></div>
                        
                        <div class="file-input-wrapper">
                            <input type="file" id="photo-upload" class="file-input" accept=".jpg,.jpeg,.png"
                                   onchange="handleFileUpload(this, 'photo')">
                            <div class="file-input-button" id="photo-upload-btn">
                                <span>📤</span>
                                <span>Choose File</span>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Passport Upload -->
                    <div class="file-category">
                        <div class="file-category-header">
                            <div class="file-category-icon">🛂</div>
                            <div>
                                <div class="file-category-title">Passport Photo</div>
                                <div class="file-category-hint">For hotel booking and tax purposes (PDF, JPG, PNG)</div>
                            </div>
                        </div>
                        <div id="passport-file-list" class="file-list"></div>
                        
                        <div class="file-input-wrapper">
                            <input type="file" id="passport-upload" class="file-input" accept=".pdf,.jpg,.jpeg,.png"
                                   onchange="handleFileUpload(this, 'passport')">
                            <div class="file-input-button" id="passport-upload-btn">
                                <span>📤</span>
                                <span>Choose File</span>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Flight Upload -->
                    <div class="file-category">
                        <div class="file-category-header">
                            <div class="file-category-icon">✈️</div>
                            <div>
                                <div class="file-category-title">Flight Booking</div>
                                <div class="file-category-hint">Screenshot or PDF from airline/website (Kayak, Expedia, trip.com, etc.)</div>
                            </div>
                        </div>
                        <div id="flight-file-list" class="file-list"></div>
                        
                        <div class="file-input-wrapper">
                            <input type="file" id="flight-upload" class="file-input" accept=".pdf,.jpg,.jpeg,.png"
                                   onchange="handleFileUpload(this, 'flight')">
                            <div class="file-input-button" id="flight-upload-btn">
                                <span>📤</span>
                                <span>Choose File</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <div style="text-align: center; color: var(--gray-600); font-size: 14px; margin-top: 20px;">
            <p>💾 All changes are saved automatically</p>
        </div>
    </div>
    
    <script>
        const TOKEN = '{token}';
        const API_BASE = '/api/v1/seminars/speaker-tokens';
        let saveTimeout = null;
        let uploadedFiles = {{}}; // Track files by category
        
        // Initialize
        document.addEventListener('DOMContentLoaded', function() {{
            loadData();
            loadFiles();
            setupAutoSave();
            setupEventListeners();
            setupTabs();
        }});
        
        // ==================== TABS ====================
        
        function setupTabs() {{
            document.querySelectorAll('.tab').forEach(tab => {{
                tab.addEventListener('click', () => {{
                    const tabId = tab.dataset.tab;
                    
                    // Update active tab
                    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
                    tab.classList.add('active');
                    
                    // Update active content
                    document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
                    document.getElementById('tab-' + tabId).classList.add('active');
                }});
            }});
        }}
        
        // ==================== DATA LOADING & SAVING ====================
        
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
                document.getElementById('accommodationFields').style.display = 'block';
            }}
            if (data.check_in_date) document.getElementById('checkInDate').value = data.check_in_date;
            if (data.check_out_date) document.getElementById('checkOutDate').value = data.check_out_date;
            if (data.accommodation_nights) document.getElementById('accommodationNights').value = data.accommodation_nights;
            if (data.estimated_hotel_cost) document.getElementById('estimatedHotelCost').value = data.estimated_hotel_cost;
            if (data.estimated_travel_cost) document.getElementById('estimatedTravelCost').value = data.estimated_travel_cost;
            if (data.payment_email) document.getElementById('paymentEmail').value = data.payment_email;
            if (data.beneficiary_name) document.getElementById('beneficiaryName').value = data.beneficiary_name;
            if (data.bank_name) document.getElementById('bankName').value = data.bank_name;
            if (data.bank_address) document.getElementById('bankAddress').value = data.beneficiary_address;
            if (data.swift_code) document.getElementById('swiftCode').value = data.swift_code;
            if (data.bank_account_number) document.getElementById('bankAccount').value = data.bank_account_number;
            if (data.currency) document.getElementById('currency').value = data.currency;
        }}
        
        function setupAutoSave() {{
            document.querySelectorAll('input, textarea, select').forEach(input => {{
                if (input.type === 'file') return;
                
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
                document.getElementById('accommodationFields').style.display = this.checked ? 'block' : 'none';
                saveToServer();
            }});
        }}
        
        async function saveToServer() {{
            const indicator = document.getElementById('savingIndicator');
            indicator.textContent = '💾 Saving...';
            indicator.className = 'saving-indicator saving show';
            
            const data = gatherFormData();
            
            try {{
                const response = await fetch(`${{API_BASE}}/${{TOKEN}}/submit-info`, {{
                    method: 'POST',
                    headers: {{'Content-Type': 'application/json'}},
                    body: JSON.stringify(data)
                }});
                
                if (response.ok) {{
                    indicator.textContent = '✓ Saved';
                    indicator.className = 'saving-indicator show';
                    setTimeout(() => indicator.classList.remove('show'), 1000);
                }} else {{
                    const error = await response.text();
                    indicator.textContent = '✗ Error';
                    indicator.className = 'saving-indicator error show';
                    console.error('Save failed:', error);
                }}
            }} catch (err) {{
                indicator.textContent = '✗ Error';
                indicator.className = 'saving-indicator error show';
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
                estimated_travel_cost: document.getElementById('estimatedTravelCost').value || null,
                needs_accommodation: document.getElementById('needsAccommodation').checked,
                check_in_date: document.getElementById('checkInDate').value || null,
                check_out_date: document.getElementById('checkOutDate').value || null,
                accommodation_nights: document.getElementById('accommodationNights').value || null,
                estimated_hotel_cost: document.getElementById('estimatedHotelCost').value || null,
                payment_email: document.getElementById('paymentEmail').value,
                beneficiary_name: document.getElementById('beneficiaryName').value,
                bank_name: document.getElementById('bankName').value,
                bank_address: document.getElementById('bankAddress').value,
                swift_code: document.getElementById('swiftCode').value,
                bank_account_number: document.getElementById('bankAccount').value,
                currency: document.getElementById('currency').value,
                special_requirements: document.getElementById('bankAddress').value
            }};
        }}
        
        // ==================== FILE UPLOAD (CATEGORIZED) ====================
        
        async function loadFiles() {{
            try {{
                const response = await fetch(`${{API_BASE}}/${{TOKEN}}/files`);
                if (response.ok) {{
                    const files = await response.json();
                    
                    // Organize files by category
                    uploadedFiles = {{ cv: [], photo: [], passport: [], flight: [] }};
                    
                    files.forEach(file => {{
                        const category = file.file_category || 'other';
                        if (!uploadedFiles[category]) uploadedFiles[category] = [];
                        uploadedFiles[category].push({{
                            id: file.id,
                            name: file.original_filename,
                            size: formatFileSize(file.file_size),
                            uploaded_at: file.uploaded_at
                        }});
                    }});
                    
                    // Render each category
                    renderFileCategory('cv');
                    renderFileCategory('photo');
                    renderFileCategory('passport');
                    renderFileCategory('flight');
                }}
            }} catch (err) {{
                console.error('Failed to load files:', err);
            }}
        }}
        
        function renderFileCategory(category) {{
            const container = document.getElementById(category + '-file-list');
            const files = uploadedFiles[category] || [];
            
            if (files.length === 0) {{
                container.innerHTML = '';
                return;
            }}
            
            container.innerHTML = files.map(file => `
                <div class="file-item" data-id="${{file.id}}" data-category="${{category}}">
                    <div class="file-info">
                        <span>✅</span>
                        <span class="file-name">${{escapeHtml(file.name)}}</span>
                    </div>
                    <div class="file-actions">
                        <a href="${{API_BASE}}/${{TOKEN}}/files/${{file.id}}/download" 
                           class="file-btn file-btn-download" 
                           download>Download</a>
                        <button class="file-btn file-btn-delete" onclick="deleteFile(${{file.id}}, '${{category}}')">Delete</button>
                    </div>
                </div>
            `).join('');
        }}
        
        async function handleFileUpload(input, category) {{
            if (!input.files || input.files.length === 0) return;
            
            const file = input.files[0];
            const btn = document.getElementById(category + '-upload-btn');
            
            // Validate file size (10MB max)
            if (file.size > 10 * 1024 * 1024) {{
                showStatus(`File "${{file.name}}" is too large. Max size is 10MB.`, 'error');
                input.value = '';
                return;
            }}
            
            // Show uploading state
            btn.disabled = true;
            btn.innerHTML = '<span>⏳</span><span>Uploading...</span>';
            
            const formData = new FormData();
            formData.append('file', file);
            formData.append('category', category);
            
            try {{
                const response = await fetch(`${{API_BASE}}/${{TOKEN}}/upload`, {{
                    method: 'POST',
                    body: formData
                }});
                
                if (response.ok) {{
                    const result = await response.json();
                    
                    // Add to uploaded files
                    if (!uploadedFiles[category]) uploadedFiles[category] = [];
                    uploadedFiles[category].push({{
                        id: result.file_id,
                        name: file.name,
                        size: formatFileSize(file.size)
                    }});
                    
                    renderFileCategory(category);
                    showStatus(`"${{file.name}}" uploaded successfully`, 'success');
                }} else {{
                    const error = await response.text();
                    showStatus(`Failed to upload: ${{error}}`, 'error');
                }}
            }} catch (err) {{
                showStatus(`Failed to upload: ${{err.message}}`, 'error');
            }} finally {{
                btn.disabled = false;
                btn.innerHTML = '<span>📤</span><span>Choose File</span>';
                input.value = '';
            }}
        }}
        
        async function deleteFile(fileId, category) {{
            if (!confirm('Are you sure you want to delete this file?')) return;
            
            try {{
                const response = await fetch(`${{API_BASE}}/${{TOKEN}}/files/${{fileId}}`, {{
                    method: 'DELETE'
                }});
                
                if (response.ok) {{
                    // Remove from uploaded files
                    uploadedFiles[category] = uploadedFiles[category].filter(f => f.id !== fileId);
                    renderFileCategory(category);
                    showStatus('File deleted successfully', 'success');
                }} else {{
                    const error = await response.text();
                    showStatus('Failed to delete file: ' + error, 'error');
                }}
            }} catch (err) {{
                showStatus('Failed to delete file: ' + err.message, 'error');
            }}
        }}
        
        // ==================== UTILITIES ====================
        
        function formatFileSize(bytes) {{
            if (bytes === 0) return '0 B';
            const k = 1024;
            const sizes = ['B', 'KB', 'MB', 'GB'];
            const i = Math.floor(Math.log(bytes) / Math.log(k));
            return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
        }}
        
        function escapeHtml(text) {{
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }}
        
        function showStatus(message, type) {{
            const statusDiv = document.getElementById('statusMessage');
            statusDiv.innerHTML = message;
            statusDiv.className = 'status-message ' + type + ' show';
            setTimeout(() => statusDiv.classList.remove('show'), 5000);
        }}
    </script>
</body>
</html>
"""
