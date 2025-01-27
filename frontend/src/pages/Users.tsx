// src/pages/Users.tsx
import React, { useState, useEffect } from "react";
import Layout from "../components/Layout/Layout";
import Header from "../components/Layout/Header";
import { fetchWithAuth } from "../utils/api";
import { useUserProfileContext } from "../context/UserProfileContext";
import { Loader2 } from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import { Button } from "@/components/ui/button";

interface User {
  id: string;
  full_name: string;
  email: string;
  organization?: string;
  certification_body?: string;
  role?: string;
}

const Users: React.FC = () => {
  const { userProfile, loading } = useUserProfileContext();
  const { toast } = useToast();
  const [users, setUsers] = useState<User[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const fetchData = async () => {
      try {
        const usersUrl = userProfile?.role === "ADMIN"
          ? "/admin/users"
          : "/organization/members";
        const response = await fetchWithAuth(usersUrl, { method: "GET" });
        if (!response.ok) throw new Error("Failed to fetch users");
        setUsers(await response.json());
      } catch (error) {
        setError((error as Error).message);
        toast({
          title: "Error loading users",
          description: (error as Error).message,
          variant: "destructive",
        });
      } finally {
        setIsLoading(false);
      }
    };

    if (userProfile?.role) fetchData();
  }, [userProfile?.role, toast]);

  const handleDeleteUser = async (userId: string) => {
    try {
      const response = await fetchWithAuth(`/organization/members/remove`, {
        method: "DELETE",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_id: userId }),
      });

      if (!response.ok) throw new Error("Failed to delete user");
      setUsers(users.filter(user => user.id !== userId));
      toast({
        title: "User removed",
        description: "User has been removed from the organization",
        variant: "default",
      });
    } catch (error) {
      toast({
        title: "Error removing user",
        description: (error as Error).message,
        variant: "destructive",
      });
    }
  };

  if (loading) return null;

  return (
    <Layout role={userProfile?.role || "GUEST"}>
      <div className="space-y-6">
        <Header userName={userProfile?.name} />
        <div className="bg-card rounded-lg p-6 shadow-sm border">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-2xl font-semibold">
              {userProfile?.role === "ADMIN" ? "User Management" : "Organization Members"}
            </h2>
          </div>

          {/* Users Table */}
          {isLoading ? (
            <div className="flex justify-center items-center h-64">
              <Loader2 className="h-12 w-12 animate-spin text-primary" />
            </div>
          ) : error ? (
            <div className="text-center text-destructive">{error}</div>
          ) : (
            <div className="border rounded-lg overflow-hidden">
              <table className="w-full">
                <thead className="bg-muted">
                  <tr>
                    <th className="px-4 py-3 text-left">Name</th>
                    <th className="px-4 py-3 text-left">Email</th>
                    {userProfile?.role === "ADMIN" && (
                      <>
                        <th className="px-4 py-3 text-left">Organization</th>
                        <th className="px-4 py-3 text-left">Certification Body</th>
                      </>
                    )}
                    <th className="px-4 py-3 text-left">Role</th>
                    {userProfile?.role === 'MANAGER' && (
                      <th className="px-4 py-3 text-left">Actions</th>
                    )}
                  </tr>
                </thead>
                <tbody>
                  {users.map((user) => {
                    const showActions = userProfile?.role === 'MANAGER';
                    return (
                      <tr key={user.id} className="border-b hover:bg-muted/50">
                        <td className="px-4 py-3">{user.full_name}</td>
                        <td className="px-4 py-3">{user.email}</td>
                        {userProfile?.role === "ADMIN" && (
                          <>
                            <td className="px-4 py-3">{user.organization || '-'}</td>
                            <td className="px-4 py-3">{user.certification_body || '-'}</td>
                          </>
                        )}
                        <td className="px-4 py-3 capitalize">{user.role.split('.')[1] || '-'}</td>
                        {showActions && (
                          <td className="px-4 py-3">
                            <Button
                              variant="destructive"
                              size="sm"
                              onClick={() => handleDeleteUser(user.id)}
                            >
                              Remove
                            </Button>
                          </td>
                        )}
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </Layout>
  );
};

export default Users;