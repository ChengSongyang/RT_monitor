import { cn } from "@/lib/utils";

const variantStyles: Record<string, string> = {
  default: "bg-white/10 text-gray-300 border-white/10",
  paper: "bg-blue-500/20 text-blue-400 border-blue-500/30",
  industry_news: "bg-green-500/20 text-green-400 border-green-500/30",
  guideline: "bg-purple-500/20 text-purple-400 border-purple-500/30",
  research: "bg-orange-500/20 text-orange-400 border-orange-500/30",
  conference: "bg-pink-500/20 text-pink-400 border-pink-500/30",
  featured: "bg-amber-500/20 text-amber-400 border-amber-500/30",
  score: "bg-cyan-500/20 text-cyan-400 border-cyan-500/30",
};

interface BadgeProps {
  children: React.ReactNode;
  variant?: string;
  className?: string;
}

export function Badge({ children, variant = "default", className }: BadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded border px-1.5 py-0.5 text-[10px] font-medium",
        variantStyles[variant] || variantStyles.default,
        className
      )}
    >
      {children}
    </span>
  );
}
