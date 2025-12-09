import React, { useState } from 'react';
import { Bell, Settings, Menu, X } from 'lucide-react';
import UserSwitcher from './UserSwitcher';
import SparklesIcon from './icons/SparklesIcon';

interface LayoutProps {
  children: React.ReactNode;
  activeTab: string;
  onTabChange: (tab: string) => void;
  onSignUpClick: () => void;
}

const Layout: React.FC<LayoutProps> = ({ children, activeTab, onTabChange, onSignUpClick }) => {
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  const navigation = [
    { id: 'dashboard', label: 'Dashboard', icon: '🏠', customIcon: null },
    { id: 'transactions', label: 'Transactions', icon: '💳', customIcon: null },
    { id: 'transfer', label: 'Transfer', icon: '🔄', customIcon: null },
    { id: 'analytics', label: 'Analytics', icon: '📊', customIcon: null },
    { id: 'ai-module', label: 'AI Module', icon: null, customIcon: 'sparkles' },
  ];

  const renderNavIcon = (item: typeof navigation[0], isActive: boolean) => {
    if (item.customIcon === 'sparkles') {
      return (
        <span className="mr-2">
          <SparklesIcon size={18} className={isActive ? 'opacity-100' : 'opacity-70'} />
        </span>
      );
    }
    return <span className="mr-2">{item.icon}</span>;
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <h1 className="text-2xl font-bold bg-gradient-to-r from-blue-800 to-blue-600 bg-clip-text text-transparent">
                  SecureBank
                </h1>
              </div>
              <nav className="hidden md:ml-10 md:flex md:space-x-4">
                {navigation.map((item) => {
                  const isActive = activeTab === item.id;
                  const isAIModule = item.id === 'ai-module';
                  
                  return (
                    <button
                      key={item.id}
                      onClick={() => onTabChange(item.id)}
                      className={`px-3 py-2 rounded-md text-sm font-medium transition-all flex items-center ${
                        isActive
                          ? isAIModule 
                            ? 'bg-gradient-to-r from-indigo-50 to-purple-50 text-indigo-700 border border-indigo-200 shadow-sm'
                            : 'bg-blue-50 text-blue-700'
                          : isAIModule
                            ? 'text-gray-600 hover:text-indigo-700 hover:bg-indigo-50'
                            : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
                      }`}
                    >
                      {renderNavIcon(item, isActive)}
                      {item.label}
                    </button>
                  );
                })}
              </nav>
            </div>
            
            <div className="flex items-center space-x-4">
              <button className="p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-50 rounded-full">
                <Bell className="h-5 w-5" />
              </button>
              <button className="p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-50 rounded-full">
                <Settings className="h-5 w-5" />
              </button>
              
              {/* User Switcher replaces the old user icon */}
              <UserSwitcher onSignUpClick={onSignUpClick} />
              
              <button className="md:hidden p-2" onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}>
                {isMobileMenuOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
              </button>
            </div>
          </div>
        </div>

        {/* Mobile menu */}
        {isMobileMenuOpen && (
          <div className="md:hidden">
            <div className="px-2 pt-2 pb-3 space-y-1 sm:px-3 bg-white border-t">
              {navigation.map((item) => {
                const isActive = activeTab === item.id;
                const isAIModule = item.id === 'ai-module';
                
                return (
                  <button
                    key={item.id}
                    onClick={() => {
                      onTabChange(item.id);
                      setIsMobileMenuOpen(false);
                    }}
                    className={`flex items-center px-3 py-2 rounded-md text-base font-medium w-full text-left transition-colors ${
                      isActive
                        ? isAIModule
                          ? 'bg-gradient-to-r from-indigo-50 to-purple-50 text-indigo-700'
                          : 'bg-blue-50 text-blue-700'
                        : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
                    }`}
                  >
                    {renderNavIcon(item, isActive)}
                    {item.label}
                  </button>
                );
              })}
            </div>
          </div>
        )}
      </header>

      {/* Main content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {children}
      </main>
    </div>
  );
};

export default Layout;