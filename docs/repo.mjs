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
