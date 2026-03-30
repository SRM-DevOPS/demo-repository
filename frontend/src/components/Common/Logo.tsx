import { Link } from "@tanstack/react-router"

import { cn } from "@/lib/utils"

interface LogoProps {
  variant?: "full" | "icon" | "responsive"
  className?: string
  asLink?: boolean
}

export function Logo({
  variant = "full",
  className,
  asLink = true,
}: LogoProps) {
  const srmLogoUrl = "https://www.srmtech.com/wp-content/uploads/2021/05/logo.png"

  const content =
    variant === "responsive" ? (
      <>
        <img
          src={srmLogoUrl}
          alt="SRM Technologies"
          className={cn(
            "h-8 w-auto group-data-[collapsible=icon]:hidden",
            className,
          )}
        />
        <img
          src={srmLogoUrl}
          alt="SRM Technologies"
          className={cn(
            "size-6 hidden group-data-[collapsible=icon]:block",
            className,
          )}
        />
      </>
    ) : (
      <img
        src={srmLogoUrl}
        alt="SRM Technologies"
        className={cn(variant === "full" ? "h-8 w-auto" : "size-6", className)}
      />
    )

  if (!asLink) {
    return content
  }

  return <Link to="/">{content}</Link>
}
