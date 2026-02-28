import { useState } from 'react'
import { clsx } from 'clsx'
import AzureSettings from '../components/settings/AzureSettings'
import AWSSettings from '../components/settings/AWSSettings'
import GCPSettings from '../components/settings/GCPSettings'
import GeneralSettings from '../components/settings/GeneralSettings'
import SlackSettings from '../components/settings/SlackSettings'
import EmailSettings from '../components/settings/EmailSettings'
import UserProfileSettings from '../components/settings/UserProfileSettings'
import AdvancedSettings from '../components/settings/AdvancedSettings'

const tabs = [
  { id: 'azure', label: 'Azure' },
  { id: 'aws', label: 'AWS' },
  { id: 'gcp', label: 'GCP' },
  { id: 'general', label: 'General' },
  { id: 'slack', label: 'Slack' },
  { id: 'email', label: 'Email' },
  { id: 'profile', label: 'Profile' },
  { id: 'advanced', label: 'Advanced' },
] as const

type SettingsTab = typeof tabs[number]['id']

export default function Settings() {
  const [activeTab, setActiveTab] = useState<SettingsTab>('azure')

  const renderTab = () => {
    switch (activeTab) {
      case 'azure': return <AzureSettings />
      case 'aws': return <AWSSettings />
      case 'gcp': return <GCPSettings />
      case 'general': return <GeneralSettings />
      case 'slack': return <SlackSettings />
      case 'email': return <EmailSettings />
      case 'profile': return <UserProfileSettings />
      case 'advanced': return <AdvancedSettings />
    }
  }

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-dark-900 dark:text-white">Settings</h1>
        <p className="mt-1 text-sm text-dark-500 dark:text-dark-400">Configure cloud providers and integrations</p>
      </div>

      <div className="flex gap-6">
        <nav className="w-48 flex-shrink-0 space-y-1">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={clsx(
                'w-full rounded-lg px-3 py-2 text-left text-sm font-medium transition-colors',
                activeTab === tab.id
                  ? 'bg-primary-50 text-primary-700 dark:bg-primary-900/30 dark:text-primary-400'
                  : 'text-dark-600 hover:bg-gray-100 dark:text-dark-400 dark:hover:bg-dark-800',
              )}
            >
              {tab.label}
            </button>
          ))}
        </nav>

        <div className="flex-1">
          {renderTab()}
        </div>
      </div>
    </div>
  )
}
