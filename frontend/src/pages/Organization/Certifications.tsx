// src/pages/Organization/Certifications.tsx
import React from "react";
import Layout from "@/components/Layout/Layout";
import Header from "@/components/Layout/Header";
import { useUserProfileContext } from "@/context/UserProfileContext";

const Certifications: React.FC = () => {
  const { userProfile } = useUserProfileContext();

  return (
    <Layout role={userProfile?.role || "GUEST"}>
      <div className="space-y-6">
        <Header userName={userProfile?.name} />
        <div className="bg-card rounded-lg p-6 shadow-sm border">
          <h2 className="text-2xl font-semibold mb-6">Certifications</h2>
          {/* Add certifications content here */}
        </div>
      </div>
    </Layout>
  );
};

export default Certifications;