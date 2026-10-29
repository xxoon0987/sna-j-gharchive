"""Build the reproducible SNA summary consumed by the presentation site.

Run after fetch_events.py. The raw public event extract stays out of Git; this
script publishes aggregate network data and a small illustrative actor subset.
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from itertools import combinations
from pathlib import Path

import networkx as nx


REPOS = [
    ("huggingface/transformers", "Transformers"),
    ("huggingface/datasets", "Datasets"),
    ("huggingface/tokenizers", "Tokenizers"),
    ("huggingface/accelerate", "Accelerate"),
    ("huggingface/diffusers", "Diffusers"),
    ("huggingface/peft", "PEFT"),
    ("huggingface/trl", "TRL"),
    ("huggingface/huggingface_hub", "Hub"),
    ("huggingface/smolagents", "Smolagents"),
    ("huggingface/text-generation-inference", "TGI"),
]
REPO_INDEX = {name: index for index, (name, _) in enumerate(REPOS)}
TYPE_LAYER = {
    "IssuesEvent": "issues",
    "IssueCommentEvent": "discussion",
    "PullRequestEvent": "pulls",
    "PullRequestReviewEvent": "reviews",
    "PullRequestReviewCommentEvent": "reviews",
}
LAYERS = ["all", "issues", "discussion", "pulls", "reviews"]
WEEK_STARTS = ["2025-01-01", "2025-01-08", "2025-01-15", "2025-01-22"]


def is_bot(name: str) -> bool:
    return name.lower().endswith("[bot]") or name == "HuggingFaceDocBuilderDev"


def jaccard(left: set[str], right: set[str]) -> float:
    union = left | right
    return round(len(left & right) / len(union), 3) if union else 0.0


def make_view(
    key: str,
    actors_repos: dict[str, dict[str, Counter[str]]],
    actor_events: dict[str, Counter[str]],
) -> dict:
    per_actor = actors_repos[key]
    repo_actors = {name: set() for name, _ in REPOS}
    for actor, repo_counts in per_actor.items():
        for repo in repo_counts:
            repo_actors[repo].add(actor)

    core = nx.Graph()
    for repo, _ in REPOS:
        core.add_node(f"repo:{repo}")
    multi = {actor: repos for actor, repos in per_actor.items() if len(repos) >= 2}
    for actor, repos in multi.items():
        core.add_node(f"actor:{actor}")
        for repo in repos:
            core.add_edge(f"actor:{actor}", f"repo:{repo}")
    between = nx.betweenness_centrality(core, normalized=True)

    edges = []
    for first, second in combinations((name for name, _ in REPOS), 2):
        shared = repo_actors[first] & repo_actors[second]
        if shared:
            edges.append({"source": first, "target": second, "shared": len(shared)})
    edges.sort(key=lambda edge: (-edge["shared"], edge["source"], edge["target"]))

    selected = sorted(
        multi,
        key=lambda actor: (
            -between.get(f"actor:{actor}", 0),
            -len(multi[actor]),
            -sum(multi[actor].values()),
            actor.lower(),
        ),
    )[:40]
    sample_actors = [
        {
            "id": actor,
            "repos": [repo for repo, _ in REPOS if repo in multi[actor]],
            "events": sum(multi[actor].values()),
            "betweenness": round(between.get(f"actor:{actor}", 0), 5),
            "roles": {layer: actor_events[actor].get(layer, 0) for layer in LAYERS[1:]},
        }
        for actor in selected
    ]
    result = {
        "events": sum(sum(counts.values()) for counts in per_actor.values()),
        "actors": len(per_actor),
        "multiRepoActors": len(multi),
        "repoActors": {repo: len(people) for repo, people in repo_actors.items()},
        "edges": edges,
        "sampleActors": sample_actors,
        "maxBetweenness": round(max((between.get(f"actor:{a}", 0) for a in multi), default=0), 5),
    }
    if key == "all":
        # Compare centralities on the same connected, undirected, binary
        # bipartite core. Single-repository actors are excluded consistently.
        if not nx.is_connected(core):
            raise ValueError("The all-events cross-repository core is disconnected")
        closeness = nx.closeness_centrality(core)
        eigen_raw = nx.eigenvector_centrality(core, max_iter=1000, tol=1e-10)
        eigen_max = max(eigen_raw[f"actor:{actor}"] for actor in multi)
        scores = {
            actor: {
                "degree": len(repos),
                "closeness": round(closeness[f"actor:{actor}"], 5),
                "betweenness": round(between[f"actor:{actor}"], 5),
                # Rescale within the actor class for a readable 0–1 value.
                "eigenvector": round(eigen_raw[f"actor:{actor}"] / eigen_max, 5),
            }
            for actor, repos in multi.items()
        }
        metrics = ("degree", "closeness", "betweenness", "eigenvector")
        rankings = {
            metric: [
                {"actor": actor, "score": scores[actor][metric]}
                for actor in sorted(scores, key=lambda name: (-scores[name][metric], name.lower()))[:5]
            ]
            for metric in metrics
        }
        for item in sample_actors:
            item["centrality"] = scores[item["id"]]
        result["centrality"] = {
            "coreActors": len(multi),
            "coreRepos": len(REPOS),
            "coreEdges": core.number_of_edges(),
            "connected": True,
            "scores": scores,
            "rankings": rankings,
        }
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=Path("data/raw-events.jsonl"))
    parser.add_argument("--output", type=Path, default=Path("docs/data.json"))
    parser.add_argument("--centrality-csv", type=Path, default=Path("docs/repro/centrality-scores.csv"))
    args = parser.parse_args()

    raw_events = [json.loads(line) for line in args.input.read_text(encoding="utf-8").splitlines()]
    actors_repos = {key: defaultdict(Counter) for key in LAYERS}
    actor_events = defaultdict(Counter)
    repo_events = defaultdict(Counter)
    week_events = {start: Counter() for start in WEEK_STARTS}
    type_counts = Counter()
    bot_rows = 0
    review_pairs = Counter()
    review_actors = set()
    review_authors = set()

    for event in raw_events:
        actor = event["actor_login"]
        repo = event["repo_name"]
        kind = event["event_type"]
        layer = TYPE_LAYER[kind]
        if repo not in REPO_INDEX:
            raise ValueError(f"Unexpected repository: {repo}")
        if not actor or is_bot(actor):
            bot_rows += 1
            continue

        type_counts[kind] += 1
        for view in ("all", layer):
            actors_repos[view][actor][repo] += 1
        actor_events[actor][layer] += 1
        repo_events[repo][layer] += 1
        day = event["event_time_utc"][:10]
        week = max(start for start in WEEK_STARTS if start <= day)
        week_events[week][layer] += 1

        # In this flattened table, creator_user_login is the comment author's
        # login for comment events. Only PullRequestReviewEvent reliably names
        # the PR creator, so directed person-to-person edges use that type.
        if kind == "PullRequestReviewEvent":
            author = event["creator_user_login"]
            if author and author != actor and not is_bot(author):
                review_pairs[(actor, author)] += 1
                review_actors.add(actor)
                review_authors.add(author)

    views = {key: make_view(key, actors_repos, actor_events) for key in LAYERS}
    role_sets = {key: set(actors_repos[key]) for key in LAYERS[1:]}
    bridge_sets = {
        key: {actor for actor, repos in actors_repos[key].items() if len(repos) >= 2}
        for key in LAYERS[1:]
    }
    community = role_sets["issues"] | role_sets["discussion"]
    code = role_sets["pulls"] | role_sets["reviews"]
    cross_role = community & code
    cross_role_bridges = {
        actor for actor in cross_role if len(actors_repos["all"].get(actor, {})) >= 2
    }

    output = {
        "metadata": {
            "title": "開源協作地圖｜第 J 組 SNA 報告",
            "period": "2025-01-01 — 2025-01-31 (UTC)",
            "periodStart": "2025-01-01T00:00:00Z",
            "periodEndExclusive": "2025-02-01T00:00:00Z",
            "generatedAt": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "rawRows": len(raw_events),
            "humanRows": len(raw_events) - bot_rows,
            "excludedBotRows": bot_rows,
            "repoCount": len(REPOS),
            "source": "GH Archive, accessed via ClickHouse public github.github_events mirror",
            "sourceUrl": "https://www.gharchive.org/",
            "queryUrl": "https://sql.clickhouse.com/",
            "githubEventDocs": "https://docs.github.com/en/rest/using-the-rest-api/github-event-types",
        },
        "repositories": [
            {
                "id": name,
                "label": label,
                "url": f"https://github.com/{name}",
                "events": sum(repo_events[name].values()),
                "roles": {role: repo_events[name][role] for role in LAYERS[1:]},
            }
            for name, label in REPOS
        ],
        "views": views,
        "typeCounts": dict(type_counts),
        "overlap": {
            "actorJaccard": {
                f"{a}-{b}": jaccard(role_sets[a], role_sets[b])
                for a, b in combinations(("issues", "pulls", "reviews"), 2)
            },
            "actorOverlapCounts": {
                f"{a}-{b}": {
                    "intersection": len(role_sets[a] & role_sets[b]),
                    "union": len(role_sets[a] | role_sets[b]),
                }
                for a, b in combinations(("issues", "pulls", "reviews"), 2)
            },
            "bridgeJaccard": {
                f"{a}-{b}": jaccard(bridge_sets[a], bridge_sets[b])
                for a, b in combinations(("issues", "pulls", "reviews"), 2)
            },
            "communityActors": len(community),
            "codeActors": len(code),
            "crossRoleActors": len(cross_role),
            "crossRoleBridgeActors": len(cross_role_bridges),
        },
        "reviewNetwork": {
            "directedEvents": sum(review_pairs.values()),
            "reviewerAuthorPairs": len(review_pairs),
            "reviewers": len(review_actors),
            "authors": len(review_authors),
            "topPairs": [
                {"reviewer": actor, "author": author, "events": count}
                for (actor, author), count in review_pairs.most_common(12)
            ],
        },
        "weeks": [
            {
                "start": start,
                "endExclusive": [*WEEK_STARTS[1:], "2025-02-01"][i],
                "roles": {role: week_events[start][role] for role in LAYERS[1:]},
            }
            for i, start in enumerate(WEEK_STARTS)
        ],
        "definitions": {
            "unit": "一列鏡像回傳的公開 GitHub 事件紀錄；同一帳號可產生多列",
            "node": "GitHub 帳號與儲存庫，建立二模參與網絡",
            "edge": "帳號在指定期間於儲存庫產生至少一筆指定類型事件；圖上使用二元邊，事件數另行顯示",
            "bridge": "於兩個以上選定儲存庫留下事件的帳號；圖示依二模核心（跨庫帳號＋儲存庫）的標準化中介中心度挑選前 40 位",
            "centrality": "全部事件層的二模核心為無向、無權重、二元圖；以同一張 93 帳號＋10 儲存庫網絡比較 degree、closeness、betweenness、eigenvector。特徵向量分數在帳號類內以最高分縮放為 1。",
            "issues": "IssuesEvent；議題開啟、關閉與重新開啟",
            "discussion": "IssueCommentEvent；包含 issue 與 PR 討論留言，不能全當成 issue 留言",
            "pulls": "PullRequestEvent；PR 開啟、關閉與重新開啟",
            "reviews": "PullRequestReviewEvent 與 PullRequestReviewCommentEvent；審查與程式碼審查留言",
            "directedReview": "僅用 PullRequestReviewEvent 建立審查者 → PR 作者的有向關係，排除自己審查自己",
            "botFilter": "排除名稱以 [bot] 結尾的帳號，以及經 Hugging Face doc-builder 專案文件確認的 HuggingFaceDocBuilderDev 自動化帳號；其他自動化帳號可能仍在資料內",
            "limitations": [
                "公開事件反映平台上可見的動作，不能代表全部溝通、工作量或能力。",
                "十個儲存庫依同一生態系與資料活動量目的性選取，非隨機樣本；一個月份的結果不能推論整個 GitHub。",
                "IssueCommentEvent 同時包含 issue 與 PR 留言；ClickHouse 的扁平欄位不足以拆開兩者。",
                "已排除可辨識的自動化帳號，但其他自動化動作可能仍在資料內。",
                "中介中心度描述這個界定網絡中的路徑位置，不能當成開發者價值排名。",
                "特徵向量中心度偏向連到結構上較中心的儲存庫；其分數與其他中心度不可混成單一人物排名。",
            ],
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    args.centrality_csv.parent.mkdir(parents=True, exist_ok=True)
    with args.centrality_csv.open("w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(("actor_login", "repo_degree", "closeness", "betweenness", "eigenvector_actor_max_1"))
        for actor, scores in sorted(views["all"]["centrality"]["scores"].items()):
            writer.writerow((actor, scores["degree"], scores["closeness"], scores["betweenness"], scores["eigenvector"]))
    print(
        f"Raw rows: {len(raw_events)} | human rows: {output['metadata']['humanRows']} "
        f"| actors: {views['all']['actors']} | cross-repo: {views['all']['multiRepoActors']}"
    )
    print("Role overlap:", output["overlap"])
    print("Saved", args.output)
    print("Saved", args.centrality_csv)


if __name__ == "__main__":
    main()
