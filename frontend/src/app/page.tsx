import Link from 'next/link'

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-between p-8 md:p-24">
      <div className="z-10 max-w-5xl w-full items-center justify-between text-sm flex">
        <p className="fixed left-0 top-0 flex w-full justify-center border-b border-gray-300 bg-gradient-to-b from-zinc-200 p-4 backdrop-blur-2xl dark:border-neutral-800 dark:bg-zinc-800/30 dark:from-inherit lg:static lg:w-auto lg:rounded-xl lg:border lg:bg-gray-200 lg:p-4 lg:dark:bg-zinc-800/30">
          AI Hiring SaaS Platform&nbsp;
          <code className="font-mono font-bold">Production Multi-Tenant Engine</code>
        </p>
      </div>

      <div className="relative flex place-items-center flex-col my-12 text-center">
        <h1 className="text-4xl md:text-6xl font-extrabold tracking-tight text-slate-900 mb-4">
          Enterprise AI Recruitment SaaS
        </h1>
        <p className="text-lg md:text-xl text-slate-600 max-w-2xl">
          Explainable, evidence-backed candidate matching, automated verification, and end-to-end recruitment workflow orchestration.
        </p>
      </div>

      <div className="mb-32 grid text-center lg:max-w-5xl lg:w-full lg:grid-cols-3 lg:text-left gap-6">
        <Link
          href="/recruiter/dashboard"
          className="group rounded-xl border border-slate-200 p-6 transition-all hover:border-brand-500 hover:bg-brand-50/50 shadow-sm"
        >
          <h2 className="mb-3 text-2xl font-semibold">
            Recruiter Portal{' '}
            <span className="inline-block transition-transform group-hover:translate-x-1 motion-reduce:transform-none">
              -&gt;
            </span>
          </h2>
          <p className="m-0 max-w-[30ch] text-sm opacity-75 text-slate-600">
            Create jobs, review AI candidate match evidence, manage pipelines, and schedule interviews.
          </p>
        </Link>

        <Link
          href="/candidate/dashboard"
          className="group rounded-xl border border-slate-200 p-6 transition-all hover:border-brand-500 hover:bg-brand-50/50 shadow-sm"
        >
          <h2 className="mb-3 text-2xl font-semibold">
            Candidate Portal{' '}
            <span className="inline-block transition-transform group-hover:translate-x-1 motion-reduce:transform-none">
              -&gt;
            </span>
          </h2>
          <p className="m-0 max-w-[30ch] text-sm opacity-75 text-slate-600">
            Manage reusable profile, upload resume, apply to jobs, track applications and assessments.
          </p>
        </Link>

        <Link
          href="/admin/dashboard"
          className="group rounded-xl border border-slate-200 p-6 transition-all hover:border-brand-500 hover:bg-brand-50/50 shadow-sm"
        >
          <h2 className="mb-3 text-2xl font-semibold">
            Platform Admin{' '}
            <span className="inline-block transition-transform group-hover:translate-x-1 motion-reduce:transform-none">
              -&gt;
            </span>
          </h2>
          <p className="m-0 max-w-[30ch] text-sm opacity-75 text-slate-600">
            Verify recruiters and jobs, monitor AI Gateway costs, token metrics, and platform security.
          </p>
        </Link>
      </div>
    </main>
  )
}
