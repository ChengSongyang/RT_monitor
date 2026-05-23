import Link from "next/link";
import ReactMarkdown from "react-markdown";

interface ReportPageProps {
  params: Promise<{ year: string; month: string; source: string; id: string }>;
}

async function getReport(id: string) {
  try {
    const res = await fetch(
      `${process.env.API_BASE_URL || "http://localhost:8001"}/api/reports/${id}`,
      {
        cache: "no-store",
      }
    );
    if (res.ok) {
      const data = await res.json();
      return data.md_content || "";
    }
  } catch {}
  return "";
}

export default async function ReportPage({ params }: ReportPageProps) {
  const { id } = await params;
  const content = await getReport(id);

  return (
    <div className="min-h-screen bg-[var(--background)]">
      <div className="mx-auto max-w-[800px] px-6 py-8">
        <Link
          href="/"
          className="text-sm text-[var(--muted-foreground)] hover:text-[var(--accent)] mb-6 inline-block"
        >
          ← 返回精选
        </Link>
        {content ? (
          <article className="prose prose-invert max-w-none">
            <ReactMarkdown>{content}</ReactMarkdown>
          </article>
        ) : (
          <div className="text-center py-16 text-[var(--muted-foreground)]">
            <p>暂无解读报告</p>
          </div>
        )}
      </div>
    </div>
  );
}
