// src/App.tsx
import { Toaster } from "./components/ui/toaster";
import { Toaster as Sonner } from "./components/ui/sonner";
import { TooltipProvider } from "./components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { createBrowserRouter, RouterProvider, Outlet } from "react-router-dom";
import { UserProfileProvider } from "./context/UserProfileContext";
import ProtectedRoute from "@/pages/ProtectedRoute";

// Pages
import Index from "./pages/Index";
import Login from "./pages/Login";
import Register from "./pages/Register";
import About from "./pages/About";
import Dashboard from "@/pages/Dashboard";
import EmailConfirmation from "@/pages/verifyEmail";
import Standards from "@/pages/standards";
import Unauthorized from "@/pages/Unauthorized";
import Users from "@/pages/Users";
import Layout from "@/components/Layout/Layout.tsx";
import Chat from "@/pages/Chat.tsx";
import Audits from "@/pages/Organization/Audits.tsx";
import Certifications from "@/pages/Organization/Certifications.tsx";
import Invitations from "@/pages/invitations.tsx";

const queryClient = new QueryClient();

const RootLayout = () => (
  <>
    <Outlet />
    <Toaster />
    <Sonner />
  </>
);

const router = createBrowserRouter([
  {
    element: <RootLayout />,
    children: [
      { path: "/", element: <Index /> },
      { path: "/login", element: <Login /> },
      { path: "/register", element: <Register /> },
      { path: "/verify-email", element: <EmailConfirmation /> },
      { path: "/about", element: <About /> },
      {
        path: "/dashboard",
        element: (
          <ProtectedRoute allowedRoles={['ALL']}>
            <Dashboard />
          </ProtectedRoute>
        ),
      },
      {
        path: "/standards",
        element: (
          <ProtectedRoute allowedRoles={['ALL']}>
            <Standards />
          </ProtectedRoute>
        ),
      },
      { path: "/unauthorized", element: <Unauthorized /> },
      {
        path: "/users",
        element: (
          <ProtectedRoute allowedRoles={["ADMIN",'MANAGER','EMPLOYEE']}>
            <Users />
          </ProtectedRoute>
        ),
      },
      {
        path: '/chat',
        element: (
          <ProtectedRoute allowedRoles={["ALL"]}>
            <Chat />
          </ProtectedRoute>
        ),
      },
      {
        path: '/organization/audits',
        element: (
          <ProtectedRoute allowedRoles={["MANAGER", "EMPLOYEE"]}>
            <Audits />
          </ProtectedRoute>
        ),
      },
      {
        path: '/organization/certifications',
        element: (
          <ProtectedRoute allowedRoles={["MANAGER", "EMPLOYEE"]}>
            <Certifications />
          </ProtectedRoute>
        ),
      },
      {
        path: '/organization/users',
        element: (
          <ProtectedRoute allowedRoles={["MANAGER", "EMPLOYEE"]}>
            <Users />
          </ProtectedRoute>
        )
      },
        {
  path: '/organization/invitations',
  element: (
    <ProtectedRoute allowedRoles={["MANAGER"]}>
      <Invitations />
    </ProtectedRoute>
  ),
}
    ],
  },
]);

const App = () => (
  <QueryClientProvider client={queryClient}>
    <UserProfileProvider>
      <TooltipProvider>
        <div className="min-h-screen bg-background text-foreground">
          <RouterProvider router={router} />
        </div>
      </TooltipProvider>
    </UserProfileProvider>
  </QueryClientProvider>
);

export default App;