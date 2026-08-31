// Schema for proof-of-progress stats.json, computed daily by the
// scheduled agent. Keep this file in sync with scripts/compute-stats.py
// in the proof-of-progress repo.

export interface ProgressStats {
  generated_at: string // ISO timestamp
  window: {
    start: string // YYYY-MM-DD
    end: string // YYYY-MM-DD
    days: number
  }
  totals: {
    commits: number
    prs_merged: number
    prs_opened: number
    contributors: number
    releases: number
    repos_active: number
  }
  repos: RepoStats[]
  top_contributors: ContributorStats[]
  recent_releases: ReleaseEntry[]
  daily_commits: number[] // length = window.days, oldest-first
}

export interface RepoStats {
  name: string
  full_name: string
  url: string
  description: string
  stars: number
  open_issues: number
  open_prs: number
  default_branch: string
  commits_28d: number
  commits_7d: number
  prs_merged_28d: number
  contributors_28d: number
  last_commit_at: string | null
  last_commit_message: string | null
  weekly_commits: number[] // last 12 weeks, oldest-first
}

export interface ContributorStats {
  login: string
  avatar_url: string
  html_url: string
  commits_28d: number
  prs_merged_28d: number
  repos_touched: number
  highlighted: boolean
}

export interface ReleaseEntry {
  repo: string
  tag: string
  name: string
  published_at: string
  url: string
  is_prerelease: boolean
}
