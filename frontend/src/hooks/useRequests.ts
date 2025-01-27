import { useState, useEffect } from "react";
import { fetchWithAuth } from "../utils/api";
import { useToast } from "../hooks/useToast";
import { Request, RequestType, UserProfile } from "@/types";

type ProcessingRequest = {
  id: string;
  action: "approve" | "reject";
};

export function useRequests(userProfile: UserProfile | null) {
  const { toast } = useToast();

  // Admin requests (pending, approved, rejected)
  const [adminRequests, setAdminRequests] = useState<Request[]>([]);
  // Organization/Certification Body requests
  const [orgRequests, setOrgRequests] = useState<Request[]>([]);

  // Dialog states for processing requests (Admin)
  const [processingRequest, setProcessingRequest] = useState<ProcessingRequest | null>(null);
  const [comment, setComment] = useState("");

  // Guest-only: new request form
  const [newRequest, setNewRequest] = useState({
    organization_name: "",
    certification_body_name: "",
    description: "",
    address: "",
    contactEmail: "",
    contactPhone: "",
  });

  // Submission states for Guest requests
  const [isSubmittingRequest, setIsSubmittingRequest] = useState(false);
  const [submissionSuccess, setSubmissionSuccess] = useState(false);

  /**
   * Fetch admin requests (both Organizations and Certification Bodies).
   */
  const fetchAdminRequests = async () => {
    try {
      const [orgResponse, cbResponse] = await Promise.all([
        fetchWithAuth("/organization/requests/view"),
        fetchWithAuth("/certification_body/requests/view"),
      ]);
      if (!orgResponse.ok || !cbResponse.ok) {
        throw new Error("Failed to fetch admin requests");
      }

      const orgData = await orgResponse.json();
      const cbData = await cbResponse.json();

      setAdminRequests([
        ...(orgData?.map((r: any) => ({
          id: r.id,
          type: "Organization",
          status: r.status,
          data: r,
        })) || []),
        ...(cbData?.map((r: any) => ({
          id: r.id,
          type: "Certification Body",
          status: r.status,
          data: r,
        })) || []),
      ]);
    } catch (error) {
      console.error("Error fetching admin requests:", error);
      // fetchWithAuth handles error toast
    }
  };

  /**
   * Fetch organization/cert-body requests for non-guest, non-admin users.
   * @param orgName The organization name if applicable
   * @param cbName The certification body name if applicable
   */
  const fetchOrgRequests = async (orgName?: string, cbName?: string) => {
    try {
      if (!orgName && !cbName) return; // user belongs to neither

      let endpoint = "";
      if (orgName) {
        endpoint = `/organization/requests/view?name=${encodeURIComponent(orgName)}`;
      } else if (cbName) {
        endpoint = `/certification_body/requests/view?name=${encodeURIComponent(cbName)}`;
      }

      const response = await fetchWithAuth(endpoint);
      if (!response.ok) throw new Error("Failed to fetch organization requests");

      const data = await response.json();
      setOrgRequests(
        data?.map((r: any) => ({
          id: r.id,
          type: r.type || (orgName ? "Organization" : "Certification Body"),
          status: r.status,
          data: r,
        })) || []
      );
    } catch (error) {
      console.error("Error fetching organization requests:", error);
      // fetchWithAuth handles error toast
    }
  };

  /**
   * Role-based effect to fetch requests upon user profile availability.
   */
  useEffect(() => {
    if (!userProfile) return;

    if (userProfile.role === "ADMIN") {
      fetchAdminRequests();
    } else if (userProfile.role !== "GUEST") {
      fetchOrgRequests(userProfile.organization_name, userProfile.certification_body_name);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [userProfile]);

  /**
   * Create a new request (Guest users).
   * @param type "Organization" or "Certification Body"
   */
  const handleRequestSubmit = async (type: RequestType) => {
    setIsSubmittingRequest(true);
    setSubmissionSuccess(false); // reset success state
    try {
      const endpoint =
        type === "Organization"
          ? "/organization/requests/create"
          : "/certification_body/requests/create";

      let body;
      if (newRequest.certification_body_name === "") {
        body = {
          organization_name: newRequest.organization_name,
          description: newRequest.description,
          address: newRequest.address,
          contact_email: newRequest.contactEmail,
          contact_phone: newRequest.contactPhone,
        };
      } else {
        body = {
          certification_body_name: newRequest.certification_body_name,
          address: newRequest.address,
          contact_email: newRequest.contactEmail,
          contact_phone: newRequest.contactPhone,
        };
      }

      await fetchWithAuth(endpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });

      toast({
        title: "Request Submitted",
        description: "Your request has been submitted for review.",
        variant: "testing out", // custom variant example
      });
      setSubmissionSuccess(true);

      // Clear form
      setNewRequest({
        organization_name: "",
        certification_body_name: "",
        description: "",
        address: "",
        contactEmail: "",
        contactPhone: "",
      });

      // Refresh requests if user is an organization/cert-body
      if (userProfile.role !== "ADMIN" && userProfile.role !== "GUEST") {
        fetchOrgRequests(userProfile.organization_name, userProfile.certification_body_name);
      }
    } catch (error) {
      console.error("Error submitting request:", error);
    } finally {
      setIsSubmittingRequest(false);
      setTimeout(() => setSubmissionSuccess(false), 3000);
    }
  };

  /**
   * Approve or reject a request (Admins only).
   */
  const handleRequestAction = async () => {
    if (!processingRequest) return;
    try {
      const foundRequest = adminRequests.find((r) => r.id === processingRequest.id);
      if (!foundRequest) throw new Error("Request not found");

      const endpoint =
        foundRequest.type === "Organization"
          ? `/organization/requests/${processingRequest.action}`
          : `/certification_body/requests/${processingRequest.action}`;

      await fetchWithAuth(endpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          admin_comment: comment,
          id: processingRequest.id,
        }),
      });

      toast({
        title: `Request ${processingRequest.action}`,
        description: `The request has been ${processingRequest.action} successfully.`,
          variant:'none'
      });

      // Reset state
      setProcessingRequest(null);
      setComment("");

      // Refetch to update adminRequests
      await fetchAdminRequests();
    } catch (error) {
      console.error(`Error processing request: ${error}`);
    }
  };

  // Filters for Admin
  const pendingRequests = adminRequests.filter((r) => r.status.includes("PENDING"));
  const approvedRequests = adminRequests.filter((r) => r.status.includes("APPROVED"));
  const rejectedRequests = adminRequests.filter((r) => r.status.includes("REJECTED"));

  return {
    // Data
    adminRequests,
    orgRequests,
    pendingRequests,
    approvedRequests,
    rejectedRequests,

    // States
    newRequest,
    setNewRequest,
    isSubmittingRequest,
    submissionSuccess,
    comment,
    setComment,
    processingRequest,
    setProcessingRequest,

    // Handlers
    handleRequestSubmit,
    handleRequestAction,
  };
}
