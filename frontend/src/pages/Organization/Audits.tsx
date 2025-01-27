// src/pages/Organization/Audits.tsx
import React from "react";
import Layout from "@/components/Layout/Layout.tsx";
import Header from "@/components/Layout/Header.tsx";
import { useUserProfileContext } from "@/context/UserProfileContext.tsx";

const Audits: React.FC = () => {
  const { userProfile } = useUserProfileContext();

  return (
    <Layout role={userProfile?.role || "GUEST"}>
      <div className="space-y-6">
        <Header userName={userProfile?.name} />
        <div className="bg-card rounded-lg p-6 shadow-sm border">
          <h2 className="text-2xl font-semibold mb-6">Audit Trails</h2>
          {/* Add audit table/content here */}
        </div>
      </div>
    </Layout>
  );
};

export default Audits;