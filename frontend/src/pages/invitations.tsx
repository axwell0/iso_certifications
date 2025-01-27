// src/pages/Organization/Invitations.tsx
import React, { useState, useEffect } from "react";
import Layout from "@/components/Layout/Layout";
import Header from "@/components/Layout/Header";
import { fetchWithAuth } from "@/utils/api";
import { useUserProfileContext } from "@/context/UserProfileContext";
import { Loader2 } from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";

interface Invitation {
  id: string;
  email: string;
  role: string;
  status: string;
  expires_at: string;
}

const Invitations: React.FC = () => {
  const { userProfile } = useUserProfileContext();
  const { toast } = useToast();
  const [isInviting, setIsInviting] = useState(false);
  const [revokingId, setRevokingId] = useState<string | null>(null);
  const [invitations, setInvitations] = useState<Invitation[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [inviteEmail, setInviteEmail] = useState("");
  const [selectedRole, setSelectedRole] = useState("");

  useEffect(() => {
    const fetchInvitations = async () => {
      try {
        const response = await fetchWithAuth("/organization/invitations");
        if (!response.ok) throw new Error("Failed to fetch invitations");
        setInvitations(await response.json());
      } catch (error) {
        toast({
          title: "Error loading invitations",
          description: (error as Error).message,
          variant: "destructive",
        });
      } finally {
        setIsLoading(false);
      }
    };

    fetchInvitations();
  }, [toast]);

  const handleInviteMember = async () => {
    setIsInviting(true);
    try {
      const response = await fetchWithAuth("/organization/invite", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: inviteEmail, role: selectedRole }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || "Failed to send invitation");
      }

      toast({
        title: "Invitation sent",
        description: `Invitation sent to ${inviteEmail}`,
        variant: "default",
      });
      setInviteEmail("");
      setSelectedRole("");

      const invitationsResponse = await fetchWithAuth("/organization/invitations");
      setInvitations(await invitationsResponse.json());
      setInviteEmail("");
      setSelectedRole("");

    } catch (error) {
      toast({
        title: "Invitation failed",
        description: (error as Error).message,
        variant: "destructive",
      });
    } finally {
      setIsInviting(false);
    }
  };

  const handleRevokeInvitation = async (invitationId: string) => {
    setRevokingId(invitationId);
    try {
      const response = await fetchWithAuth("/organization/invitations/revoke", {
        method: "DELETE",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ id: invitationId }),
      });

      if (!response.ok) throw new Error("Failed to revoke invitation");

      toast({
        title: "Invitation revoked",
        description: "The invitation has been successfully revoked",
        variant: "default",
      });

      setInvitations(invitations.filter(inv => inv.id !== invitationId));
    } catch (error) {
      toast({
        title: "Revocation failed",
        description: (error as Error).message,
        variant: "destructive",
      });
    } finally {
      setRevokingId(null);
    }
  };

  return (
    <Layout role={userProfile?.role || "GUEST"}>
      <div className="space-y-6">
        <Header userName={userProfile?.name} />
        <div className="bg-card rounded-lg p-6 shadow-sm border">
          <div className="flex justify-between items-center mb-8">
            <h2 className="text-2xl font-semibold">Manage Invitations</h2>
          </div>

          {/* Invitation Form */}
          <div className="mb-8 space-y-6">
            <div className="flex gap-4 items-end">
              <div className="flex-1 space-y-2">
                <label className="text-sm font-medium text-foreground">Email Address</label>
                <Input
                  type="email"
                  placeholder="Enter email address"
                  value={inviteEmail}
                  onChange={(e) => setInviteEmail(e.target.value)}
                  disabled={isInviting}
                />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium text-foreground">Role</label>
                <Select onValueChange={setSelectedRole} disabled={isInviting}>
                  <SelectTrigger className="w-[180px]">
                    <SelectValue placeholder="Select role" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="employee">Employee</SelectItem>
                    <SelectItem value="manager">Manager</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <Button
                onClick={handleInviteMember}
                disabled={!inviteEmail || !selectedRole || isInviting}
                className="h-[40px]"
              >
                {isInviting ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Sending...
                  </>
                ) : (
                  "Send Invitation"
                )}
              </Button>
            </div>

            {/* Invitations List */}
            <div className="space-y-4">
              <h3 className="text-lg font-semibold">Pending Invitations</h3>
              {isLoading ? (
                <div className="flex justify-center items-center h-32">
                  <Loader2 className="h-8 w-8 animate-spin text-primary" />
                </div>
              ) : (
                <div className="border rounded-lg overflow-hidden">
                  <table className="w-full">
                    <thead className="bg-muted">
                      <tr>
                        <th className="px-4 py-3 text-left w-[35%]">Email</th>
                        <th className="px-4 py-3 text-left w-[20%]">Role</th>
                        <th className="px-4 py-3 text-left w-[25%]">Status</th>
                        <th className="px-4 py-3 text-left w-[20%]">Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {invitations.map((invitation) => {
                        const isPending = invitation.status.toLowerCase().includes("pending");
                        const isRevoking = revokingId === invitation.id;

                        return (
                          <tr key={invitation.id} className="border-b hover:bg-muted/50">
                            <td className="px-4 py-3">{invitation.email}</td>
                            <td className="px-4 py-3 capitalize">
                              {invitation.role.split('.').pop()}
                            </td>
                            <td className="px-4 py-3 capitalize">
                              {invitation.status.split('.').pop()}
                            </td>
                            <td className="px-4 py-3">
                              {isPending && (
                                <Button
                                  variant="destructive"
                                  size="sm"
                                  onClick={() => handleRevokeInvitation(invitation.id)}
                                  disabled={isRevoking}
                                >
                                  {isRevoking ? (
                                    <>
                                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                      Revoking...
                                    </>
                                  ) : (
                                    "Revoke"
                                  )}
                                </Button>
                              )}
                            </td>
                          </tr>
                        )}
                      )}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </Layout>
  );
};

export default Invitations;