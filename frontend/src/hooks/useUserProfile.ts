// src/hooks/useUserProfile.ts
import { useUserProfileContext } from "../context/UserProfileContext";

export function useUserProfile() {
  const { userProfile, loading } = useUserProfileContext();
  return {
    userProfile,
    loading,
    isAdmin: userProfile?.role === "ADMIN",
    isGuest: userProfile?.role === "GUEST"
  };
}