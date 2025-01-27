// src/components/Requests/RequestContainers.tsx
import React from "react";
import { Request } from "../../types";
import RequestContainer from "./RequestContainer";

type RequestContainersProps = {
  pendingRequests: Request[];
  approvedRequests: Request[];
  rejectedRequests: Request[];
  setProcessingRequest: React.Dispatch<
    React.SetStateAction<{
      id: string;
      action: "approve" | "reject";
    } | null>
  >;
  openDialog: () => void;
};

const RequestContainers: React.FC<RequestContainersProps> = ({
  pendingRequests,
  approvedRequests,
  rejectedRequests,
  setProcessingRequest,
  openDialog,
}) => (
  <>
    <RequestContainer
      title="Pending Requests"
      requests={pendingRequests}
      statusColor="text-yellow-600"
      setProcessingRequest={setProcessingRequest}
      openDialog={openDialog}
    />
    <RequestContainer
      title="Approved Requests"
      requests={approvedRequests}
      statusColor="#01A87B"
    />
    <RequestContainer
      title="Rejected Requests"
      requests={rejectedRequests}
      statusColor="text-red-600"
    />
  </>
);

export default RequestContainers;
