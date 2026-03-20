"use client";

import * as React from "react";
import { cn } from "@/lib/utils";

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "default" | "destructive" | "outline" | "secondary" | "ghost" | "link";
  size?: "default" | "sm" | "lg" | "icon";
  asChild?: boolean;
}

const variantClasses: Record<string, string> = {
  default: "bg-primary text-primary-content hover:bg-primary/85 shadow-sm",
  destructive: "bg-error text-error-content hover:bg-error/85 shadow-sm",
  outline: "border border-base-300 bg-transparent hover:bg-base-200 text-base-content",
  secondary: "bg-base-200 text-base-content hover:bg-base-300",
  ghost: "bg-transparent hover:bg-base-200 text-base-content",
  link: "bg-transparent text-primary underline-offset-4 hover:underline",
};

const sizeClasses: Record<string, string> = {
  default: "h-10 px-5 py-2",
  sm: "h-8 px-4 text-xs",
  lg: "h-11 px-8",
  icon: "h-9 w-9",
};

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = "default", size = "default", ...props }, ref) => {
    return (
      <button
        ref={ref}
        className={cn(
          "inline-flex items-center justify-center whitespace-nowrap rounded-full text-sm font-medium transition-all duration-150 active:scale-[0.97] disabled:pointer-events-none disabled:opacity-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/40",
          variantClasses[variant],
          sizeClasses[size],
          className,
        )}
        {...props}
      />
    );
  }
);
Button.displayName = "Button";

export { Button };
