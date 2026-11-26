"""Render statistics from GitHub into a standalone, accessible SVG."""
import json
import subprocess
from html import escape
from pathlib import Path

OWNER = "kauebrpe"


def api(*arguments):
    output = subprocess.check_output(["gh", "api", *arguments], text=True)
    return json.loads(output)


query = """
query($login: String!) {
  user(login: $login) {
    contributionsCollection {
      totalCommitContributions
      totalPullRequestContributions
      contributionCalendar { totalContributions }
    }
  }
}
"""
response = api("graphql", "-f", "query=" + query, "-f", "login=" + OWNER)
stats = response["data"]["user"]["contributionsCollection"]
pages = api("--paginate", "--slurp", f"users/{OWNER}/repos?type=owner&per_page=100")
languages = {}
for page in pages:
    for repo in page:
        if repo["fork"] or repo["private"]:
            continue
        for name, size in api("repos/" + repo["full_name"] + "/languages").items():
            languages[name] = languages.get(name, 0) + size


def label(x, y, size, value, color="#E6EDF3"):
    return (f'<text x="{x}" y="{y}" font-size="{size}" fill="{color}">'
            f'{escape(str(value))}</text>')


rows = sorted(languages.items(), key=lambda pair: (-pair[1], pair[0]))[:4]
height = 130 + 26 * len(rows)
parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="460" height="{height}" '
         f'viewBox="0 0 460 {height}" font-family="system-ui,sans-serif">',
         '<title>Atividade no GitHub e linguagens dos repositórios públicos</title>',
         '<rect width="100%" height="100%" rx="12" fill="#0D1117"/>']
counts = [("Contribuições", stats["contributionCalendar"]["totalContributions"]),
          ("Commits", stats["totalCommitContributions"]),
          ("Pull requests", stats["totalPullRequestContributions"])]
for index, (name, number) in enumerate(counts):
    x = 18 + 148 * index
    parts.extend([label(x, 41, 27, number, "#7EE787"), label(x, 67, 15, name)])
parts.append(label(18, 108, 16, "Linguagens por volume de código"))
total = sum(languages.values())
for index, (name, size) in enumerate(rows):
    y = 134 + index * 26
    share = size / total
    parts.extend([label(18, y, 15, name),
                  f'<rect x="172" y="{y-9}" width="182" height="5" fill="#30363D"/>',
                  f'<rect x="172" y="{y-9}" width="{182*share:.2f}" height="5" fill="#39FF14"/>',
                  label(374, y, 15, f"{share:.1%}")])
parts.append("</svg>")
Path("dist").mkdir(exist_ok=True)
Path("dist/activity.svg").write_text("\n".join(parts) + "\n", encoding="utf-8")
