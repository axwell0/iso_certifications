// src/components/Requests/RequestCard.tsx
import React from "react";
import { Card, CardContent } from "../ui/card";
import { Button } from "../ui/button";
import { Request } from "../../types";

type RequestCardProps = {
  request: Request;
  statusColor?: string;
  setProcessingRequest?: React.Dispatch<
    React.SetStateAction<{
      id: string;
      action: "approve" | "reject";
    } | null>
  >;
  openDialog?: () => void;
};

const RequestCard: React.FC<RequestCardProps> = ({
  request,
  statusColor,
  setProcessingRequest,
  openDialog,
}) => (
  <Card className="bg-muted">
    <CardContent className="p-4">
      <div className="flex justify-between items-center">
        <div>
          <h3 className="font-medium">
            {request.data.certification_body_name ||
              request.data.organization_name ||
              "Unnamed Request"}
          </h3>
          <p><span className="font-bold text-yellow-500">Type </span>
            <span className="text-sm text-muted-foreground">{request.type}</span>
          </p>

          {Object.entries(request.data).map(([key, value]) => {
            if (key.includes("id") || key === "updated_at") return null;

            const displayKey = key.replace(/_/g, " ").toUpperCase();
            let displayValue = value;

            if (key === "status") {
              if (String(value).includes("APPROVED")) {
                displayValue = "APPROVED";
              } else if (String(value).includes("REJECTED")) {
                displayValue = "REJECTED";
              } else if (String(value).includes("PENDING")) {
                displayValue = "PENDING";
              } else {
                return null;
              }
            }

            const highlightClass =
              key === "status" && displayValue === "APPROVED"
                ? "text-green-400 font-bold"
                : key === "status" && displayValue === "REJECTED"
                ? "text-red-600 font-bold"
                : key === "status" && displayValue === "PENDING"
                ? "text-yellow-600 font-bold"
                : "";

            return (
              <p
                key={key}
                className={`text-sm text-muted-foreground ${highlightClass}`}
              >
                <span className="font-bold text-yellow-500">{displayKey}:</span> {String(displayValue)}
              </p>
            );
          })}

        </div>
        {request.status.includes("PENDING") && setProcessingRequest && openDialog && (
          <div className="flex gap-2">
            <Button
              onClick={() => {
                setProcessingRequest({
                  id: request.id,
                  action: "approve",
                });
                openDialog();
              }}
              variant="default"
              className="bg-green-400 text-primary-foreground hover:bg-green-400 text-white"
            >
              Approve
            </Button>
            <Button
              onClick={() => {
                setProcessingRequest({
                  id: request.id,
                  action: "reject",
                });
                openDialog();
              }}
              variant="destructive"
            >
              Reject
            </Button>
          </div>
        )}
      </div>
    </CardContent>
  </Card>
);

export default RequestCard;
