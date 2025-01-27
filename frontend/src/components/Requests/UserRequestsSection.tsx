// src/components/Requests/UserRequestsSection.tsx

import React from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "../ui/dialog";
import { Button } from "../ui/button";
import { Input } from "../ui/input";
import { Label } from "../ui/label";
import { Card, CardContent } from "../ui/card";
import { Request, RequestType } from "@/types";
import { Loader2 } from "lucide-react"; // Import Loader2

type UserRequestsSectionProps = {
  handleRequestSubmit: (type: RequestType) => Promise<void>; // Ensure handleRequestSubmit is async and returns a Promise
  requests: Request[];
  newRequest: {
    organization_name: string;
    certification_body_name: string;
    description: string;
    address: string;
    contactEmail: string;
    contactPhone: string;
  };
  setNewRequest: React.Dispatch<
    React.SetStateAction<{
      organization_name: string;
      certification_body_name: string;
      description: string;
      address: string;
      contactEmail: string;
      contactPhone: string;
    }>
  >;
  isSubmitting: boolean; // Add isSubmitting prop
};

const UserRequestsSection: React.FC<UserRequestsSectionProps> = ({
  requests,
  handleRequestSubmit,
  newRequest,
  setNewRequest,
  isSubmitting, // Receive isSubmitting prop
}) => {
  const handleInputChange = (
    e: React.ChangeEvent<HTMLInputElement> | React.ChangeEvent<HTMLTextAreaElement>
  ) => {
    const { name, value } = e.target;
    setNewRequest((prevState) => ({
      ...prevState,
      [name]: value,
    }));
  };

  return (
    <div className="grid gap-6">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Request Organization Creation */}
        <Dialog>
          <DialogTrigger asChild>
            <Button className="w-full bg-primary text-primary-foreground hover:bg-primary/90" disabled={isSubmitting}> {/* Disable when submitting */}
              Request Organization Creation
            </Button>
          </DialogTrigger>
          <DialogContent className="bg-card">
            <DialogHeader>
              <DialogTitle>New Organization Request</DialogTitle>
            </DialogHeader>
            <div className="space-y-4">
              <div>
                <Label htmlFor="org-name">Organization Name</Label>
                <Input
                  id="org-name"
                  name="organization_name" // Add name attribute
                  value={newRequest.organization_name}
                  onChange={handleInputChange} // Use handleInputChange
                  className="bg-muted"
                  required
                />
              </div>
              <div>
                <Label htmlFor="org-description">Description</Label>
                <Input
                  id="org-description"
                  name="description" // Add name attribute
                  value={newRequest.description}
                  onChange={handleInputChange} // Use handleInputChange
                  className="bg-muted"
                  required
                />
              </div>
              <div>
                <Label htmlFor="org-address">Address</Label>
                <Input
                  id="org-address"
                  name="address" // Add name attribute
                  value={newRequest.address}
                  onChange={handleInputChange} // Use handleInputChange
                  className="bg-muted"
                  required
                />
              </div>
              <div>
                <Label htmlFor="org-contactEmail">Contact Email</Label>
                <Input
                  id="org-contactEmail"
                  type="email"
                  name="contactEmail" // Add name attribute
                  value={newRequest.contactEmail}
                  onChange={handleInputChange} // Use handleInputChange
                  className="bg-muted"
                  required
                />
              </div>
              <div>
                <Label htmlFor="org-contactPhone">Contact Phone</Label>
                <Input
                  id="org-contactPhone"
                  type="tel"
                  name="contactPhone" // Add name attribute
                  value={newRequest.contactPhone}
                  onChange={handleInputChange} // Use handleInputChange
                  className="bg-muted"
                  required
                />
              </div>
              <Button
                onClick={() => handleRequestSubmit("Organization")}
                className="w-full bg-primary text-primary-foreground hover:bg-primary/90"
                disabled={isSubmitting} // Disable when submitting
              >
                {isSubmitting ? ( // Show spinner when submitting
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Submitting...
                  </>
                ) : (
                  "Submit Request"
                )}
              </Button>
            </div>
          </DialogContent>
        </Dialog>

        {/* Request Certification Body Creation */}
        <Dialog>
          <DialogTrigger asChild>
            <Button className="w-full bg-primary text-primary-foreground hover:bg-primary/90" disabled={isSubmitting}> {/* Disable when submitting */}
              Request Certification Body Creation
            </Button>
          </DialogTrigger>
          <DialogContent className="bg-card">
            <DialogHeader>
              <DialogTitle>New Certification Body Request</DialogTitle>
            </DialogHeader>
            <div className="space-y-4">
              <div>
                <Label htmlFor="cb-name">Certification Body Name</Label>
                <Input
                  id="cb-name"
                  name="certification_body_name" // Add name attribute
                  value={newRequest.certification_body_name}
                  onChange={handleInputChange} // Use handleInputChange
                  className="bg-muted"
                  required
                />
              </div>

              <div>
                <Label htmlFor="cb-address">Address</Label>
                <Input
                  id="cb-address"
                  name="address" // Add name attribute
                  value={newRequest.address}
                  onChange={handleInputChange} // Use handleInputChange
                  className="bg-muted"
                  required
                />
              </div>
              <div>
                <Label htmlFor="cb-contactEmail">Contact Email</Label>
                <Input
                  id="cb-contactEmail"
                  type="email"
                  name="contactEmail" // Add name attribute
                  value={newRequest.contactEmail}
                  onChange={handleInputChange} // Use handleInputChange
                  className="bg-muted"
                  required
                />
              </div>
              <div>
                <Label htmlFor="cb-contactPhone">Contact Phone</Label>
                <Input
                  id="cb-contactPhone"
                  type="tel"
                  name="contactPhone" // Add name attribute
                  value={newRequest.contactPhone}
                  onChange={handleInputChange} // Use handleInputChange
                  className="bg-muted"
                  required
                />
              </div>
              <Button
                onClick={() => handleRequestSubmit("Certification Body")}
                className="w-full bg-primary text-primary-foreground hover:bg-primary/90"
                disabled={isSubmitting} // Disable when submitting
              >
                {isSubmitting ? ( // Show spinner when submitting
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Submitting...
                  </>
                ) : (
                  "Submit Request"
                )}
              </Button>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      {/* Display User's Existing Requests */}
      <Card className="bg-card">
        <CardContent className="p-6">
          <h2 className="text-lg font-semibold mb-4">Your Requests</h2>
          <div className="space-y-4">
            {requests.map((request) => (
              <Card key={request.id} className="bg-muted">
                <CardContent className="p-4">
                  <h3 className="font-medium">
                    {request.data.name as string || "Unnamed Request"}
                  </h3>
                  <p className="text-sm text-muted-foreground">
                    Type: {request.type}
                  </p>
                  <p className="text-sm text-muted-foreground">
                    Status: {request.status}
                  </p>
                  {/* Display additional fields */}
                  {Object.entries(request.data).map(([key, value]) => (
                    key !== "name" && key !== "description" && (
                      <p key={key} className="text-sm text-muted-foreground">
                        {key.replace(/_/g, " ").toUpperCase()}: {String(value)}
                      </p>
                    )
                  ))}
                </CardContent>
              </Card>
            ))}
            {requests.length === 0 && (
              <p className="text-muted-foreground text-sm">
                You have no requests.
              </p>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default UserRequestsSection;