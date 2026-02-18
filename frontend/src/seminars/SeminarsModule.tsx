import { useState, useEffect } from 'react';
import { Plus, Calendar, Users, MapPin, CheckCircle, XCircle, AlertCircle, Trash2, Edit, X } from 'lucide-react';
import { seminarsApi } from '../api';

interface Speaker {
  id: number;
  name: string;
  affiliation?: string;
  email?: string;
  website?: string;
  bio?: string;
}

interface Room {
  id: number;
  name: string;
  capacity?: number;
  location?: string;
}

interface Seminar {
  id: number;
  title: string;
  date: string;
  start_time: string;
  end_time?: string;
  speaker_id: number;
  room_id?: number;
  abstract?: string;
  paper_title?: string;
  status: string;
  room_booked: boolean;
  announcement_sent: boolean;
  calendar_invite_sent: boolean;
  website_updated: boolean;
  speaker?: Speaker;
  room?: Room;
}

export function SeminarsModule() {
  const [seminars, setSeminars] = useState<Seminar[]>([]);
  const [speakers, setSpeakers] = useState<Speaker[]>([]);
  const [rooms, setRooms] = useState<Room[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'seminars' | 'speakers' | 'rooms'>('seminars');
  const [showModal, setShowModal] = useState(false);
  const [editingSeminar, setEditingSeminar] = useState<Seminar | null>(null);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [seminarsData, speakersData, roomsData] = await Promise.all([
        seminarsApi.listSeminars(),
        seminarsApi.listSpeakers(),
        seminarsApi.listRooms(),
      ]);
      setSeminars(seminarsData);
      setSpeakers(speakersData);
      setRooms(roomsData);
    } catch (err) {
      console.error('Failed to load data:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteSeminar = async (id: number) => {
    if (!confirm('Delete this seminar?')) return;
    try {
      await seminarsApi.deleteSeminar(id);
      loadData();
    } catch (err) {
      console.error('Failed to delete:', err);
    }
  };

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString('en-US', { 
      month: 'short', day: 'numeric', year: 'numeric' 
    });
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-black text-white flex items-center justify-center">
        <div className="text-xl">Loading...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-black text-white">
      {/* Header */}
      <header className="border-b border-gray-800">
        <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
          <h1 className="text-2xl font-bold">📚 Seminars</h1>
          <button
            onClick={() => setShowModal(true)}
            className="bg-blue-600 hover:bg-blue-700 px-4 py-2 rounded-lg flex items-center gap-2"
          >
            <Plus className="w-4 h-4" />
            New Seminar
          </button>
        </div>
      </header>

      {/* Navigation */}
      <nav className="border-b border-gray-800">
        <div className="max-w-7xl mx-auto px-4">
          <div className="flex gap-6">
            {(['seminars', 'speakers', 'rooms'] as const).map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`py-3 px-2 border-b-2 capitalize ${
                  activeTab === tab
                    ? 'border-blue-500 text-blue-500'
                    : 'border-transparent text-gray-400 hover:text-white'
                }`}
              >
                {tab}
              </button>
            ))}
          </div>
        </div>
      </nav>

      {/* Content */}
      <main className="max-w-7xl mx-auto px-4 py-6">
        {activeTab === 'seminars' && (
          <div className="space-y-4">
            {seminars.length === 0 ? (
              <div className="text-center py-12 text-gray-400">
                <Calendar className="w-12 h-12 mx-auto mb-4 opacity-50" />
                <p>No seminars scheduled yet.</p>
                <button
                  onClick={() => setShowModal(true)}
                  className="mt-4 text-blue-500 hover:text-blue-400"
                >
                  Create your first seminar
                </button>
              </div>
            ) : (
              seminars.map((seminar) => (
                <div
                  key={seminar.id}
                  className="bg-gray-900 rounded-xl p-6 border border-gray-800"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="text-blue-400 text-sm font-medium mb-1">
                        {formatDate(seminar.date)} at {seminar.start_time}
                      </div>
                      <h3 className="text-lg font-semibold mb-2">{seminar.title}</h3>
                      
                      <div className="flex items-center gap-4 text-sm text-gray-400 mb-3">
                        <span className="flex items-center gap-1">
                          <Users className="w-4 h-4" />
                          {seminar.speaker?.name || 'TBD'}
                        </span>
                        <span className="flex items-center gap-1">
                          <MapPin className="w-4 h-4" />
                          {seminar.room?.name || 'TBD'}
                        </span>
                      </div>

                      {seminar.abstract && (
                        <p className="text-gray-400 text-sm mb-3 line-clamp-2">
                          {seminar.abstract}
                        </p>
                      )}

                      <div className="flex gap-2">
                        {!seminar.room_booked && (
                          <span className="px-2 py-1 bg-yellow-500/20 text-yellow-500 text-xs rounded">
                            Room needed
                          </span>
                        )}
                        {!seminar.announcement_sent && (
                          <span className="px-2 py-1 bg-orange-500/20 text-orange-500 text-xs rounded">
                            Announcement needed
                          </span>
                        )}
                        {!seminar.calendar_invite_sent && (
                          <span className="px-2 py-1 bg-purple-500/20 text-purple-500 text-xs rounded">
                            Calendar needed
                          </span>
                        )}
                      </div>
                    </div>

                    <div className="flex items-center gap-2 ml-4">
                      <button
                        onClick={() => {
                          setEditingSeminar(seminar);
                          setShowModal(true);
                        }}
                        className="p-2 hover:bg-gray-800 rounded-lg text-gray-400 hover:text-white"
                      >
                        <Edit className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => handleDeleteSeminar(seminar.id)}
                        className="p-2 hover:bg-red-900/50 rounded-lg text-gray-400 hover:text-red-400"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        )}

        {activeTab === 'speakers' && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {speakers.map((speaker) => (
              <div
                key={speaker.id}
                className="bg-gray-900 rounded-xl p-4 border border-gray-800"
              >
                <h3 className="font-semibold mb-1">{speaker.name}</h3>
                {speaker.affiliation && (
                  <p className="text-sm text-gray-400 mb-2">{speaker.affiliation}</p>
                )}
                {speaker.email && (
                  <p className="text-sm text-gray-500">{speaker.email}</p>
                )}
              </div>
            ))}
          </div>
        )}

        {activeTab === 'rooms' && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {rooms.map((room) => (
              <div
                key={room.id}
                className="bg-gray-900 rounded-xl p-4 border border-gray-800"
              >
                <h3 className="font-semibold mb-1">{room.name}</h3>
                {room.capacity && (
                  <p className="text-sm text-gray-400">Capacity: {room.capacity}</p>
                )}
                {room.location && (
                  <p className="text-sm text-gray-500">{room.location}</p>
                )}
              </div>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}
