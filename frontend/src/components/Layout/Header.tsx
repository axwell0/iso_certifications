// src/components/Layout/Header.tsx
import React from "react";
import { Button } from "../ui/button";
import { LogOut } from "lucide-react";
import { useUserProfileContext } from "@/context/UserProfileContext";
import { useNavigate } from "react-router-dom";
import { useToast } from "@/hooks/useToast";
import { handleLogout } from "@/utils/handleLogout";

type HeaderProps = {
  userName?: string;
};

const Header: React.FC<HeaderProps> = ({ userName }) => {
  const { setUserProfile } = useUserProfileContext();
  const { toast } = useToast();
  const navigate = useNavigate();

  return (
    <header className="flex justify-between items-center mb-8">
      {userName && (
        <div>
          <h1 className="text-2xl font-semibold text-foreground">
            Welcome back, {userName}
          </h1>
          <p className="text-muted-foreground">
            {new Date().toLocaleDateString("en-US", {
              weekday: "long",
              year: "numeric",
              month: "long",
              day: "numeric",
            })}
          </p>
        </div>
      )}
      <Button
        onClick={() => handleLogout(toast, navigate, setUserProfile)}
        variant="destructive"
        className="gap-2"
      >
        <LogOut className="w-4 h-4" />
        Logout
      </Button>
    </header>
  );
};

export default Header;