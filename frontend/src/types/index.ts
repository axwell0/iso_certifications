// src/types/index.ts
export type RequestType = "Organization" | "Certification Body";

export type RequestStatus = "PENDING" | "APPROVED" | "REJECTED";

export type Request = {
  id: string;
  type: RequestType;
  status: RequestStatus;
  data: Record<string, unknown>;
};

export type UserProfile = {
  role: string;
  name: string;
  certification_body_name?: string;
  organization_name?: string;
};
