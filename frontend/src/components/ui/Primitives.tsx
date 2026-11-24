import React from "react";
import { clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: (string | undefined | false | null)[]) {
  return twMerge(clsx(inputs));
}

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "outline" | "ghost" | "danger" | "success";
  size?: "sm" | "md" | "lg";
}

export function Button({ variant = "primary", size = "md", className, ...props }: ButtonProps) {
  const variants = {
    primary: "bg-[#1F6AA5] text-white hover:bg-[#154B75] shadow-sm disabled:opacity-50",
    secondary: "bg-slate-900 text-white hover:bg-slate-800 shadow-sm disabled:opacity-50",
    outline: "bg-white text-slate-700 border border-slate-200 hover:bg-slate-50 hover:border-slate-300 disabled:opacity-50",
    ghost: "bg-transparent text-slate-600 hover:bg-slate-100 hover:text-slate-900 disabled:opacity-50",
    danger: "bg-rose-600 text-white hover:bg-rose-700 shadow-sm disabled:opacity-50",
    success: "bg-emerald-700 text-white hover:bg-emerald-800 shadow-sm disabled:opacity-50",
  };
  const sizes = {
    sm: "h-9 px-3 text-xs rounded-lg gap-1.5",
    md: "h-10 px-4 text-sm rounded-xl gap-2",
    lg: "h-11 px-5 text-sm rounded-xl gap-2",
  };
  return (
    <button
      className={cn(
        "inline-flex items-center justify-center font-semibold transition-all duration-150 focus:outline-none focus:ring-2 focus:ring-[#1F6AA5]/40 active:scale-[0.99] cursor-pointer",
        variants[variant],
        sizes[size],
        className
      )}
      {...props}
    />
  );
}

export function Card({ className, children }: { className?: string; children: React.ReactNode }) {
  return (
    <div className={cn("bg-white border border-slate-200/90 rounded-2xl shadow-[0_1px_3px_rgba(15,23,42,0.04)]", className)}>
      {children}
    </div>
  );
}

/**
 * Badges con contraste WCAG AA verificado (nunca texto blanco sobre turquesa claro).
 */
export function Badge({
  variant = "neutral",
  className,
  children,
}: {
  variant?: "blue" | "cyan" | "green" | "amber" | "red" | "purple" | "neutral";
  className?: string;
  children: React.ReactNode;
}) {
  const map = {
    blue: "bg-sky-50 text-[#154B75] border-sky-200",
    cyan: "bg-cyan-50 text-[#0E4A56] border-cyan-200",
    green: "bg-emerald-50 text-emerald-800 border-emerald-200",
    amber: "bg-amber-50 text-amber-800 border-amber-200",
    red: "bg-rose-50 text-rose-800 border-rose-200",
    purple: "bg-violet-50 text-violet-800 border-violet-200",
    neutral: "bg-slate-100 text-slate-700 border-slate-200",
  };
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 px-2.5 py-0.5 text-xs font-semibold rounded-full border whitespace-nowrap",
        map[variant],
        className
      )}
    >
      {children}
    </span>
  );
}

export function Field({
  label,
  hint,
  children,
}: {
  label: string;
  hint?: string;
  children: React.ReactNode;
}) {
  return (
    <div className="space-y-1.5">
      <label className="block text-xs font-bold uppercase tracking-wide text-slate-700">{label}</label>
      {children}
      {hint && <p className="text-xs text-slate-500">{hint}</p>}
    </div>
  );
}

export function Input({ className, ...props }: React.InputHTMLAttributes<HTMLInputElement>) {
  return (
    <input
      className={cn(
        "w-full h-10 px-3.5 rounded-xl bg-white border border-slate-200 text-sm text-slate-900 placeholder:text-slate-400 focus:outline-none focus:border-[#1F6AA5] focus:ring-2 focus:ring-[#1F6AA5]/20 transition",
        className
      )}
      {...props}
    />
  );
}

export function Select({ className, ...props }: React.SelectHTMLAttributes<HTMLSelectElement>) {
  return (
    <select
      className={cn(
        "w-full h-10 px-3.5 rounded-xl bg-white border border-slate-200 text-sm text-slate-900 focus:outline-none focus:border-[#1F6AA5] focus:ring-2 focus:ring-[#1F6AA5]/20 transition",
        className
      )}
      {...props}
    />
  );
}

export function StatCard({
  label,
  value,
  sub,
  icon,
  accent = "blue",
}: {
  label: string;
  value: string | number;
  sub?: string;
  icon: React.ReactNode;
  accent?: "blue" | "cyan" | "green" | "amber" | "purple";
}) {
  const topBar = {
    blue: "bg-[#1F6AA5]",
    cyan: "bg-[#36B5C6]",
    green: "bg-emerald-600",
    amber: "bg-amber-500",
    purple: "bg-[#3B1C7A]",
  };
  const iconBg = {
    blue: "bg-sky-50 text-[#1F6AA5]",
    cyan: "bg-cyan-50 text-[#0E7490]",
    green: "bg-emerald-50 text-emerald-700",
    amber: "bg-amber-50 text-amber-700",
    purple: "bg-violet-50 text-[#3B1C7A]",
  };
  return (
    <Card className="relative overflow-hidden p-4">
      <div className={cn("absolute inset-x-0 top-0 h-1", topBar[accent])} />
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0">
          <p className="text-[11px] font-bold uppercase tracking-wider text-slate-500 truncate">{label}</p>
          <p className="mt-1 text-2xl font-extrabold text-slate-900 font-display tracking-tight">{value}</p>
          {sub && <p className="mt-0.5 text-xs text-slate-500 truncate">{sub}</p>}
        </div>
        <div className={cn("p-2.5 rounded-xl shrink-0", iconBg[accent])}>{icon}</div>
      </div>
    </Card>
  );
}

export function StepHeader({
  step,
  title,
  subtitle,
  action,
}: {
  step: string;
  title: string;
  subtitle?: string;
  action?: React.ReactNode;
}) {
  return (
    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-slate-200/80">
      <div className="flex items-start sm:items-center gap-3">
        <span className="inline-flex items-center px-2.5 py-1 rounded-lg bg-[#1F6AA5] text-white text-[11px] font-bold uppercase tracking-wider shrink-0">
          {step}
        </span>
        <div>
          <h2 className="text-base sm:text-lg font-bold text-slate-900 leading-tight">{title}</h2>
          {subtitle && <p className="text-xs sm:text-sm text-slate-500 mt-0.5">{subtitle}</p>}
        </div>
      </div>
      {action && <div className="shrink-0">{action}</div>}
    </div>
  );
}
