import { Icon } from "@iconify/react";

const createIcon = (iconName) => ({ width = 24, height = 24, color = "currentColor" }) =>
  <Icon icon={iconName} width={width} height={height} color={color} />;

// Dashboard
export const DashboardIcon = createIcon("mage:dashboard");

// Employees & Roles
export const UsersIcon = createIcon("mage:users");

// Hotel
export const HotelIcon = createIcon("lucide:hotel");

// Menu Management
export const MenuIcon = createIcon("mynaui:reception-bell");

// Order
export const OrderIcon = createIcon("mingcute:bell-ringing-line");

// Billing
export const BillingIcon = createIcon("majesticons:receipt-text-line");

// Inventory
export const InventoryIcon = createIcon("flowbite:clipboard-list-outline");

// Reports
export const ReportsIcon = createIcon("uil:signal-alt-3");

// Settings
export const SettingsIcon = createIcon("tabler:settings");

// Dots
export const DotsIcon = createIcon("bx:wifi-0");

// Dropdown
export const CaretUpIcon = createIcon("mi:caret-up");
export const CaretDownIcon = createIcon("mi:caret-down");
export const CaretRightIcon=createIcon("mi:caret-right")

export const UpArrow=createIcon("prime:chevron-up");
export const RightArrow=createIcon("prime:chevron-right");


// Search
export const SearchIcon = createIcon("mi:search");

// Circle Chevron Down
export const CircleChevronDownIcon = createIcon("lucide:circle-chevron-down");

//option
export const OptionIcon = createIcon("proicons:more");

// Close / Dismiss
export const CloseIcon = createIcon("humbleicons:times");

//info
export const InfoIcon=createIcon("si:info-fill")

