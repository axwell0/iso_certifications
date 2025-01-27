    import React from "react";
    import { Card, CardContent } from "../ui/card";
    import { Request } from "@/types";
    import RequestCard from "./RequestCard";

    type RequestContainerProps = {
      title: string;
      requests: Request[];
      statusColor?: string;
      setProcessingRequest?: React.Dispatch<
        React.SetStateAction<{
          id: string;
          action: "approve" | "reject";
        } | null>
      >;
      openDialog?: () => void;
    };

    const RequestContainer: React.FC<RequestContainerProps> = ({
      title,
      requests,
      statusColor,
      setProcessingRequest,
      openDialog,
    }) => (
      <Card className="bg-card">
        <CardContent className="p-6">
          <h2 className="text-lg font-semibold mb-4">{title}</h2>
          <div className="space-y-4">
            {requests.map((request) => (
              <RequestCard
                key={request.id}
                request={request}
                statusColor={statusColor}
                setProcessingRequest={setProcessingRequest}
                openDialog={openDialog}
              />
            ))}
            {requests.length === 0 && (
              <p className="text-muted-foreground text-sm">
                No {title.toLowerCase()} requests
              </p>
            )}
          </div>
        </CardContent>
      </Card>
    );

    export default RequestContainer;
