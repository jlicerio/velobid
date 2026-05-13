import { createBrowserRouter } from 'react-router-dom'
import { AppProviders } from './AppProviders'
import { AppShell } from '@/components/shared/AppShell'
import { LoginPage } from '@/pages/LoginPage'
import { SignupPage } from '@/pages/SignupPage'
import { ProjectsPage } from '@/pages/ProjectsPage'
import { ProjectDetailPage } from '@/pages/ProjectDetailPage'
import { DocumentViewerPage } from '@/pages/DocumentViewerPage'
import { BlueprintVisionPage } from '@/pages/BlueprintVisionPage'
import { ResidentialEstimatesPage } from '@/pages/ResidentialEstimatesPage'
import { SettingsPage } from '@/pages/SettingsPage'
import { NotFoundPage } from '@/pages/NotFoundPage'

export const router = createBrowserRouter([
  {
    element: <AppProviders />,
    children: [
      { path: '/login', element: <LoginPage /> },
      { path: '/signup', element: <SignupPage /> },
      {
        path: '/',
        element: <AppShell />,
        children: [
          { index: true, element: <ProjectsPage /> },
          { path: 'projects', element: <ProjectsPage /> },
          { path: 'projects/:projectId', element: <ProjectDetailPage /> },
          {
            path: 'projects/:projectId/documents',
            element: <DocumentViewerPage />,
          },
          {
            path: 'projects/:projectId/blueprints/analyze',
            element: <BlueprintVisionPage />,
          },
          { path: 'residential', element: <ResidentialEstimatesPage /> },
          { path: 'settings', element: <SettingsPage /> },
          { path: 'settings/profile', element: <SettingsPage /> },
          { path: 'settings/bidders', element: <SettingsPage /> },
          { path: 'settings/users', element: <SettingsPage /> },
          { path: 'settings/trades', element: <SettingsPage /> },
        ],
      },
      { path: '*', element: <NotFoundPage /> },
    ],
  },
])
