// src/utils/handleLogout.ts
export const handleLogout = (
  toast: any,
  navigate: (path: string) => void,
  setUserProfile: (profile: null) => void
) => {
  localStorage.removeItem("accessToken");
  setUserProfile(null);
  toast({
    title: "Logged out",
    description: "You have been successfully logged out.",
    variant: 'none'
  });
  navigate("/login");
};