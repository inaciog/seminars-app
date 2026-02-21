"""
Clean Speaker Info Page - Version 2.0
A fresh implementation with robust error handling and clear feedback.
"""

def get_speaker_info_page_v2(speaker_name, speaker_email, speaker_affiliation, seminar_title, seminar_date, token, seminar_id=None):
    """
    Generate a clean, robust speaker information page.
    
    Key features:
    - Clear visual feedback for all actions
    - Auto-save to localStorage
    - File upload with progress
    - Form submission with validation
    - Mobile-responsive design
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
        
        /* Header */
        .header {{
            background: var(--primary);
            color: white;
            padding: 20px;
            text-align: center;
        }}
        .header h1 {{ font-size: 24px; font-weight: 600; }}
        .header .subtitle {{ font-size: 14px; opacity: 0.9; margin-top: 5px; }}
        
        /* Container */
        .container {{
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
        }}
        
        /* Cards */
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
        
        /* Info display */
        .info-grid {{
            display: grid;
            grid-template-columns: 120px 1fr;
            gap: 12px 16px;
            margin-bottom: 20px;
        }}
        
        .info-label {{
            color: var(--gray-600);
            font-size: 14px;
            font-weight: 500;
        }}
        
        .info-value {{
            color: var(--gray-800);
            font-weight: 500;
        }}
        
        /* Form elements */
        .form-group {{
            margin-bottom: 20px;
        }}
        
        .form-label {{
            display: block;
            margin-bottom: 6px;
            font-weight: 500;
            color: var(--gray-800);
        }}
        
        .form-label .required {{
            color: var(--error);
            margin-left: 2px;
        }}
        
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
        
        .form-textarea {{
            min-height: 120px;
            resize: vertical;
        }}
        
        /* File upload */
        .file-upload {{
            border: 2px dashed var(--gray-300);
            border-radius: 8px;
            padding: 24px;
            text-align: center;
            cursor: pointer;
            transition: all 0.2s;
        }}
        
        .file-upload:hover {{
            border-color: var(--primary-light);
            background: var(--gray-100);
        }}
        
        .file-upload.has-file {{
            border-color: var(--success);
            background: rgba(40,167,69,0.05);
        }}
        
        .file-upload input[type="file"] {{
            display: none;
        }}
        
        .file-name {{
            margin-top: 8px;
            font-size: 14px;
            color: var(--gray-600);
        }}
        
        .upload-progress {{
            margin-top: 12px;
            height: 4px;
            background: var(--gray-200);
            border-radius: 2px;
            overflow: hidden;
            display: none;
        }}
        
        .upload-progress.active {{ display: block; }}
        
        .upload-progress-bar {{
            height: 100%;
            background: var(--primary-light);
            width: 0%;
            transition: width 0.3s;
        }}
        
        /* Checkboxes */
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
        
        /* Buttons */
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
        
        .btn-secondary {{
            background: var(--gray-200);
            color: var(--gray-800);
        }}
        
        .btn-secondary:hover:not(:disabled) {{
            background: var(--gray-300);
        }}
        
        .btn:disabled {{
            opacity: 0.6;
            cursor: not-allowed;
        }}
        
        .btn-group {{
            display: flex;
            gap: 12px;
            margin-top: 24px;
        }}
        
        /* Status messages */
        .status-message {{
            padding: 16px;
            border-radius: 8px;
            margin-bottom: 20px;
            display: none;
        }}
        
        .status-message.show {{ display: block; }}
        
        .status-message.success {{
            background: rgba(40,167,69,0.1);
            border: 1px solid var(--success);
            color: #155724;
        }}
        
        .status-message.error {{
            background: rgba(220,53,69,0.1);
            border: 1px solid var(--error);
            color: #721c24;
        }}
        
        .status-message.info {{
            background: rgba(0,102,204,0.1);
            border: 1px solid var(--primary-light);
            color: #004085;
        }}
        
        /* Auto-save indicator */
        .save-indicator {{
            position: fixed;
            top: 20px;
            right: 20px;
            background: var(--success);
            color: white;
            padding: 12px 20px;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.2);
            opacity: 0;
            transform: translateY(-20px);
            transition: all 0.3s;
            pointer-events: none;
        }}
        
        .save-indicator.show {{
            opacity: 1;
            transform: translateY(0);
        }}
        
        /* Section headers */
        .section-title {{
            font-size: 18px;
            font-weight: 600;
            color: var(--primary);
            margin-bottom: 16px;
            padding-bottom: 8px;
            border-bottom: 2px solid var(--gray-200);
        }}
        
        /* Responsive */
        @media (max-width: 600px) {{
            .container {{ padding: 12px; }}
            .card-body {{ padding: 16px; }}
            .info-grid {{ grid-template-columns: 1fr; }}
            .btn-group {{ flex-direction: column; }}
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🏛️ University of Macau</h1>
        <div class="subtitle">Department of Computer Science · Faculty of Science and Technology</div>
    </div>
    
    <div class="container">
        <!-- Status Messages -->
        <div id="statusMessage" class="status-message"></div>
        
        <!-- Save Indicator -->
        <div id="saveIndicator" class="save-indicator">✓ Saved</div>
        
        <!-- Welcome Card -->
        <div class="card">
            <div class="card-header">
                <h2>📝 Speaker Information</h2>
                <p>Please provide your details for the upcoming seminar. You can save your progress and return later.</p>
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
        
        <!-- Main Form -->
        <form id="speakerForm" class="card">
            <div class="card-body">
                <!-- Basic Information -->
                <h3 class="section-title">Basic Information</h3>
                
                <div class="form-group">
                    <label class="form-label">
                        Speaker Name <span class="required">*</span>
                    </label>
                    <input type="text" id="speakerName" class="form-input" 
                           value="{speaker_name or ''}" required
                           placeholder="Your full name">
                </div>
                
                <div class="form-group">
                    <label class="form-label">
                        Final Talk Title <span class="required">*</span>
                    </label>
                    <input type="text" id="talkTitle" class="form-input" required
                           placeholder="Title of your presentation">
                </div>
                
                <div class="form-group">
                    <label class="form-label">Abstract</label>
                    <textarea id="abstract" class="form-textarea" 
                              placeholder="Brief description of your talk (optional)"></textarea>
                </div>
                
                <!-- Travel Information -->
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
                
                <!-- Payment Information -->
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
                
                <!-- File Uploads -->
                <h3 class="section-title" style="margin-top: 32px;">Document Uploads</h3>
                
                <div class="form-group">
                    <label class="form-label">CV / Resume</label>
                    <div class="file-upload" id="cvUpload" onclick="document.getElementById('cvFile').click()">
                        <div>📄 Click to upload CV</div>
                        <div class="file-name" id="cvFileName">No file selected</div>
                        <div class="upload-progress" id="cvProgress">
                            <div class="upload-progress-bar"></div>
                        </div>
                    </div>
                    <input type="file" id="cvFile" accept=".pdf,.doc,.docx" 
                           onchange="handleFileSelect(this, 'cv')">
                </div>
                
                <div class="form-group">
                    <label class="form-label">Photo</label>
                    <div class="file-upload" id="photoUpload" onclick="document.getElementById('photoFile').click()">
                        <div>📷 Click to upload photo</div>
                        <div class="file-name" id="photoFileName">No file selected</div>
                        <div class="upload-progress" id="photoProgress">
                            <div class="upload-progress-bar"></div>
                        </div>
                    </div>
                    <input type="file" id="photoFile" accept="image/*" 
                           onchange="handleFileSelect(this, 'photo')">
                </div>
                
                <div class="form-group">
                    <label class="form-label">Passport Scan</label>
                    <div class="file-upload" id="passportUpload" onclick="document.getElementById('passportFile').click()">
                        <div>🛂 Click to upload passport</div>
                        <div class="file-name" id="passportFileName">No file selected</div>
                        <div class="upload-progress" id="passportProgress">
                            <div class="upload-progress-bar"></div>
                        </div>
                    </div>
                    <input type="file" id="passportFile" accept=".pdf,.jpg,.jpeg,.png" 
                           onchange="handleFileSelect(this, 'passport')">
                </div>
                
                <!-- Technical Requirements -->
                <h3 class="section-title" style="margin-top: 32px;">Technical Requirements</h3>
                
                <label class="checkbox-group">
                    <input type="checkbox" id="needsProjector" checked>
                    <span>Projector needed</span>
                </label>
                
                <label class="checkbox-group">
                    <input type="checkbox" id="needsMicrophone">
                    <span>Microphone needed</span>
                </label>
                
                <div class="form-group" style="margin-top: 16px;">
                    <label class="form-label">Special Requirements</label>
                    <textarea id="specialRequirements" class="form-textarea"
                              placeholder="Any other requirements for your talk?"></textarea>
                </div>
                
                <!-- Actions -->
                <div class="btn-group">
                    <button type="button" class="btn btn-secondary" onclick="saveDraft()">
                        💾 Save Draft
                    </button>
                    <button type="submit" class="btn btn-primary" id="submitBtn">
                        Submit Information
                    </button>
                </div>
            </div>
        </form>
    </div>
    
    <script>
        // Configuration
        const TOKEN = '{token}';
        const SEMINAR_ID = {seminar_id or 'null'};
        const API_BASE = '/api/v1/seminars/speaker-tokens';
        
        // State
        let uploadedFiles = {{}};
        let isSubmitting = false;
        
        // Initialize
        document.addEventListener('DOMContentLoaded', function() {{
            loadExistingData();
            setupAutoSave();
            setupEventListeners();
        }});
        
        // Load existing data from server first, then merge with localStorage draft
        async function loadExistingData() {{
            try {{
                const response = await fetch(`${{API_BASE}}/${{TOKEN}}/info`);
                if (response.ok) {{
                    const data = await response.json();
                    
                    // If already submitted, show message and disable form
                    if (data.has_submitted) {{
                        showStatus('You have already submitted this form. Thank you!', 'success');
                        document.querySelectorAll('input, textarea, select, button').forEach(el => {{
                            el.disabled = true;
                        }});
                        return;
                    }}
                    
                    // Populate form with server data
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
                    if (data.needs_projector !== undefined) document.getElementById('needsProjector').checked = data.needs_projector;
                    if (data.needs_microphone !== undefined) document.getElementById('needsMicrophone').checked = data.needs_microphone;
                    if (data.special_requirements) document.getElementById('specialRequirements').value = data.special_requirements;
                }}
            }} catch (e) {{
                console.error('Failed to load existing data:', e);
            }}
            
            // Now load localStorage draft (which may override server data if newer)
            loadDraft();
        }}
        
        // Event listeners
        function setupEventListeners() {{
            // Accommodation toggle
            document.getElementById('needsAccommodation').addEventListener('change', function() {{
                document.getElementById('accommodationDates').style.display = 
                    this.checked ? 'block' : 'none';
            }});
            
            // Form submission
            document.getElementById('speakerForm').addEventListener('submit', handleSubmit);
        }}
        
        // File handling
        function handleFileSelect(input, category) {{
            const file = input.files[0];
            if (!file) return;
            
            // Update UI
            const uploadDiv = document.getElementById(category + 'Upload');
            const fileNameDiv = document.getElementById(category + 'FileName');
            
            uploadDiv.classList.add('has-file');
            fileNameDiv.textContent = file.name;
            
            // Upload file
            uploadFile(file, category);
        }}
        
        async function uploadFile(file, category) {{
            const progressDiv = document.getElementById(category + 'Progress');
            const progressBar = progressDiv.querySelector('.upload-progress-bar');
            
            progressDiv.classList.add('active');
            progressBar.style.width = '0%';
            
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
                    uploadedFiles[category] = result.file_id;
                    progressBar.style.width = '100%';
                    showStatus('File uploaded successfully', 'success');
                }} else {{
                    throw new Error('Upload failed');
                }}
            }} catch (err) {{
                showStatus('Failed to upload file: ' + err.message, 'error');
                progressDiv.classList.remove('active');
            }}
        }}
        
        // Form submission
        async function handleSubmit(e) {{
            e.preventDefault();
            
            if (isSubmitting) return;
            isSubmitting = true;
            
            const submitBtn = document.getElementById('submitBtn');
            submitBtn.disabled = true;
            submitBtn.textContent = 'Submitting...';
            
            // Gather form data
            const data = {{
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
                needs_projector: document.getElementById('needsProjector').checked,
                needs_microphone: document.getElementById('needsMicrophone').checked,
                special_requirements: document.getElementById('specialRequirements').value
            }};
            
            try {{
                const response = await fetch(`${{API_BASE}}/${{TOKEN}}/submit-info`, {{
                    method: 'POST',
                    headers: {{'Content-Type': 'application/json'}},
                    body: JSON.stringify(data)
                }});
                
                if (response.ok) {{
                    showStatus('✅ Information submitted successfully! Thank you.', 'success');
                    localStorage.removeItem('speaker_info_draft_' + TOKEN);
                    
                    // Disable form
                    document.querySelectorAll('input, textarea, select, button').forEach(el => {{
                        el.disabled = true;
                    }});
                }} else {{
                    const error = await response.text();
                    throw new Error(error);
                }}
            }} catch (err) {{
                showStatus('❌ Error: ' + err.message, 'error');
                submitBtn.disabled = false;
                submitBtn.textContent = 'Submit Information';
            }}
            
            isSubmitting = false;
        }}
        
        // Draft saving
        function saveDraft() {{
            const data = gatherFormData();
            localStorage.setItem('speaker_info_draft_' + TOKEN, JSON.stringify(data));
            
            const indicator = document.getElementById('saveIndicator');
            indicator.classList.add('show');
            setTimeout(() => indicator.classList.remove('show'), 2000);
        }}
        
        function loadDraft() {{
            const draft = localStorage.getItem('speaker_info_draft_' + TOKEN);
            if (!draft) return;
            
            try {{
                const data = JSON.parse(draft);
                
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
                if (data.needs_projector !== undefined) document.getElementById('needsProjector').checked = data.needs_projector;
                if (data.needs_microphone !== undefined) document.getElementById('needsMicrophone').checked = data.needs_microphone;
                if (data.special_requirements) document.getElementById('specialRequirements').value = data.special_requirements;
            }} catch (e) {{
                console.error('Failed to load draft:', e);
            }}
        }}
        
        function setupAutoSave() {{
            let timeout;
            document.querySelectorAll('input, textarea, select').forEach(input => {{
                input.addEventListener('change', () => {{
                    clearTimeout(timeout);
                    timeout = setTimeout(saveDraft, 1000);
                }});
            }});
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
                check_in_date: document.getElementById('checkInDate').value,
                check_out_date: document.getElementById('checkOutDate').value,
                payment_email: document.getElementById('paymentEmail').value,
                beneficiary_name: document.getElementById('beneficiaryName').value,
                bank_name: document.getElementById('bankName').value,
                swift_code: document.getElementById('swiftCode').value,
                bank_account_number: document.getElementById('bankAccount').value,
                currency: document.getElementById('currency').value,
                needs_projector: document.getElementById('needsProjector').checked,
                needs_microphone: document.getElementById('needsMicrophone').checked,
                special_requirements: document.getElementById('specialRequirements').value
            }};
        }}
        
        // Status messages
        function showStatus(message, type) {{
            const statusDiv = document.getElementById('statusMessage');
            statusDiv.textContent = message;
            statusDiv.className = 'status-message ' + type + ' show';
            
            setTimeout(() => {{
                statusDiv.classList.remove('show');
            }}, 5000);
        }}
    </script>
</body>
</html>
"""
