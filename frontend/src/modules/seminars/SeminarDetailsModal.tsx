import { useState, useEffect, useCallback, useRef } from 'react';
import { fetchWithAuth, getAccessCode } from '@/api/client';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { X, Upload, FileText, Image, Plane, Home, CreditCard, User, Check, Trash2 } from 'lucide-react';
import { cn } from '@/lib/utils';

interface SeminarDetailsModalProps {
  seminarId: number;
  speakerName: string;
  onClose: () => void;
}

interface SeminarDetails {
  seminar_id: number;
  speaker_id: number | null;
  speaker_name: string | null;
  title: string;
  abstract: string | null;
  has_details: boolean;
  info: {
    id: number;
    talk_title: string | null;
    abstract: string | null;
    check_in_date: string | null;
    check_out_date: string | null;
    passport_number: string | null;
    passport_country: string | null;
    payment_email: string | null;
    beneficiary_name: string | null;
    bank_account_number: string | null;
    bank_name: string | null;
    bank_address: string | null;
    swift_code: string | null;
    currency: string | null;
    beneficiary_address: string | null;
    departure_city: string | null;
    travel_method: string | null;
    estimated_travel_cost: number | null;
    needs_accommodation: boolean;
    accommodation_nights: number | null;
    estimated_hotel_cost: number | null;
    cv_file_path: string | null;
    photo_file_path: string | null;
    passport_file_path: string | null;
    flight_booking_file_path: string | null;
    info_complete: boolean;
    submitted_at: string | null;
  } | null;
}

// Controlled input components
const TextInput = ({ value, onChange, placeholder, type = 'text', step }: { 
  value: string; 
  onChange: (v: string) => void; 
  placeholder?: string;
  type?: string;
  step?: string;
}) => (
  <input
    type={type}
    step={step}
    value={value}
    onChange={(e) => onChange(e.target.value)}
    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
    placeholder={placeholder}
  />
);

const TextArea = ({ value, onChange, placeholder, rows = 3 }: { 
  value: string; 
  onChange: (v: string) => void; 
  placeholder?: string;
  rows?: number;
}) => (
  <textarea
    value={value}
    onChange={(e) => onChange(e.target.value)}
    rows={rows}
    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
    placeholder={placeholder}
  />
);

const Select = ({ value, onChange, children }: { 
  value: string; 
  onChange: (v: string) => void; 
  children: React.ReactNode;
}) => (
  <select
    value={value}
    onChange={(e) => onChange(e.target.value)}
    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
  >
    {children}
  </select>
);

const Checkbox = ({ checked, onChange }: { 
  checked: boolean; 
  onChange: (v: boolean) => void; 
}) => (
  <input
    type="checkbox"
    checked={checked}
    onChange={(e) => onChange(e.target.checked)}
    className="w-4 h-4 text-primary-600 rounded border-gray-300"
  />
);

// Form field wrapper
function FormField({ label, children, required }: { label: string; children: React.ReactNode; required?: boolean }) {
  return (
    <div>
      <label className="block text-sm font-medium text-gray-700 mb-1">
        {label} {required && <span className="text-red-500">*</span>}
      </label>
      {children}
    </div>
  );
}

// Form section wrapper - MUST be outside main component to prevent focus loss
function FormSection({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="space-y-4">
      <h3 className="font-semibold text-gray-900 border-b pb-2">{title}</h3>
      {children}
    </div>
  );
}

export function SeminarDetailsModal({ seminarId, speakerName, onClose }: SeminarDetailsModalProps) {
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState<'talk' | 'accommodation' | 'travel' | 'payment' | 'documents'>('talk');
  const [isSaving, setIsSaving] = useState(false);
  const [uploadingFile, setUploadingFile] = useState<string | null>(null);
  const [deletingFile, setDeletingFile] = useState<number | null>(null);
  
  // Use refs to store form values to avoid re-render focus loss
  const formValues = useRef<Record<string, string | boolean>>({
    title: '',
    abstract: '',
    check_in_date: '',
    check_out_date: '',
    passport_number: '',
    passport_country: '',
    payment_email: '',
    beneficiary_name: '',
    bank_account_number: '',
    bank_name: '',
    bank_address: '',
    swift_code: '',
    currency: 'USD',
    beneficiary_address: '',
    departure_city: '',
    travel_method: 'flight',
    estimated_travel_cost: '',
    needs_accommodation: true,
    accommodation_nights: '2',
    estimated_hotel_cost: '',
  });
  
  const [initialized, setInitialized] = useState(false);
  const [, forceUpdate] = useState({});
  
  const { data: details, isLoading } = useQuery({
    queryKey: ['seminar-details', seminarId],
    queryFn: async (): Promise<SeminarDetails> => {
      const response = await fetchWithAuth(`/api/v1/seminars/seminars/${seminarId}/details`);
      if (!response.ok) throw new Error('Failed to fetch details');
      return response.json();
    },
    staleTime: Infinity,
  });

  // Fetch uploaded files
  const { data: files, refetch: refetchFiles } = useQuery({
    queryKey: ['seminar-files', seminarId],
    queryFn: async () => {
      const response = await fetchWithAuth(`/api/v1/seminars/seminars/${seminarId}/files`);
      if (!response.ok) throw new Error('Failed to fetch files');
      return response.json();
    },
  });

  // Helper to get files by category
  const getFilesByCategory = (category: string) => {
    return files?.filter((f: any) => f.file_category === category) || [];
  };

  // Initialize form values from server data ONCE
  useEffect(() => {
    if (details && !initialized) {
      formValues.current = {
        title: details.title || '',
        abstract: details.abstract || '',
        check_in_date: details.info?.check_in_date || '',
        check_out_date: details.info?.check_out_date || '',
        passport_number: details.info?.passport_number || '',
        passport_country: details.info?.passport_country || '',
        payment_email: details.info?.payment_email || '',
        beneficiary_name: details.info?.beneficiary_name || '',
        bank_account_number: details.info?.bank_account_number || '',
        bank_name: details.info?.bank_name || '',
        bank_address: details.info?.bank_address || '',
        swift_code: details.info?.swift_code || '',
        currency: details.info?.currency || 'USD',
        beneficiary_address: details.info?.beneficiary_address || '',
        departure_city: details.info?.departure_city || '',
        travel_method: details.info?.travel_method || 'flight',
        estimated_travel_cost: details.info?.estimated_travel_cost?.toString() || '',
        needs_accommodation: details.info?.needs_accommodation ?? true,
        accommodation_nights: details.info?.accommodation_nights?.toString() || '2',
        estimated_hotel_cost: details.info?.estimated_hotel_cost?.toString() || '',
      };
      setInitialized(true);
      forceUpdate({}); // Trigger one re-render to populate defaultValues
    }
  }, [details, initialized]);

  // Update a single field and trigger re-render for controlled components
  const [, setFormVersion] = useState(0);
  const updateField = useCallback((field: string, value: string | boolean) => {
    formValues.current[field] = value;
    setFormVersion(v => v + 1); // Trigger re-render
  }, []);

  const handleSubmit = useCallback(async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSaving(true);
    
    const payload = {
      title: formValues.current.title,
      abstract: formValues.current.abstract,
      check_in_date: formValues.current.check_in_date,
      check_out_date: formValues.current.check_out_date,
      passport_number: formValues.current.passport_number,
      passport_country: formValues.current.passport_country,
      payment_email: formValues.current.payment_email,
      beneficiary_name: formValues.current.beneficiary_name,
      bank_account_number: formValues.current.bank_account_number,
      bank_name: formValues.current.bank_name,
      bank_address: formValues.current.bank_address,
      swift_code: formValues.current.swift_code,
      currency: formValues.current.currency,
      beneficiary_address: formValues.current.beneficiary_address,
      departure_city: formValues.current.departure_city,
      travel_method: formValues.current.travel_method,
      estimated_travel_cost: formValues.current.estimated_travel_cost,
      needs_accommodation: formValues.current.needs_accommodation,
      accommodation_nights: formValues.current.accommodation_nights,
      estimated_hotel_cost: formValues.current.estimated_hotel_cost,
    };
    
    try {
      const response = await fetchWithAuth(`/api/v1/seminars/seminars/${seminarId}/details`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      if (!response.ok) throw new Error('Failed to save details');
      
      queryClient.setQueryData(['seminar-details', seminarId], (old: any) => ({
        ...old,
        title: formValues.current.title,
        abstract: formValues.current.abstract,
        info: {
          ...old?.info,
          check_in_date: formValues.current.check_in_date,
          check_out_date: formValues.current.check_out_date,
          passport_number: formValues.current.passport_number,
          passport_country: formValues.current.passport_country,
          payment_email: formValues.current.payment_email,
          beneficiary_name: formValues.current.beneficiary_name,
          bank_account_number: formValues.current.bank_account_number,
          bank_name: formValues.current.bank_name,
          bank_address: formValues.current.bank_address,
          swift_code: formValues.current.swift_code,
          currency: formValues.current.currency,
          beneficiary_address: formValues.current.beneficiary_address,
          departure_city: formValues.current.departure_city,
          travel_method: formValues.current.travel_method,
          estimated_travel_cost: formValues.current.estimated_travel_cost ? parseFloat(formValues.current.estimated_travel_cost as string) : null,
          needs_accommodation: formValues.current.needs_accommodation,
          accommodation_nights: formValues.current.accommodation_nights ? parseInt(formValues.current.accommodation_nights as string) : null,
          estimated_hotel_cost: formValues.current.estimated_hotel_cost ? parseFloat(formValues.current.estimated_hotel_cost as string) : null,
        },
      }));
      queryClient.invalidateQueries({ queryKey: ['seminars'] });
      alert('Saved successfully!');
    } catch (error) {
      alert('Failed to save: ' + (error as Error).message);
    } finally {
      setIsSaving(false);
    }
  }, [seminarId, queryClient]);

  // File upload handler
  const handleFileUpload = async (file: File, fileType: 'cv' | 'photo' | 'passport' | 'flight') => {
    setUploadingFile(fileType);
    const uploadData = new FormData();
    uploadData.append('file', file);
    uploadData.append('file_category', fileType);
    
    try {
      const response = await fetchWithAuth(`/api/v1/seminars/seminars/${seminarId}/upload`, {
        method: 'POST',
        body: uploadData,
      });
      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Upload failed: ${errorText}`);
      }
      
      // Refetch both details and files list
      queryClient.invalidateQueries({ queryKey: ['seminar-details', seminarId] });
      refetchFiles();
      alert('File uploaded successfully!');
    } catch (error) {
      alert('Upload failed: ' + (error as Error).message);
    } finally {
      setUploadingFile(null);
    }
  };

  // File delete handler
  const handleFileDelete = async (fileId: number) => {
    if (!confirm('Are you sure you want to delete this file?')) return;
    
    setDeletingFile(fileId);
    try {
      const response = await fetchWithAuth(`/api/v1/seminars/seminars/${seminarId}/files/${fileId}`, {
        method: 'DELETE',
      });
      if (!response.ok) throw new Error('Delete failed');
      
      // Refetch files list
      refetchFiles();
      alert('File deleted successfully!');
    } catch (error) {
      alert('Delete failed: ' + (error as Error).message);
    } finally {
      setDeletingFile(null);
    }
  };

  const TabButton = useCallback(({ id, label, icon: Icon }: { id: typeof activeTab; label: string; icon: any }) => (
    <button
      type="button"
      onClick={() => setActiveTab(id)}
      className={cn(
        'flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors',
        activeTab === id
          ? 'bg-primary-100 text-primary-700'
          : 'text-gray-600 hover:bg-gray-100'
      )}
    >
      <Icon className="w-4 h-4" />
      {label}
    </button>
  ), [activeTab]);

  if (isLoading) {
    return (
      <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
        <div className="bg-white rounded-xl p-6 w-full max-w-4xl max-h-[90vh] overflow-hidden">
          <div className="text-center py-12">Loading details...</div>
        </div>
      </div>
    );
  }

  const v = formValues.current;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl w-full max-w-4xl max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b">
          <div>
            <h2 className="text-xl font-semibold text-gray-900">Seminar Details</h2>
            <p className="text-sm text-gray-600">{speakerName}</p>
          </div>
          <button onClick={onClose} className="p-2 hover:bg-gray-100 rounded-lg">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Tabs */}
        <div className="flex gap-2 px-6 py-3 border-b bg-gray-50 overflow-x-auto">
          <TabButton id="talk" label="Talk Info" icon={FileText} />
          <TabButton id="accommodation" label="Accommodation" icon={Home} />
          <TabButton id="travel" label="Travel" icon={Plane} />
          <TabButton id="payment" label="Payment" icon={CreditCard} />
          <TabButton id="documents" label="Documents" icon={Upload} />
        </div>

        {/* Content */}
        <form onSubmit={handleSubmit} className="flex-1 overflow-y-auto">
          <div className="p-6">
            {/* Talk Info Tab */}
            {activeTab === 'talk' && (
              <div className="space-y-6">
                <FormSection title="Talk Information">
                  <div className="grid grid-cols-1 gap-4">
                    <FormField label="Talk Title">
                      <TextInput 
                        value={v.title as string} 
                        onChange={(val) => updateField('title', val)}
                        placeholder="Enter talk title"
                      />
                    </FormField>
                    
                    <FormField label="Abstract">
                      <TextArea 
                        value={v.abstract as string} 
                        onChange={(val) => updateField('abstract', val)}
                        placeholder="Enter talk abstract"
                        rows={6}
                      />
                    </FormField>
                  </div>
                </FormSection>
              </div>
            )}

            {/* Accommodation Tab */}
            {activeTab === 'accommodation' && (
              <div className="space-y-6">
                <FormSection title="Accommodation Details">
                  <div className="flex items-center gap-3 mb-4">
                    <Checkbox
                      checked={v.needs_accommodation as boolean}
                      onChange={(val) => updateField('needs_accommodation', val)}
                    />
                    <label className="text-sm text-gray-700">
                      Needs hotel accommodation
                    </label>
                  </div>

                  {v.needs_accommodation && (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <FormField label="Check-in Date">
                        <TextInput 
                          type="date"
                          value={v.check_in_date as string} 
                          onChange={(val) => updateField('check_in_date', val)}
                        />
                      </FormField>
                      
                      <FormField label="Check-out Date">
                        <TextInput 
                          type="date"
                          value={v.check_out_date as string} 
                          onChange={(val) => updateField('check_out_date', val)}
                        />
                      </FormField>
                      
                      <FormField label="Number of Nights">
                        <TextInput 
                          type="number"
                          value={v.accommodation_nights as string} 
                          onChange={(val) => updateField('accommodation_nights', val)}
                        />
                      </FormField>
                      
                      <FormField label="Estimated Hotel Cost">
                        <TextInput 
                          type="number"
                          step="0.01"
                          value={v.estimated_hotel_cost as string} 
                          onChange={(val) => updateField('estimated_hotel_cost', val)}
                          placeholder="0.00"
                        />
                      </FormField>
                    </div>
                  )}
                </FormSection>
              </div>
            )}

            {/* Travel Tab */}
            {activeTab === 'travel' && (
              <div className="space-y-6">
                <FormSection title="Travel Details">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <FormField label="Departure City">
                      <TextInput 
                        value={v.departure_city as string} 
                        onChange={(val) => updateField('departure_city', val)}
                        placeholder="City, Country"
                      />
                    </FormField>
                    
                    <FormField label="Travel Method">
                      <Select 
                        value={v.travel_method as string} 
                        onChange={(val) => updateField('travel_method', val)}
                      >
                        <option value="flight">Flight</option>
                        <option value="train">Train</option>
                        <option value="bus">Bus</option>
                        <option value="car">Car</option>
                        <option value="other">Other</option>
                      </Select>
                    </FormField>
                    
                    <FormField label="Estimated Travel Cost">
                      <TextInput 
                        type="number"
                        step="0.01"
                        value={v.estimated_travel_cost as string} 
                        onChange={(val) => updateField('estimated_travel_cost', val)}
                        placeholder="0.00"
                      />
                    </FormField>
                  </div>
                </FormSection>

                <FormSection title="Passport Information">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <FormField label="Passport Number">
                      <TextInput 
                        value={v.passport_number as string} 
                        onChange={(val) => updateField('passport_number', val)}
                        placeholder="Enter passport number"
                      />
                    </FormField>
                    
                    <FormField label="Passport Country">
                      <TextInput 
                        value={v.passport_country as string} 
                        onChange={(val) => updateField('passport_country', val)}
                        placeholder="Country of issue"
                      />
                    </FormField>
                  </div>
                </FormSection>
              </div>
            )}

            {/* Payment Tab */}
            {activeTab === 'payment' && (
              <div className="space-y-6">
                <FormSection title="Payment Information">
                  <div className="grid grid-cols-1 gap-4">
                    <FormField label="Payment Email">
                      <TextInput 
                        type="email"
                        value={v.payment_email as string} 
                        onChange={(val) => updateField('payment_email', val)}
                        placeholder="email@example.com"
                      />
                    </FormField>
                    
                    <FormField label="Beneficiary Name">
                      <TextInput 
                        value={v.beneficiary_name as string} 
                        onChange={(val) => updateField('beneficiary_name', val)}
                        placeholder="Full name as on bank account"
                      />
                    </FormField>
                    
                    <FormField label="Bank Account Number">
                      <TextInput 
                        value={v.bank_account_number as string} 
                        onChange={(val) => updateField('bank_account_number', val)}
                        placeholder="Account/IBAN number"
                      />
                    </FormField>
                    
                    <FormField label="Bank Name">
                      <TextInput 
                        value={v.bank_name as string} 
                        onChange={(val) => updateField('bank_name', val)}
                        placeholder="Bank name"
                      />
                    </FormField>
                    
                    <FormField label="Bank Address">
                      <TextArea 
                        value={v.bank_address as string} 
                        onChange={(val) => updateField('bank_address', val)}
                        placeholder="Full bank address"
                        rows={3}
                      />
                    </FormField>
                    
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <FormField label="SWIFT/BIC Code">
                        <TextInput 
                          value={v.swift_code as string} 
                          onChange={(val) => updateField('swift_code', val)}
                          placeholder="SWIFT code"
                        />
                      </FormField>
                      
                      <FormField label="Currency">
                        <Select 
                          value={v.currency as string} 
                          onChange={(val) => updateField('currency', val)}
                        >
                          <option value="USD">USD - US Dollar</option>
                          <option value="EUR">EUR - Euro</option>
                          <option value="GBP">GBP - British Pound</option>
                          <option value="CNY">CNY - Chinese Yuan</option>
                          <option value="JPY">JPY - Japanese Yen</option>
                          <option value="CAD">CAD - Canadian Dollar</option>
                          <option value="AUD">AUD - Australian Dollar</option>
                          <option value="CHF">CHF - Swiss Franc</option>
                          <option value="HKD">HKD - Hong Kong Dollar</option>
                          <option value="SGD">SGD - Singapore Dollar</option>
                          <option value="Other">Other</option>
                        </Select>
                      </FormField>
                    </div>
                    
                    <FormField label="Beneficiary Address">
                      <TextArea 
                        value={v.beneficiary_address as string} 
                        onChange={(val) => updateField('beneficiary_address', val)}
                        placeholder="Your address for banking purposes"
                        rows={3}
                      />
                    </FormField>
                  </div>
                </FormSection>
              </div>
            )}

            {/* Documents Tab */}
            {activeTab === 'documents' && (
              <div className="space-y-4">
                <FormSection title="Required Documents">
                  {/* CV Upload */}
                  <div className="p-4 border border-gray-200 rounded-lg">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <FileText className="w-5 h-5 text-primary-600" />
                        <span className="font-medium">CV / Resume</span>
                      </div>
                    </div>
                    {/* List uploaded CVs */}
                    {getFilesByCategory('cv').length > 0 && (
                      <div className="mb-3 space-y-2">
                        {getFilesByCategory('cv').map((file: any) => (
                          <div key={file.id} className="flex items-center justify-between bg-green-50 p-2 rounded">
                            <span className="text-sm text-green-700 truncate flex-1">{file.original_filename}</span>
                            <div className="flex items-center gap-2">
                              <a 
                                href={`/api/v1/seminars/seminars/${seminarId}/files/${file.id}/download?access_code=${getAccessCode() || ''}`}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="text-sm text-primary-600 hover:text-primary-700 flex items-center gap-1"
                              >
                                <Check className="w-4 h-4" /> Download
                              </a>
                              <button
                                onClick={() => handleFileDelete(file.id)}
                                disabled={deletingFile === file.id}
                                className="text-sm text-red-600 hover:text-red-700 flex items-center gap-1 disabled:opacity-50"
                                title="Delete file"
                              >
                                <Trash2 className="w-4 h-4" />
                              </button>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                    <input
                      type="file"
                      
                      disabled={uploadingFile === 'cv'}
                      onChange={(e) => e.target.files?.[0] && handleFileUpload(e.target.files[0], 'cv')}
                      className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-medium file:bg-primary-50 file:text-primary-700 hover:file:bg-primary-100 disabled:opacity-50"
                    />
                    <p className="text-xs text-gray-500 mt-1">Please upload your CV (PDF, DOC, DOCX)</p>
                  </div>

                  {/* Photo Upload */}
                  <div className="p-4 border border-gray-200 rounded-lg">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <Image className="w-5 h-5 text-primary-600" />
                        <span className="font-medium">High-Definition Photo</span>
                      </div>
                    </div>
                    {/* List uploaded photos */}
                    {getFilesByCategory('photo').length > 0 && (
                      <div className="mb-3 space-y-2">
                        {getFilesByCategory('photo').map((file: any) => (
                          <div key={file.id} className="flex items-center justify-between bg-green-50 p-2 rounded">
                            <span className="text-sm text-green-700 truncate flex-1">{file.original_filename}</span>
                            <div className="flex items-center gap-2">
                              <a 
                                href={`/api/v1/seminars/seminars/${seminarId}/files/${file.id}/download?access_code=${getAccessCode() || ''}`}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="text-sm text-primary-600 hover:text-primary-700 flex items-center gap-1"
                              >
                                <Check className="w-4 h-4" /> Download
                              </a>
                              <button
                                onClick={() => handleFileDelete(file.id)}
                                disabled={deletingFile === file.id}
                                className="text-sm text-red-600 hover:text-red-700 flex items-center gap-1 disabled:opacity-50"
                                title="Delete file"
                              >
                                <Trash2 className="w-4 h-4" />
                              </button>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                    <input
                      type="file"
                      disabled={uploadingFile === 'photo'}
                      onChange={(e) => e.target.files?.[0] && handleFileUpload(e.target.files[0], 'photo')}
                      className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-medium file:bg-primary-50 file:text-primary-700 hover:file:bg-primary-100 disabled:opacity-50"
                    />
                    <p className="text-xs text-gray-500 mt-1">For the poster of your talk (JPG, PNG)</p>
                  </div>

                  {/* Passport Upload */}
                  <div className="p-4 border border-gray-200 rounded-lg">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <User className="w-5 h-5 text-primary-600" />
                        <span className="font-medium">Passport Photo</span>
                      </div>
                    </div>
                    {/* List uploaded passports */}
                    {getFilesByCategory('passport').length > 0 && (
                      <div className="mb-3 space-y-2">
                        {getFilesByCategory('passport').map((file: any) => (
                          <div key={file.id} className="flex items-center justify-between bg-green-50 p-2 rounded">
                            <span className="text-sm text-green-700 truncate flex-1">{file.original_filename}</span>
                            <div className="flex items-center gap-2">
                              <a 
                                href={`/api/v1/seminars/seminars/${seminarId}/files/${file.id}/download?access_code=${getAccessCode() || ''}`}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="text-sm text-primary-600 hover:text-primary-700 flex items-center gap-1"
                              >
                                <Check className="w-4 h-4" /> Download
                              </a>
                              <button
                                onClick={() => handleFileDelete(file.id)}
                                disabled={deletingFile === file.id}
                                className="text-sm text-red-600 hover:text-red-700 flex items-center gap-1 disabled:opacity-50"
                                title="Delete file"
                              >
                                <Trash2 className="w-4 h-4" />
                              </button>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                    <input
                      type="file"
                      disabled={uploadingFile === 'passport'}
                      onChange={(e) => e.target.files?.[0] && handleFileUpload(e.target.files[0], 'passport')}
                      className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-medium file:bg-primary-50 file:text-primary-700 hover:file:bg-primary-100 disabled:opacity-50"
                    />
                    <p className="text-xs text-gray-500 mt-1">For hotel booking and tax purposes (PDF, JPG, PNG)</p>
                  </div>

                  {/* Flight Upload */}
                  <div className="p-4 border border-gray-200 rounded-lg">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <Plane className="w-5 h-5 text-primary-600" />
                        <span className="font-medium">Flight Booking</span>
                      </div>
                    </div>
                    {/* List uploaded flight bookings */}
                    {getFilesByCategory('flight').length > 0 && (
                      <div className="mb-3 space-y-2">
                        {getFilesByCategory('flight').map((file: any) => (
                          <div key={file.id} className="flex items-center justify-between bg-green-50 p-2 rounded">
                            <span className="text-sm text-green-700 truncate flex-1">{file.original_filename}</span>
                            <div className="flex items-center gap-2">
                              <a 
                                href={`/api/v1/seminars/seminars/${seminarId}/files/${file.id}/download?access_code=${getAccessCode() || ''}`}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="text-sm text-primary-600 hover:text-primary-700 flex items-center gap-1"
                              >
                                <Check className="w-4 h-4" /> Download
                              </a>
                              <button
                                onClick={() => handleFileDelete(file.id)}
                                disabled={deletingFile === file.id}
                                className="text-sm text-red-600 hover:text-red-700 flex items-center gap-1 disabled:opacity-50"
                                title="Delete file"
                              >
                                <Trash2 className="w-4 h-4" />
                              </button>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                    <input
                      type="file"
                      disabled={uploadingFile === 'flight'}
                      onChange={(e) => e.target.files?.[0] && handleFileUpload(e.target.files[0], 'flight')}
                      className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-medium file:bg-primary-50 file:text-primary-700 hover:file:bg-primary-100 disabled:opacity-50"
                    />
                    <p className="text-xs text-gray-500 mt-1">Screenshot or PDF from airline/website (Kayak, Expedia, trip.com, etc.)</p>
                  </div>
                </FormSection>
              </div>
            )}
          </div>

          {/* Footer */}
          <div className="flex justify-end gap-3 px-6 py-4 border-t bg-gray-50">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-lg font-medium"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSaving}
              className="px-4 py-2 bg-primary-600 text-white hover:bg-primary-700 rounded-lg font-medium disabled:opacity-50"
            >
              {isSaving ? 'Saving...' : 'Save Changes'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
