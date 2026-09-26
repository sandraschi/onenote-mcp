import {
  BookOpen,
  Bot,
  ChevronLeft,
  ChevronRight,
  Grid,
  HelpCircle,
  History,
  LayoutDashboard,
  ScrollText,
  Search,
  Server,
  Settings,
  Shield,
  Sparkles,
  Wrench,
} from "lucide-react";
import { useEffect, useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { cn } from "@/common/utils";
import { API_BASE } from "@/lib/api";

interface SidebarProps {
  collapsed: boolean;
  onToggle: () => void;
}

export function Sidebar({ collapsed, onToggle }: SidebarProps) {
  const location = useLocation();
  const [backendOk, setBackendOk] = useState<boolean | null>(null);
  const [version, setVersion] = useState("");

  useEffect(() => {
    let cancelled = false;
    const probe = async () => {
      try {
        const r = await fetch(`${API_BASE}/status`);
        if (!r.ok) throw new Error();
        const d = (await r.json()) as { version?: string };
        if (!cancelled) {
          setBackendOk(true);
          setVersion(d.version || "");
        }
      } catch {
        if (!cancelled) {
          setBackendOk(false);
          setVersion("");
        }
      }
    };
    probe();
    const timer = setInterval(probe, 30000);
    return () => {
      cancelled = true;
      clearInterval(timer);
    };
  }, []);

  const navItems = [
    { href: "/", label: "Overview", icon: LayoutDashboard },
    { href: "/notebooks", label: "Notebooks", icon: BookOpen },
    { href: "/recent", label: "Recent", icon: History },
    { href: "/search", label: "Search", icon: Search },
    { href: "/tools", label: "Tools", icon: Wrench },
    { href: "/status", label: "Status", icon: Shield },
    { href: "/apps", label: "App Hub", icon: Grid },
    { href: "/chat", label: "AI Command", icon: Bot },
    { href: "/logging", label: "Logging", icon: ScrollText },
    { href: "/skills", label: "Skills", icon: Sparkles },
    { href: "/help", label: "Help", icon: HelpCircle },
    { href: "/settings", label: "Settings", icon: Settings },
  ];

  return (
    <aside
      className={cn(
        "relative flex flex-col border-r border-slate-800 bg-slate-950/50 backdrop-blur-xl transition-all duration-300 ease-in-out",
        collapsed ? "w-16" : "w-64",
      )}
    >
      <div
        className={cn(
          "flex items-center border-b border-slate-800 px-4",
          collapsed ? "h-auto flex-col gap-1 py-3" : "h-16 justify-between",
        )}
      >
        <div className="flex items-center gap-2 font-semibold text-slate-100">
          <Server className="h-6 w-6 text-blue-500" />
          {!collapsed && (
            <span className="animate-in fade-in duration-300">OneNote MCP</span>
          )}
        </div>
        <button
          type="button"
          onClick={onToggle}
          title={collapsed ? "Expand sidebar" : "Collapse sidebar"}
          aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
          data-testid="sidebar-toggle"
          className="rounded-md p-1.5 text-slate-400 hover:bg-slate-800 hover:text-white transition-colors"
        >
          {collapsed ? (
            <ChevronRight className="h-5 w-5" />
          ) : (
            <ChevronLeft className="h-5 w-5" />
          )}
        </button>
      </div>

      <nav className="flex-1 space-y-1 p-2">
        {navItems.map((item) => {
          const isActive = location.pathname === item.href;
          return (
            <Link
              key={item.href}
              to={item.href}
              className={cn(
                "group flex items-center rounded-md px-3 py-2 text-sm font-medium transition-colors hover:bg-slate-800 hover:text-white",
                isActive ? "bg-slate-800 text-white" : "text-slate-400",
                collapsed ? "justify-center" : "justify-start",
              )}
            >
              <item.icon
                className={cn(
                  "h-5 w-5",
                  !collapsed && "mr-3",
                  isActive && "text-blue-400",
                )}
              />
              {!collapsed && <span>{item.label}</span>}

              {/* Tooltip for collapsed mode */}
              {collapsed && (
                <div className="absolute left-full ml-2 hidden rounded bg-slate-800 px-2 py-1 text-xs text-white group-hover:block z-50 whitespace-nowrap">
                  {item.label}
                </div>
              )}
            </Link>
          );
        })}
      </nav>

      <div className="border-t border-slate-800 p-2">
        <div
          className={cn(
            "flex items-center gap-2 px-3 py-2 text-sm text-slate-400",
            collapsed && "justify-center px-0",
          )}
          title={
            backendOk === null
              ? "Checking backend..."
              : backendOk
                ? `Backend connected${version ? ` (v${version})` : ""}`
                : "Backend unreachable"
          }
          data-testid="sidebar-backend"
        >
          <span
            className={cn(
              "h-2 w-2 rounded-full shrink-0",
              backendOk === null
                ? "bg-slate-500"
                : backendOk
                  ? "bg-emerald-500"
                  : "bg-red-500",
            )}
          />
          {!collapsed && (
            <span>
              {backendOk === null
                ? "Checking..."
                : backendOk
                  ? `Backend${version ? ` v${version}` : ""}`
                  : "Backend down"}
            </span>
          )}
        </div>
      </div>
    </aside>
  );
}
