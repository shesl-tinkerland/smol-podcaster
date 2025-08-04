"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import { FileText, Mic, Settings } from "lucide-react";

const navigation = [
  { name: "Create Writeup", href: "/", icon: FileText },
  { name: "Sync Chapters", href: "/sync", icon: Settings },
  { name: "Edit Episodes", href: "/episodes", icon: Mic },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="w-64 bg-gray-900 h-screen flex flex-col">
      <div className="p-6">
        <h1 className="text-2xl font-bold text-white">Smol Podcaster</h1>
      </div>
      <nav className="flex-1 px-6 space-y-1">
        {navigation.map((item) => {
          const isActive = pathname === item.href;
          return (
            <Link
              key={item.name}
              href={item.href}
              className={cn(
                "flex items-center px-4 py-2 text-sm font-medium rounded-lg transition-colors",
                isActive
                  ? "bg-primary text-white"
                  : "text-gray-300 hover:bg-gray-800 hover:text-white"
              )}
            >
              <item.icon className="mr-3 h-5 w-5" />
              {item.name}
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}