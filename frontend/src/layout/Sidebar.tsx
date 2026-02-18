import { useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { 
  Calendar, 
  DollarSign, 
  GraduationCap, 
  LayoutDashboard,
  ChevronRight,
  Menu,
  X,
  Settings,
  LogOut
} from 'lucide-react';
import { useAuth } from '@/context/AuthContext';
import { modulesApi } from '@/api/client';
import { useAppStore } from '@/store/appStore';
import { cn } from '@/lib/utils';

const iconMap: Record<string, React.ReactNode> = {
  seminars: <Calendar className="w-5 h-5" />,
  reimbursements: <DollarSign className="w-5 h-5" />,
  teaching: <GraduationCap className="w-5 h-5" />,
  dashboard: <LayoutDashboard className="w-5 h-5" />,
  settings: <Settings className="w-5 h-5" />,
};

export function Sidebar() {
  const { 
    modules, 
    setModules, 
    activeModule, 
    setActiveModule,
    sidebarCollapsed,
    toggleSidebar
  } = useAppStore();

  const { data, isLoading } = useQuery({
    queryKey: ['modules'],
    queryFn: modulesApi.list,
  });

  useEffect(() => {
    if (data) {
      setModules(data);
    }
  }, [data, setModules]);

  const handleModuleClick = (moduleName: string | null) => {
    setActiveModule(moduleName);
  };

  return (
    <aside
      className={cn(
        'bg-slate-900 text-white transition-all duration-300 flex flex-col',
        sidebarCollapsed ? 'w-16' : 'w-64'
      )}
    >
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-slate-700">
        {!sidebarCollapsed && (
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-primary-500 rounded-lg flex items-center justify-center font-bold text-lg">
              I
            </div>
            <span className="font-semibold text-lg">InacioTool</span>
          </div>
        )}
        <button
          onClick={toggleSidebar}
          className="p-1 hover:bg-slate-700 rounded-lg transition-colors"
        >
          {sidebarCollapsed ? <Menu className="w-5 h-5" /> : <X className="w-5 h-5" />}
        </button>
      </div>

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto p-2">
        {/* Dashboard */}
        <button
          onClick={() => handleModuleClick(null)}
          className={cn(
            'w-full flex items-center gap-3 px-3 py-2 rounded-lg transition-colors mb-1',
            activeModule === null 
              ? 'bg-primary-600 text-white' 
              : 'hover:bg-slate-800 text-slate-300'
          )}
        >
          {iconMap.dashboard}
          {!sidebarCollapsed && <span>Dashboard</span>}
        </button>

        {/* Module Sections */}
        <div className="mt-4">
          {!sidebarCollapsed && (
            <div className="px-3 mb-2 text-xs font-semibold text-slate-500 uppercase tracking-wider">
              Modules
            </div>
          )}
          
          {isLoading ? (
            <div className="px-3 py-2 text-slate-400 text-sm">Loading...</div>
          ) : (
            modules.map((module) => (
              <button
                key={module.name}
                onClick={() => handleModuleClick(module.name)}
                className={cn(
                  'w-full flex items-center gap-3 px-3 py-2 rounded-lg transition-colors mb-1',
                  activeModule === module.name
                    ? 'bg-primary-600 text-white'
                    : 'hover:bg-slate-800 text-slate-300'
                )}
              >
                {iconMap[module.name] || <div className="w-5 h-5" />}
                {!sidebarCollapsed && (
                  <>
                    <span className="flex-1 text-left capitalize">{module.name}</span>
                    <ChevronRight className="w-4 h-4 opacity-50" />
                  </>
                )}
              </button>
            ))
          )}
        </div>
      </nav>

      {/* Footer */}
      <div className="p-2 border-t border-slate-700 space-y-1">
        <button
          onClick={() => handleModuleClick('settings')}
          className={cn(
            'w-full flex items-center gap-3 px-3 py-2 rounded-lg transition-colors',
            activeModule === 'settings'
              ? 'bg-primary-600 text-white'
              : 'hover:bg-slate-800 text-slate-300'
          )}
        >
          {iconMap.settings}
          {!sidebarCollapsed && <span>Settings</span>}
        </button>
        <LogoutButton />
      </div>
    </aside>
  );
}

// Logout Button Component
function LogoutButton() {
  const { sidebarCollapsed } = useAppStore();
  const { logout } = useAuth();
  
  return (
    <button
      onClick={logout}
      className="w-full flex items-center gap-3 px-3 py-2 rounded-lg transition-colors hover:bg-slate-800 text-slate-400 hover:text-slate-200"
    >
      <LogOut className="w-5 h-5" />
      {!sidebarCollapsed && <span>Logout</span>}
    </button>
  );
}
