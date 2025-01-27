// src/pages/Dashboard.tsx
import React from "react";
import Layout from "../components/Layout/Layout";
import Header from "../components/Layout/Header";
import RequestContainers from "../components/Requests/RequestContainers";
import RequestDialog from "../components/Requests/RequestDialog";
import UserRequestsSection from "../components/Requests/UserRequestsSection";
import OrganizationRequestsContainer from "../components/Requests/OrganizationRequestsContainer";
import { Button } from "../components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Loader2 } from "lucide-react";
import { useUserProfileContext } from "@/context/UserProfileContext";
import { useToast } from "../hooks/useToast";
import useDialog from "../hooks/useDialog";
import { useRequests } from "../hooks/useRequests";
import { useNavigate } from "react-router-dom";

const Dashboard: React.FC = () => {
  const { userProfile, setUserProfile, loading } = useUserProfileContext();
  const { toast } = useToast();
  const navigate = useNavigate();
  const { isOpen, open, close } = useDialog();
  const {
    pendingRequests,
    approvedRequests,
    rejectedRequests,
    orgRequests,
    newRequest,
    setNewRequest,
    isSubmittingRequest,
    submissionSuccess,
    comment,
    setComment,
    processingRequest,
    setProcessingRequest,
    handleRequestSubmit,
    handleRequestAction,
  } = useRequests(userProfile);

  if (loading || !userProfile) {
    return (
      <div className="flex justify-center items-center min-h-screen">
        <Loader2 className="h-12 w-12 animate-spin text-primary" />
      </div>
    );
  }
  console.log(userProfile)
  const getOrganizationName = () => {
    if (userProfile.organization_name) return userProfile.organization_name;
    if (userProfile.certification_body_name) return userProfile.certification_body_name;
    return "No Organization or Certification Body";
  };

  return (
    <Layout role={userProfile.role}>
      <Header userName={userProfile.name} />
      {userProfile.role === "GUEST" && (
        <>
          {submissionSuccess && (
            <div className="fixed top-4 left-1/2 transform -translate-x-1/2 z-50">
              <Card className="w-[380px] bg-green-400 text-white shadow-lg">
                <CardContent className="py-4 px-6">
                  Request successfully submitted!
                </CardContent>
              </Card>
            </div>
          )}
          <UserRequestsSection
            requests={[]}
            handleRequestSubmit={handleRequestSubmit}
            newRequest={newRequest}
            setNewRequest={setNewRequest}
            isSubmitting={isSubmittingRequest}
          />
        </>
      )}
      {userProfile.role === "ADMIN" && (
        <div className="grid gap-6">
          <RequestContainers
            pendingRequests={pendingRequests}
            approvedRequests={approvedRequests}
            rejectedRequests={rejectedRequests}
            setProcessingRequest={setProcessingRequest}
            openDialog={open}
          />
          <RequestDialog
            isOpen={isOpen}
            onClose={() => {
              setProcessingRequest(null);
              setComment("");
              close();
            }}
            comment={comment}
            setComment={setComment}
            onConfirm={handleRequestAction}
          />
        </div>
      )}
      {!["GUEST", "ADMIN"].includes(userProfile.role) && (
        <div className="space-y-6">
          <div className="flex justify-center items-center">
            <Button
              onClick={() => navigate("/organization/details")}
              variant="default"
              className="flex items-center gap-2 p-6 bg-muted rounded-lg hover:bg-muted-foreground transition-colors shadow-md"
            >
              <span>{getOrganizationName()}</span>
            </Button>
          </div>
          <OrganizationRequestsContainer requests={orgRequests} />
        </div>
      )}
    </Layout>
  );
};

export default Dashboard;