"use client";

import { useDashboard } from "@/hooks/useDashboard";
import UploadSection from "@/components/dashboard/UploadSection";
import LeaderboardSection from "@/components/dashboard/LeaderboardSection";
import CandidateModal from "@/components/dashboard/CandidateModal";
import { IoLogOutOutline, IoListOutline, IoCloudUploadOutline } from "react-icons/io5";
import { toast } from "sonner";

export default function DashboardPage() {
  const {
    candidates,
    loading,
    error,
    view,
    setView,
    selectedCandidate,
    setSelectedCandidate,
    fetchCandidates,
    uploadResumes,
    inviteCandidate,
    clearLeaderboard,
    logout,
    isVerifying
  } = useDashboard();

  if (isVerifying) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-black text-white">
        <div className="flex flex-col items-center gap-4">
          <div className="h-10 w-10 animate-spin rounded-full border-4 border-cyan-500 border-t-transparent"></div>
          <p className="font-mono text-sm text-cyan-400 animate-pulse">Verifying Access...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen">

      {/* Header */}
      <header className="sticky top-0 z-30 border-b border-[var(--border-color)] bg-[var(--bg-primary)] px-6 py-4 shadow-sm">
        <div className="mx-auto flex max-w-7xl items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="relative h-14 w-auto">
              <img src="/VirexLogo.jpg" alt="Virex AI Logo" className="h-full w-auto object-contain rounded-md" />
            </div>
          </div>

          <div className="flex items-center gap-4">
            <div className="hidden md:flex gap-1 bg-[var(--bg-secondary)] p-1 rounded-lg border border-[var(--border-color)]">
              <button
                onClick={() => setView("upload")}
                className={`flex items-center rounded-md px-4 py-2 text-xs font-semibold transition-all duration-200 ${view === "upload" ? "bg-white text-black shadow-sm" : "text-[var(--text-secondary)] hover:text-[var(--text-main)] hover:bg-[var(--bg-tertiary)]"}`}
              >
                <IoCloudUploadOutline className="mr-2 inline text-lg" /> Upload
              </button>
              <button
                onClick={() => {
                  fetchCandidates();
                  setView("leaderboard");
                }}
                className={`flex items-center rounded-md px-4 py-2 text-xs font-semibold transition-all duration-200 ${view === "leaderboard" ? "bg-white text-black shadow-sm" : "text-[var(--text-secondary)] hover:text-[var(--text-main)] hover:bg-[var(--bg-tertiary)]"}`}
              >
                <IoListOutline className="mr-2 inline text-lg" /> Rankings
              </button>
            </div>

            <button
              onClick={logout}
              className="group flex items-center gap-2 rounded-lg border border-red-900/30 bg-red-900/10 px-4 py-2 text-xs font-bold text-red-500 hover:bg-red-900/20 hover:text-red-400 transition-all"
            >
              <IoLogOutOutline size={18} className="group-hover:-translate-x-1 transition-transform" /> Logout
            </button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-12 relative z-10">

        {error && (
          <div className="mx-auto mb-8 max-w-4xl rounded-xl border border-red-500/50 bg-red-500/10 p-5 text-red-600 dark:text-red-200 shadow-lg animate-in fade-in slide-in-from-top-4 flex items-center gap-3 backdrop-blur-md">
            <div className="h-2 w-2 rounded-full bg-red-500 animate-pulse"></div>
            <span className="font-bold uppercase tracking-wider text-xs">System Error:</span> {error}
          </div>
        )}

        {view === "upload" ? (
          <UploadSection
            onUpload={uploadResumes}
            loading={loading}
            onComplete={() => {
              fetchCandidates();
              setView("leaderboard");
            }}
          />
        ) : (
          <LeaderboardSection
            candidates={candidates}
            onView={setSelectedCandidate}
            onInvite={(id, action) => inviteCandidate(id, action).then(msg => toast.success(msg)).catch(e => toast.error(e.message))}
            onClear={clearLeaderboard}
            onRefresh={fetchCandidates}
          />
        )}

      </main>

      {/* Modal */}
      {selectedCandidate && (
        <CandidateModal
          candidate={selectedCandidate}
          onClose={() => setSelectedCandidate(null)}
        />
      )}

    </div>
  );
}
