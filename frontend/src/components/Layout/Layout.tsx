import React from "react";
import Sidebar from "./Sidebar";

type LayoutProps = {
  children: React.ReactNode;
  role: string;
};

const Layout: React.FC<LayoutProps> = ({ children, role }) => (
  <div className="flex min-h-screen bg-background">
    <Sidebar role={role} />
    <main className="flex-1 p-8">
      <div className="max-w-7xl mx-auto">{children}</div>
    </main>
  </div>
);

export default Layout;
