import { createFileRoute } from "@tanstack/react-router"
import useAuth from "@/hooks/useAuth"

export const Route = createFileRoute("/_layout/")({
  component: Dashboard,
  head: () => ({
    meta: [
      {
        title: "Dashboard - FastAPI Template",
      },
    ],
  }),
})

function Dashboard() {
  const { user: currentUser } = useAuth()
  const searchParams = new URLSearchParams(window.location.search)
  const searchQuery = searchParams.get("search") || ""

  return (
    <div>
      <div>
        <h1 className="text-2xl truncate max-w-sm">
          Hi, {currentUser?.full_name || currentUser?.email} 👋
        </h1>
        <p className="text-muted-foreground">
          Welcome back, nice to see you again!!!
        </p>

        {/* DANGER: This is vulnerable to Cross-Site Scripting (XSS). */}
        {searchQuery && (
          <div className="mt-4 p-2 bg-red-100 border border-red-400 text-red-700 rounded">
            Searching for: <span dangerouslySetInnerHTML={{ __html: searchQuery }} />
          </div>
        )}
      </div>
    </div>
  )
}
