// src/context/UserProfileContext.tsx
import React, { createContext, useContext, useState, useEffect } from "react";
import { UserProfile } from "@/types";
import { fetchWithAuth } from "../utils/api";

type UserProfileContextType = {
  userProfile: UserProfile | null;
  setUserProfile: (profile: UserProfile | null) => void;
  loading: boolean;
};

const UserProfileContext = createContext<UserProfileContextType>({
  userProfile: null,
  setUserProfile: () => {},
  loading: true,
});

export const UserProfileProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [userProfile, setUserProfile] = useState<UserProfile | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchProfile = async () => {
      try {
        const token = localStorage.getItem("accessToken");
        if (!token) {
          setLoading(false);
          return;
        }

        const response = await fetchWithAuth("/user/profile");
        if (!response.ok) throw new Error("Failed to fetch profile");

        const data = await response.json();
        const parsedRole = data.role.includes('.')
          ? data.role.split('.').pop()
          : data.role;

        setUserProfile({
          role: parsedRole || 'GUEST',
          name: data.full_name,
          certification_body_name: data.certification_body_name,
          organization_name: data.organization_name
        });
      } catch (error) {
        console.error("Profile fetch error:", error);
        localStorage.removeItem("accessToken");
        setUserProfile(null);
      } finally {
        setLoading(false);
      }
    };

    fetchProfile();

    const storageListener = () => {
      if (!localStorage.getItem("accessToken")) {
        setUserProfile(null);
      }
    };

    window.addEventListener('storage', storageListener);
    return () => window.removeEventListener('storage', storageListener);
  }, []);

  return (
    <UserProfileContext.Provider value={{ userProfile, setUserProfile, loading }}>
      {children}
    </UserProfileContext.Provider>
  );
};

export const useUserProfileContext = () => useContext(UserProfileContext);