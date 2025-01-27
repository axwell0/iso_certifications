// src/data/sidebarItems.ts
import {
  LayoutDashboard,
  BookOpen,
  Users,
  ClipboardList,
  GraduationCap,
  MessageCircle,
  Building, LucideProps,
} from "lucide-react";

export const sidebarItems: ({
  icon: React.ForwardRefExoticComponent<Omit<LucideProps, "ref"> & React.RefAttributes<SVGSVGElement>>;
  label: string;
  href: string
} | {
  icon: React.ForwardRefExoticComponent<Omit<LucideProps, "ref"> & React.RefAttributes<SVGSVGElement>>;
  label: string;
  href: string
} | {
  icon: React.ForwardRefExoticComponent<Omit<LucideProps, "ref"> & React.RefAttributes<SVGSVGElement>>;
  label: string;
  href: string
} | {
  children: ({
    icon: React.ForwardRefExoticComponent<Omit<LucideProps, "ref"> & React.RefAttributes<SVGSVGElement>>;
    label: string;
    href: string
  } | {
    icon: React.ForwardRefExoticComponent<Omit<LucideProps, "ref"> & React.RefAttributes<SVGSVGElement>>;
    label: string;
    href: string
  } | {
    icon: React.ForwardRefExoticComponent<Omit<LucideProps, "ref"> & React.RefAttributes<SVGSVGElement>>;
    label: string;
    href: string
  })[];
  icon: React.ForwardRefExoticComponent<Omit<LucideProps, "ref"> & React.RefAttributes<SVGSVGElement>>;
  label: string
})[] = [
  { icon: LayoutDashboard, label: "Dashboard", href: "/dashboard" },
  { icon: BookOpen, label: "Standards", href: "/standards" },
  {
    label: 'Chat Assistant',
    href: '/chat',
    icon: MessageCircle,
  }
];

export const adminSidebarItems = [
  { icon: Users, label: "Users", href: "/users" },
];

// src/data/sidebarItems.ts
// src/data/sidebarItems.ts
export const orgSidebarItems = [
  {
    icon: Building,
    label: "Organization",
    children: [
      { icon: Users, label: "Users", href: "/organization/users" },
      { icon: ClipboardList, label: "Audits", href: "/organization/audits" },
      { icon: GraduationCap, label: "Certifications", href: "/organization/certifications" },
      {
        icon: ClipboardList,
        label: "Invitations",
        href: "/organization/invitations"
      }
    ],
  },
];
export const guestSidebarItems = [];