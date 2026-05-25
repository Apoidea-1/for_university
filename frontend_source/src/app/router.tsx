import type { ReactElement } from "react";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";

import { Spinner } from "@/components/ui/Spinner";
import { AppShell } from "@/app/layouts/AppShell";
import { useAuth } from "@/hooks/useAuth";
import { AddContactPage } from "@/pages/AddContactPage";
import { AnalyticsPage } from "@/pages/AnalyticsPage";
import { ContactDetailsPage } from "@/pages/ContactDetailsPage";
import { ContactsPage } from "@/pages/ContactsPage";
import { DashboardPage } from "@/pages/DashboardPage";
import { IntegrationsPage } from "@/pages/IntegrationsPage";
import { LandingPage } from "@/pages/LandingPage";
import { LoginPage } from "@/pages/LoginPage";
import { MessagesPage } from "@/pages/MessagesPage";
import { NetworkPage } from "@/pages/NetworkPage";
import { NotFoundPage } from "@/pages/NotFoundPage";
import { RegisterPage } from "@/pages/RegisterPage";
import { RemindersPage } from "@/pages/RemindersPage";

const appBasename = (import.meta.env.VITE_APP_BASENAME ?? "/app").replace(/\/$/, "") || "/";

function ProtectedLayout() {
  const { user, isBootstrapping } = useAuth();
  if (isBootstrapping) {
    return <Spinner />;
  }
  if (!user) {
    return <Navigate to="/login" replace />;
  }
  return <AppShell />;
}

function PublicOnly({ children }: { children: ReactElement }) {
  const { user, isBootstrapping } = useAuth();
  if (isBootstrapping) {
    return <Spinner />;
  }
  if (user) {
    return <Navigate to="/dashboard" replace />;
  }
  return children;
}

export function AppRouter() {
  return (
    <BrowserRouter basename={appBasename}>
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route
          path="/login"
          element={
            <PublicOnly>
              <LoginPage />
            </PublicOnly>
          }
        />
        <Route
          path="/register"
          element={
            <PublicOnly>
              <RegisterPage />
            </PublicOnly>
          }
        />

        <Route element={<ProtectedLayout />}>
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/contacts" element={<ContactsPage />} />
          <Route path="/contacts/new" element={<AddContactPage />} />
          <Route path="/contacts/:contactId" element={<ContactDetailsPage />} />
          <Route path="/contacts/:contactId/edit" element={<AddContactPage />} />
          <Route path="/network" element={<NetworkPage />} />
          <Route path="/messages" element={<MessagesPage />} />
          <Route path="/reminders" element={<RemindersPage />} />
          <Route path="/analytics" element={<AnalyticsPage />} />
          <Route path="/integrations" element={<IntegrationsPage />} />
        </Route>

        <Route path="*" element={<NotFoundPage />} />
      </Routes>
    </BrowserRouter>
  );
}
