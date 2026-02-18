import { useAppStore } from '@/store/appStore';
import { Dashboard } from '@/modules/common/Dashboard';
import { SeminarsModule } from '@/modules/seminars/SeminarsModule';
import { ReimbursementsModule } from '@/modules/reimbursements/ReimbursementsModule';
import { TeachingModule } from '@/modules/teaching/TeachingModule';
import { Settings } from '@/modules/common/Settings';
// import { cn } from '@/lib/utils';

export function MainContent() {
  const { activeModule } = useAppStore();

  const renderContent = () => {
    switch (activeModule) {
      case null:
        return <Dashboard />;
      case 'seminars':
        return <SeminarsModule />;
      case 'reimbursements':
        return <ReimbursementsModule />;
      case 'teaching':
        return <TeachingModule />;
      case 'settings':
        return <Settings />;
      default:
        return <Dashboard />;
    }
  };

  return (
    <main className="flex-1 overflow-auto bg-gray-50">
      {renderContent()}
    </main>
  );
}
