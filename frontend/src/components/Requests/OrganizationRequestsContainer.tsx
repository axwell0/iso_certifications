// src/components/Requests/OrganizationRequestsContainer.tsx
import React from "react";
import { Card, CardContent } from "../ui/card";
import { Request } from "../../types";
import RequestCard from "./RequestCard";

type OrganizationRequestsContainerProps = {
  requests: Request[];
};

const OrganizationRequestsContainer: React.FC<OrganizationRequestsContainerProps> = ({ requests }) => (
  <Card className="bg-card">
    <CardContent className="p-6">
      <h2 className="text-lg font-semibold mb-4">Your Organization's Requests</h2>
      <div className="space-y-4">
        {requests.map((request) => (
          <RequestCard key={request.id} request={request} />
        ))}
        {requests.length === 0 && (
          <p className="text-muted-foreground text-sm">
            No requests found for your organization.
          </p>
        )}
      </div>
    </CardContent>
  </Card>
);

export default OrganizationRequestsContainer;
