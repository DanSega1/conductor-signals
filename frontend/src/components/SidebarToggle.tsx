interface SidebarToggleProps {
  collapsed: boolean;
  onToggle: () => void;
}

export default function SidebarToggle({ collapsed, onToggle }: SidebarToggleProps) {
  return (
    <button
      onClick={onToggle}
      className="p-1.5 rounded-lg text-gray-500 hover:text-gray-300 hover:bg-gray-800 transition-colors"
      title={collapsed ? "Expand sidebar" : "Collapse sidebar"}
    >
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        {collapsed ? (
          <>
            <polyline points="15 18 9 12 15 6" />
          </>
        ) : (
          <>
            <polyline points="9 18 15 12 9 6" />
          </>
        )}
      </svg>
    </button>
  );
}
