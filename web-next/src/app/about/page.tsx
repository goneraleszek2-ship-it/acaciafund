import Link from "next/link";

export default function AboutPage() {
  return (
    <div className="min-h-screen bg-[var(--bg)] text-[var(--text)] py-16 px-6">
      <h1 className="text-3xl font-bold tracking-tighter text-center text-white mb-8">
        About AcaciaFund
      </h1>
      <div className="max-w-4xl mx-auto">
        <p className="mb-6 text-[var(--muted)] leading-relaxed">
          AcaciaFund is a static-first research and learning platform that turns 
          Hacker News and arXiv into structured research syntheses with metadata, 
          manifests, and local-first learning experiences. Our mission is to 
          provide privacy-preserving, judgment-focused educational content that 
          helps individuals improve their decision-making under uncertainty.
        </p>
        <p className="mb-6 text-[var(--muted)] leading-relaxed">
          The platform combines automated content synthesis with interactive 
          learning components, including quizzes and explanatory lessons, to 
          create an engaging ecosystem for continuous learning. All content is 
          available for offline reading and local-first interaction, ensuring 
          privacy and data sovereignty.
        </p>
        <div className="flex flex-wrap gap-4 justify-center">
          <Link href="/blog/" className="flex h-10 px-4 py-2 bg-[var(--accent)]/20 text-[var(--accent)] hover:bg-[var(--accent)]/30 rounded-lg transition-colors font-medium">
            Explore Research Syntheses
          </Link>
          <Link href="/learn/" className="flex h-10 px-4 py-2 bg-[var(--accent-2)]/20 text-[var(--accent-2)] hover:bg-[var(--accent-2)]/30 rounded-lg transition-colors font-medium">
            Start Learning
          </Link>
        </div>
      </div>
    </div>
  );
}