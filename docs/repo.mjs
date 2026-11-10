// Where the page fetches repository files from. Served from
// <owner>.github.io/<repo>/, files come from that repository, so a fork's
// page uses the fork's files; anywhere else, from DEFAULT_REPO.
import {DEFAULT_REPO, RELEASE_REF} from "./install-data.mjs";

export function repoFromLocation(loc) {
  const host = loc.hostname.toLowerCase();
  if (!host.endsWith(".github.io")) return DEFAULT_REPO;
  const owner = host.slice(0, -".github.io".length);
  const first = loc.pathname.split("/").filter(Boolean)[0];
  return owner + "/" + (first || owner + ".github.io");
}

// A file at RELEASE_REF of the repository, as raw.githubusercontent.com
// serves it (with CORS and byte ranges).
export function rawUrl(repo, filePath) {
  return "https://raw.githubusercontent.com/" + repo + "/" + RELEASE_REF + "/" + filePath;
}

// A page on GitHub for a path in the repository: a folder (no extension, or a
// trailing slash) opens as a tree, which renders its README; a file opens as
// a blob. An empty path is the repository itself.
export function githubUrl(repo, filePath = "") {
  const clean = filePath.replace(/^\/+|\/+$/g, "");
  if (!clean) return "https://github.com/" + repo;
  const last = clean.split("/").pop();
  const kind = filePath.endsWith("/") || !/\.[a-z0-9]+$/i.test(last) ? "tree" : "blob";
  return "https://github.com/" + repo + "/" + kind + "/" + RELEASE_REF + "/" + clean;
}

// Point every [data-repo-path] link at this site's repository and ref, so a
// fork's page links to the fork's files, as its installer and simulator fetch
// them. The static href stays as the fallback without scripts.
export function linkRepoPaths(root = document, repo = repoFromLocation(window.location)) {
  for (const a of root.querySelectorAll("a[data-repo-path]"))
    a.href = githubUrl(repo, a.dataset.repoPath);
}
