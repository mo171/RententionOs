import { Sidebar } from "@/components/layout/sidebar";
import { TopNavbar } from "@/components/layout/top-navbar";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="flex h-screen overflow-hidden bg-bg-base">
      {/* Fixed sidebar — does not scroll */}
      <Sidebar />

      {/* Main content area */}
      <div className="flex flex-col flex-1 overflow-hidden">
        {/* Fixed top navbar */}
        <TopNavbar />

        {/* Scrollable main content — scroll-contain isolates paint from sidebar */}
        <main className="flex-1 overflow-y-auto p-6 scroll-contain">
          {children}
        </main>
      </div>
    </div>
  );
}
