import { useQuery } from '@tanstack/react-query';
import { fetchWithAuth, getAccessCode } from '@/api/client';
import { ArrowLeft, Calendar, MapPin, Clock, User, FileText, Plane, Home, CreditCard, Paperclip } from 'lucide-react';

interface SeminarViewPageProps {
  seminarId: number;
  seminarTitle: string;
  onClose: () => void;
}

const InfoRow = ({ label, value }: { label: string; value: string | null | undefined }) => {
  if (value == null || value === '') return null;
  return (
    <div className="flex gap-2 py-1.5">
      <span className="text-gray-500 min-w-[140px]">{label}</span>
      <span className="text-gray-900">{value}</span>
    </div>
  );
};

const Section = ({ title, icon: Icon, children }: { title: string; icon: any; children: React.ReactNode }) => (
  <section className="bg-white rounded-xl border border-gray-200 p-6">
    <h3 className="flex items-center gap-2 font-semibold text-gray-900 mb-4">
      <Icon className="w-5 h-5 text-primary-600" />
      {title}
    </h3>
    {children}
  </section>
);

export function SeminarViewPage({ seminarId, seminarTitle, onClose }: SeminarViewPageProps) {
  const { data: details, isLoading } = useQuery({
    queryKey: ['seminar-details', seminarId],
    queryFn: async () => {
      const r = await fetchWithAuth(`/api/v1/seminars/seminars/${seminarId}/details`);
      if (!r.ok) throw new Error('Failed to fetch details');
      return r.json();
    },
  });

  const { data: files = [] } = useQuery({
    queryKey: ['seminar-files', seminarId],
    queryFn: async () => {
      const r = await fetchWithAuth(`/api/v1/seminars/seminars/${seminarId}/files`);
      if (!r.ok) throw new Error('Failed to fetch files');
      return r.json();
    },
  });

  const categoryLabels: Record<string, string> = {
    cv: 'CV / Resume',
    photo: 'Photo',
    passport: 'Passport',
    flight: 'Flight Booking',
    other: 'Other',
  };

  const downloadUrl = (fileId: number) =>
    `/api/v1/seminars/seminars/${seminarId}/files/${fileId}/download?access_code=${getAccessCode() || ''}`;

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-gray-500">Loading...</div>
      </div>
    );
  }

  const info = details?.info;
  const speaker = details?.speaker;

  return (
    <div className="fixed inset-0 z-50 bg-gray-50 overflow-auto">
      <div className="sticky top-0 z-10 bg-white border-b border-gray-200 px-6 py-4 flex items-center gap-4">
        <button
          onClick={onClose}
          className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
          title="Back to seminars"
        >
          <ArrowLeft className="w-5 h-5" />
        </button>
        <h1 className="text-xl font-semibold text-gray-900 truncate flex-1">{seminarTitle}</h1>
      </div>

      <div className="p-6 max-w-4xl mx-auto space-y-6">
        {/* Seminar basics */}
        <Section title="Seminar" icon={Calendar}>
          <div className="space-y-1">
            <InfoRow label="Title" value={details?.title} />
            <InfoRow label="Abstract" value={details?.abstract} />
            <div className="flex flex-wrap gap-6 pt-2">
              <span className="flex items-center gap-2 text-gray-600">
                <Calendar className="w-4 h-4" />
                {details?.date}
              </span>
              <span className="flex items-center gap-2 text-gray-600">
                <Clock className="w-4 h-4" />
                {details?.start_time} – {details?.end_time}
              </span>
              <span className="flex items-center gap-2 text-gray-600">
                <MapPin className="w-4 h-4" />
                {details?.room || 'TBD'}
              </span>
            </div>
          </div>
        </Section>

        {/* Speaker */}
        <Section title="Speaker" icon={User}>
          <div className="space-y-1">
            <InfoRow label="Name" value={speaker?.name} />
            <InfoRow label="Email" value={speaker?.email} />
            <InfoRow label="Affiliation" value={speaker?.affiliation} />
          </div>
        </Section>

        {/* Talk info */}
        <Section title="Talk Information" icon={FileText}>
          <div className="space-y-1">
            <InfoRow label="Title" value={details?.title} />
            <InfoRow label="Abstract" value={details?.abstract} />
          </div>
        </Section>

        {/* Travel */}
        <Section title="Travel" icon={Plane}>
          <div className="space-y-1">
            <InfoRow label="Departure City" value={info?.departure_city} />
            <InfoRow label="Travel Method" value={info?.travel_method} />
            <InfoRow label="Estimated Cost" value={info?.estimated_travel_cost != null ? `$${info.estimated_travel_cost}` : undefined} />
            <InfoRow label="Passport Number" value={info?.passport_number} />
            <InfoRow label="Passport Country" value={info?.passport_country} />
          </div>
        </Section>

        {/* Accommodation */}
        <Section title="Accommodation" icon={Home}>
          <div className="space-y-1">
            <InfoRow label="Needs accommodation" value={info?.needs_accommodation ? 'Yes' : 'No'} />
            <InfoRow label="Check-in" value={info?.check_in_date} />
            <InfoRow label="Check-out" value={info?.check_out_date} />
            <InfoRow label="Nights" value={info?.accommodation_nights?.toString()} />
            <InfoRow label="Estimated hotel cost" value={info?.estimated_hotel_cost != null ? `$${info.estimated_hotel_cost}` : undefined} />
          </div>
        </Section>

        {/* Payment */}
        <Section title="Payment" icon={CreditCard}>
          <div className="space-y-1">
            <InfoRow label="Payment Email" value={info?.payment_email} />
            <InfoRow label="Contact Number" value={info?.contact_number} />
            <InfoRow label="Beneficiary Name" value={info?.beneficiary_name} />
            <InfoRow label="Bank Name" value={info?.bank_name} />
            <InfoRow label="Bank Region" value={info?.bank_region} />
            <InfoRow label="IBAN" value={info?.iban} />
            <InfoRow label="ABA Routing Number" value={info?.aba_routing_number} />
            <InfoRow label="BSB Number" value={info?.bsb_number} />
            <InfoRow label="Bank Account" value={info?.bank_account_number} />
            <InfoRow label="SWIFT Code" value={info?.swift_code} />
            <InfoRow label="Currency" value={info?.currency} />
            <InfoRow label="Bank Address" value={info?.bank_address} />
            <InfoRow label="Beneficiary Address" value={info?.beneficiary_address} />
          </div>
        </Section>

        {/* Files */}
        <Section title="Files" icon={Paperclip}>
          {files.length === 0 ? (
            <p className="text-gray-500 text-sm">No files uploaded</p>
          ) : (
            <div className="space-y-2">
              {files.map((file: any) => (
                <div
                  key={file.id}
                  className="flex items-center justify-between py-2 px-3 bg-gray-50 rounded-lg"
                >
                  <span className="text-sm text-gray-700 truncate flex-1">
                    {file.original_filename}
                    {file.file_category && (
                      <span className="text-gray-500 ml-2">
                        ({categoryLabels[file.file_category] || file.file_category})
                      </span>
                    )}
                  </span>
                  <a
                    href={downloadUrl(file.id)}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-sm font-medium text-primary-600 hover:text-primary-700 whitespace-nowrap"
                  >
                    Download
                  </a>
                </div>
              ))}
            </div>
          )}
        </Section>
      </div>
    </div>
  );
}
