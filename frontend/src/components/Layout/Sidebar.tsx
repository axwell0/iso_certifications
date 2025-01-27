// src/components/Layout/Sidebar.tsx
import React, { useState } from "react";
import { sidebarItems, adminSidebarItems, guestSidebarItems, orgSidebarItems } from "@/data/sidebarItems";
import { useNavigate, useLocation } from "react-router-dom";
import { ChevronDown, ChevronRight } from "lucide-react";

type SidebarProps = {
  role: string;
};

type ExpandedItems = {
  [key: string]: boolean;
};

const Sidebar: React.FC<SidebarProps> = ({ role }) => {
  const navigate = useNavigate();
  const location = useLocation();
  const [expandedItems, setExpandedItems] = useState<ExpandedItems>({});
  let itemsToDisplay = sidebarItems;

  if (role === "ADMIN") {
    itemsToDisplay = [...sidebarItems, ...adminSidebarItems];
  } else if (role === "GUEST") {
    itemsToDisplay = guestSidebarItems.length > 0 ? guestSidebarItems : sidebarItems;
  } else if (["MANAGER", "EMPLOYEE"].includes(role)) {
    itemsToDisplay = [...sidebarItems, ...orgSidebarItems];
  }

  const toggleExpansion = (label: string) => {
    setExpandedItems(prev => ({ ...prev, [label]: !prev[label] }));
  };

  const handleNavigation = (href: string) => {
    if (location.pathname !== href) {
      navigate(href);
    }
  };

  const renderItem = (item: any, depth = 0) => {
    const isActive = location.pathname === item.href;
    const hasChildren = item.children && item.children.length > 0;
    const isExpanded = expandedItems[item.label];

    return (
      <div key={item.label} className="space-y-1">
        <div
          className={`flex items-center gap-3 px-3 py-2 rounded-lg text-sm cursor-pointer ${
            isActive
              ? "bg-primary text-primary-foreground pointer-events-none"
              : "text-muted-foreground hover:bg-muted"
          }`}
          onClick={() => {
            if (hasChildren) {
              toggleExpansion(item.label);
            } else {
              handleNavigation(item.href);
            }
          }}
        >
          <item.icon className="w-5 h-5" />
          <span className="flex-1">{item.label}</span>
          {hasChildren && (
            <span className="ml-auto">
              {isExpanded ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
            </span>
          )}
        </div>

        {hasChildren && isExpanded && (
          <div className="ml-4 space-y-1">
            {item.children.map((child: any) => (
              <div
                key={child.label}
                onClick={() => handleNavigation(child.href)}
                className={`flex items-center gap-3 px-3 py-2 rounded-lg text-sm cursor-pointer ${
                  location.pathname === child.href
                    ? "bg-primary/10 text-primary pointer-events-none"
                    : "text-muted-foreground hover:bg-muted"
                }`}
              >
                <child.icon className="w-5 h-5" />
                {child.label}
              </div>
            ))}
          </div>
        )}
      </div>
    );
  };

  return (
    <aside className="w-64 bg-card border-r border-muted p-4">
      <div className="flex items-center gap-2 mb-8">
        <div className="w-8 h-8 bg-primary rounded-lg" />
        <span className="text-lg font-semibold text-foreground">CertiPro</span>
      </div>
      <nav className="space-y-2">{itemsToDisplay.map(item => renderItem(item))}</nav>
    </aside>
  );
};

export default Sidebar;