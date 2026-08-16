"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

export default function CandidateLoginPage() {
  const router = useRouter();

  useEffect(() => {
    router.replace("/login?portal=candidate");
  }, [router]);

  return (
    <div className="min-h-screen bg-slate-950 flex items-center justify-center text-white">
      <p className="text-sm font-mono text-slate-400">Redirecting to Candidate Portal Login...</p>
    </div>
  );
}
