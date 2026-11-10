#!/usr/bin/env bash
# Fetches the logos that are not committed to the repo.
#
#   ./tools/fetch-logos.sh      (run from anywhere; it finds public/ itself)
#
# Most marks are committed. Two are not: TennMesh's and GCARC's are served from
# their own sites, and the sandbox this site is built in cannot reach either
# domain, so they have to be fetched from a machine that can.
#
# Nothing here is load-bearing. Every card falls back to the live URL on the
# owner's site, and then to nothing at all, so the page renders correctly
# whether or not this script has been run. Running it just means the logos are
# served from our own origin instead of theirs.
#
# Moved out of public/ for Rev 2.1 -- a shell script has no business being
# served as a static asset.

set -u
cd "$(dirname "$0")/../public/images" || exit 1

fetch() {
  local out="$1" url="$2"
  local code
  code=$(curl -sSL -o "$out.tmp" -w '%{http_code}' "$url" || echo 000)
  if [ "$code" = "200" ] && [ -s "$out.tmp" ]; then
    mv "$out.tmp" "$out"
    printf '  ok    %-16s %s\n' "$out" "$(du -h "$out" | cut -f1)"
  else
    rm -f "$out.tmp"
    printf '  FAIL  %-16s HTTP %s — %s\n' "$out" "$code" "$url"
  fi
}

fetch neighbors/tennmesh.png "https://tennmesh.com/assets/images/tennmesh-primary-dark-even.png"
fetch clubs/gcarc.png      "https://www.collegedalehams.org/wp-content/uploads/2024/02/GCARC_Logo.png"

echo
echo "Already committed, nothing to fetch: neighbors/mtnmesh.svg,"
echo "neighbors/nashmesh.png, neighbors/ncmesh.png, neighbors/ucmesh.svg,"
echo "clubs/w4gta.png, clubs/w4am.png, clubs/ka4j.png."
