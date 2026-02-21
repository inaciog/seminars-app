"""
Speaker Info Page v4 - With File Upload Support
Complete implementation with file upload, listing, download, and delete functionality.
"""

def get_speaker_info_page_v4(speaker_name, speaker_email, speaker_affiliation, seminar_title, seminar_date, token, seminar_id=None):
    """
    Generate speaker information page with file upload support.
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
        
        /* File Upload Styles */
        .file-upload-area {{
            border: 2px dashed var(--gray-300);
            border-radius: 12px;
            padding: 32px;
            text-align: center;
            background: var(--gray-100);
            transition: all 0.2s;
            cursor: pointer;
        }}
        
        .file-upload-area:hover {{
            border-color: var(--primary-light);
            background: rgba(0,102,204,0.05);
        }}
        
        .file-upload-area.dragover {{
            border-color: var(--primary);
            background: rgba(0,102,204,0.1);
        }}
        
        .file-upload-area.uploading {{
            pointer-events: none;
            opacity: 0.7;
        }}
        
        .file-upload-icon {{
            font-size: 48px;
            margin-bottom: 16px;
        }}
        
        .file-upload-text {{
            color: var(--gray-600);
            margin-bottom: 8px;
        }}
        
        .file-upload-hint {{
            font-size: 12px;
            color: var(--gray-600);
        }}
        
        .file-input {{
            display: none;
        }}
        
        .file-list {{
            margin-top: 20px;
        }}
        
        .file-item {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 12px 16px;
            background: var(--gray-100);
            border-radius: 8px;
            margin-bottom: 8px;
            border: 1px solid var(--gray-200);
        }}
        
        .file-item.uploading {{
            opacity: 0.7;
        }}
        
        .file-item.error {{
            border-color: var(--error);
            background: rgba(220,53,69,0.05);
        }}
        
        .file-info {{
            display: flex;
            align-items: center;
            gap: 12px;
            flex: 1;
            min-width: 0;
        }}
        
        .file-icon {{
            font-size: 24px;
            flex-shrink: 0;
        }}
        
        .file-details {{
            min-width: 0;
            flex: 1;
        }}
        
        .file-name {{
            font-weight: 500;
            color: var(--gray-800);
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }}
        
        .file-meta {{
            font-size: 12px;
            color: var(--gray-600);
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
            background: var(--primary);
            color: white;
        }}
        
        .file-btn-download:hover {{
            background: var(--primary-light);
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
            height: 4px;
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
        
        .empty-state {{
            text-align: center;
            padding: 40px;
            color: var(--gray-600);
        }}
        
        .empty-state-icon {{
            font-size: 48px;
            margin-bottom: 12px;
            opacity: 0.5;
        }}
        
        @media (max-width: 600px) {{
            .container {{ padding: 12px; }}
            .card-body {{ padding: 16px; }}
            .info-grid {{ grid-template-columns: 1fr; }}
            .file-item {{ flex-direction: column; align-items: flex-start; gap: 12px; }}
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
                
                <h3 class="section-title" style="margin-top: 32px;">File Attachments</h3>
                <p style="color: var(--gray-600); margin-bottom: 16px; font-size: 14px;">
                    Upload your CV, photo, passport copy, flight tickets, or any other relevant documents.
                </p>
                
                <!-- File Upload Area -->
                <div class="file-upload-area" id="fileUploadArea">
                    <div class="file-upload-icon">📁</div>
                    <div class="file-upload-text">Click to upload or drag and drop files here</div>
                    <div class="file-upload-hint">Supported: PDF, DOC, DOCX, JPG, PNG (max 10MB each)</div>
                    <input type="file" id="fileInput" class="file-input" multiple accept=".pdf,.doc,.docx,.jpg,.jpeg,.png">
                </div>
                
                <!-- File List -->
                <div class="file-list" id="fileList">
                    <!-- Files will be listed here -->
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
        let uploadedFiles = {{}}; // Track files by ID
        
        // Initialize
        document.addEventListener('DOMContentLoaded', function() {{
            loadData();
            loadFiles();
            setupAutoSave();
            setupEventListeners();
            setupFileUpload();
        }});
        
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
                if (input.type === 'file') return; // Skip file input
                
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
        
        // ==================== FILE UPLOAD ====================
        
        function setupFileUpload() {{
            const uploadArea = document.getElementById('fileUploadArea');
            const fileInput = document.getElementById('fileInput');
            
            // Click to upload
            uploadArea.addEventListener('click', (e) => {{
                if (e.target !== fileInput) {{
                    fileInput.click();
                }}
            }});
            
            // File selection
            fileInput.addEventListener('change', (e) => {{
                handleFiles(e.target.files);
                fileInput.value = ''; // Reset for re-selection
            }});
            
            // Drag and drop
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
                handleFiles(e.dataTransfer.files);
            }});
        }}
        
        function handleFiles(files) {{
            Array.from(files).forEach(file => {{
                // Validate file size (10MB max)
                if (file.size > 10 * 1024 * 1024) {{
                    showStatus(`File "${{file.name}}" is too large. Max size is 10MB.`, 'error');
                    return;
                }}
                
                // Validate file type
                const allowedTypes = [
                    'application/pdf',
                    'application/msword',
                    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                    'image/jpeg',
                    'image/png'
                ];
                const allowedExts = ['.pdf', '.doc', '.docx', '.jpg', '.jpeg', '.png'];
                const ext = '.' + file.name.split('.').pop().toLowerCase();
                
                if (!allowedTypes.includes(file.type) && !allowedExts.includes(ext)) {{
                    showStatus(`File type not supported: ${{file.name}}`, 'error');
                    return;
                }}
                
                uploadFile(file);
            }});
        }}
        
        async function uploadFile(file) {{
            const tempId = 'temp_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
            
            // Add to UI immediately with uploading state
            const fileData = {{
                id: tempId,
                name: file.name,
                size: formatFileSize(file.size),
                type: file.type,
                uploading: true,
                progress: 0
            }};
            
            uploadedFiles[tempId] = fileData;
            renderFileList();
            
            const formData = new FormData();
            formData.append('file', file);
            
            try {{
                const response = await fetch(`${{API_BASE}}/${{TOKEN}}/upload`, {{
                    method: 'POST',
                    body: formData
                }});
                
                if (response.ok) {{
                    const result = await response.json();
                    
                    // Replace temp file with actual file
                    delete uploadedFiles[tempId];
                    uploadedFiles[result.file_id] = {{
                        id: result.file_id,
                        name: file.name,
                        size: formatFileSize(file.size),
                        type: file.type,
                        uploading: false,
                        uploaded_at: new Date().toISOString()
                    }};
                    
                    renderFileList();
                    showStatus(`"${{file.name}}" uploaded successfully`, 'success');
                }} else {{
                    const error = await response.text();
                    uploadedFiles[tempId].error = true;
                    uploadedFiles[tempId].errorMsg = error;
                    renderFileList();
                    showStatus(`Failed to upload "${{file.name}}": ${{error}}`, 'error');
                }}
            }} catch (err) {{
                uploadedFiles[tempId].error = true;
                uploadedFiles[tempId].errorMsg = err.message;
                renderFileList();
                showStatus(`Failed to upload "${{file.name}}": ${{err.message}}`, 'error');
            }}
        }}
        
        // ==================== FILE LISTING ====================
        
        async function loadFiles() {{
            try {{
                const response = await fetch(`${{API_BASE}}/${{TOKEN}}/files`);
                if (response.ok) {{
                    const files = await response.json();
                    
                    // Clear existing files
                    uploadedFiles = {{}};
                    
                    files.forEach(file => {{
                        uploadedFiles[file.id] = {{
                            id: file.id,
                            name: file.original_filename,
                            size: formatFileSize(file.file_size),
                            type: file.content_type,
                            category: file.file_category,
                            uploading: false,
                            uploaded_at: file.uploaded_at
                        }};
                    }});
                    
                    renderFileList();
                }}
            }} catch (err) {{
                console.error('Failed to load files:', err);
            }}
        }}
        
        function renderFileList() {{
            const fileList = document.getElementById('fileList');
            const files = Object.values(uploadedFiles);
            
            if (files.length === 0) {{
                fileList.innerHTML = `
                    <div class="empty-state">
                        <div class="empty-state-icon">📎</div>
                        <div>No files uploaded yet</div>
                    </div>
                `;
                return;
            }}
            
            fileList.innerHTML = files.map(file => {{
                const icon = getFileIcon(file.name);
                const uploadingClass = file.uploading ? 'uploading' : '';
                const errorClass = file.error ? 'error' : '';
                
                return `
                    <div class="file-item ${{uploadingClass}} ${{errorClass}}" data-id="${{file.id}}">
                        <div class="file-info">
                            <div class="file-icon">${{icon}}</div>
                            <div class="file-details">
                                <div class="file-name">${{escapeHtml(file.name)}}</div>
                                <div class="file-meta">
                                    ${{file.size}}
                                    ${{file.category ? ' · ' + escapeHtml(file.category) : ''}}
                                    ${{file.error ? ' · <span style="color: var(--error);">Upload failed</span>' : ''}}
                                </div>
                                ${{file.uploading ? `
                                    <div class="upload-progress">
                                        <div class="upload-progress-bar" style="width: ${{file.progress || 50}}%"></div>
                                    </div>
                                ` : ''}}
                            </div>
                        </div>
                        <div class="file-actions">
                            ${{!file.uploading && !file.error ? `
                                <a href="${{API_BASE}}/${{TOKEN}}/files/${{file.id}}/download" 
                                   class="file-btn file-btn-download" 
                                   download>Download</a>
                                <button class="file-btn file-btn-delete" onclick="deleteFile(${{file.id}})">Delete</button>
                            ` : ''}}
                            ${{file.error ? `
                                <button class="file-btn file-btn-delete" onclick="removeFailedFile('${{file.id}}')">Remove</button>
                            ` : ''}}
                        </div>
                    </div>
                `;
            }}).join('');
        }}
        
        // ==================== FILE OPERATIONS ====================
        
        async function deleteFile(fileId) {{
            if (!confirm('Are you sure you want to delete this file?')) {{
                return;
            }}
            
            try {{
                const response = await fetch(`${{API_BASE}}/${{TOKEN}}/files/${{fileId}}`, {{
                    method: 'DELETE'
                }});
                
                if (response.ok) {{
                    delete uploadedFiles[fileId];
                    renderFileList();
                    showStatus('File deleted successfully', 'success');
                }} else {{
                    const error = await response.text();
                    showStatus('Failed to delete file: ' + error, 'error');
                }}
            }} catch (err) {{
                showStatus('Failed to delete file: ' + err.message, 'error');
            }}
        }}
        
        function removeFailedFile(tempId) {{
            delete uploadedFiles[tempId];
            renderFileList();
        }}
        
        // ==================== UTILITIES ====================
        
        function getFileIcon(filename) {{
            const ext = filename.split('.').pop().toLowerCase();
            const icons = {{
                'pdf': '📄',
                'doc': '📝',
                'docx': '📝',
                'jpg': '🖼️',
                'jpeg': '🖼️',
                'png': '🖼️',
                'gif': '🖼️',
                'zip': '📦',
                'txt': '📃'
            }};
            return icons[ext] || '📎';
        }}
        
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
