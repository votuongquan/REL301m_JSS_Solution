/**
 * JSS Operations Page - Server Component
 * Demonstrates proper server-side rendering with JSS streaming components
 * Following frontend rules for server components and translation
 */

import { getDictionary, createTranslator } from '@/utils/translation';
import { getCurrentLocale } from '@/utils/getCurrentLocale';
import JssDashboard from '@/components/jss/jss-dashboard';
import BackgroundTaskManager from '@/components/jss/background-task-manager';
import JssFileManager from '@/components/jss/jss-file-manager';
import JssVisualization from '@/components/jss/jss-visualization';

// Server component - no 'use client' directive
async function JssOperationsPage() {
  // Server-side translation setup
  const locale = await getCurrentLocale();
  const dictionary = await getDictionary(locale);
  const t = createTranslator(dictionary);
  // Get translations for components
  const translations = {
    pageTitle: t('jss.page.title') || 'JSS Operations',
    pageSubtitle: t('jss.page.subtitle') || 'Real-time Job Shop Scheduling Analysis and Comparison',
    dashboardTitle: t('jss.dashboard.title') || 'JSS Streaming Dashboard',
    dashboardSubtitle: t('jss.dashboard.subtitle') || 'Run and compare JSS algorithms with real-time updates',
    backgroundTitle: t('jss.background.title') || 'Streaming Sessions',
    fileManagerTitle: t('jss.files.title') || 'File Manager',
    visualizationTitle: t('jss.visualization.title') || 'Visualization Generator',
  };

  return (
    <div className="min-h-screen bg-[color:var(--background)]">
      {/* Page Header */}
      <div className="bg-[color:var(--card)] border-b border-[color:var(--border)]">
        <div className="container mx-auto px-6 py-8">
          <h1 className="text-4xl font-bold text-[color:var(--foreground)] mb-2">
            {translations.pageTitle}
          </h1>
          <p className="text-lg text-[color:var(--muted-foreground)]">
            {translations.pageSubtitle}
          </p>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="bg-[color:var(--background)] border-b border-[color:var(--border)]">
        <div className="container mx-auto px-6">
          <nav className="flex space-x-8">
            <a
              href="#dashboard"
              className="py-4 px-2 border-b-2 border-blue-600 text-blue-600 font-medium"
            >
              {t('jss.nav.dashboard') || 'Dashboard'}
            </a>            <a
              href="#background"
              className="py-4 px-2 border-b-2 border-transparent text-[color:var(--muted-foreground)] hover:text-[color:var(--foreground)] hover:border-gray-300"
            >
              {t('jss.nav.background') || 'Streaming Sessions'}
            </a>
            <a
              href="#files"
              className="py-4 px-2 border-b-2 border-transparent text-[color:var(--muted-foreground)] hover:text-[color:var(--foreground)] hover:border-gray-300"
            >
              {t('jss.nav.files') || 'Files'}
            </a>
            <a
              href="#visualization"
              className="py-4 px-2 border-b-2 border-transparent text-[color:var(--muted-foreground)] hover:text-[color:var(--foreground)] hover:border-gray-300"
            >
              {t('jss.nav.visualization') || 'Visualizations'}
            </a>
          </nav>
        </div>
      </div>

      {/* Main Content */}
      <div className="container mx-auto">
        {/* Dashboard Section */}
        <section id="dashboard" className="py-8">
          <JssDashboard
            title={translations.dashboardTitle}
            subtitle={translations.dashboardSubtitle}
          />
        </section>        {/* Background Tasks Section */}
        <section id="background" className="py-8 border-t border-[color:var(--border)]">
          <BackgroundTaskManager
            title={translations.backgroundTitle}
          />
        </section>

        {/* File Manager Section */}
        <section id="files" className="py-8 border-t border-[color:var(--border)]">
          <JssFileManager
            title={translations.fileManagerTitle}
          />
        </section>

        {/* Visualization Section */}
        <section id="visualization" className="py-8 border-t border-[color:var(--border)]">
          <JssVisualization
            title={translations.visualizationTitle}
          />
        </section>
      </div>

      {/* Features Overview */}
      <div className="bg-[color:var(--muted)] py-16 mt-16">
        <div className="container mx-auto px-6">
          <h2 className="text-3xl font-bold text-center mb-12">
            {t('jss.features.title') || 'JSS Features'}
          </h2>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
            <div className="bg-[color:var(--feature-blue)] text-[color:var(--feature-blue-text)] rounded-lg p-6 text-center">
              <div className="text-4xl mb-4">🔄</div>
              <h3 className="text-xl font-semibold mb-2">
                {t('jss.features.comparison.title') || 'Algorithm Comparison'}
              </h3>
              <p className="text-sm">
                {t('jss.features.comparison.description') || 'Compare multiple JSS algorithms and dispatching rules'}
              </p>
            </div>
              <div className="bg-[color:var(--feature-green)] text-[color:var(--feature-green-text)] rounded-lg p-6 text-center">
              <div className="text-4xl mb-4">🌊</div>
              <h3 className="text-xl font-semibold mb-2">
                {t('jss.features.streaming.title') || 'Real-time Streaming'}
              </h3>
              <p className="text-sm">
                {t('jss.features.streaming.description') || 'Stream live comparison results and progress updates'}
              </p>
            </div>
            
            <div className="bg-[color:var(--feature-purple)] text-[color:var(--feature-purple-text)] rounded-lg p-6 text-center">
              <div className="text-4xl mb-4">📊</div>
              <h3 className="text-xl font-semibold mb-2">
                {t('jss.features.visualization.title') || 'Rich Visualizations'}
              </h3>
              <p className="text-sm">
                {t('jss.features.visualization.description') || 'Generate comprehensive charts and reports'}
              </p>
            </div>
            
            <div className="bg-[color:var(--feature-orange)] text-[color:var(--feature-orange-text)] rounded-lg p-6 text-center">
              <div className="text-4xl mb-4">🎯</div>
              <h3 className="text-xl font-semibold mb-2">
                {t('jss.features.optimization.title') || 'Performance Optimization'}
              </h3>
              <p className="text-sm">
                {t('jss.features.optimization.description') || 'Find the best scheduling approach'}
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default JssOperationsPage;
