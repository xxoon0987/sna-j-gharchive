-- GH Archive events mirrored in ClickHouse's public github.github_events table.
-- Window parameters are filled by fetch_events.py; the four windows cover
-- 2025-01-01 00:00:00 to 2025-02-01 00:00:00 UTC, end exclusive.
-- Project boundary: ten Hugging Face AI/data-science repositories.
-- Numeric repo IDs are stable even if a repository is renamed.
SELECT
  repo_id,
  repo_name,
  toString(event_type) AS event_type,
  actor_login,
  creator_user_login,
  toString(action) AS action,
  toString(review_state) AS review_state,
  formatDateTime(created_at, '%Y-%m-%dT%H:%i:%sZ', 'UTC') AS event_time_utc,
  number
FROM github.github_events
WHERE repo_id IN (
  '155220641',  -- transformers
  '250213286',  -- datasets
  '219035799',  -- tokenizers
  '308638334',  -- accelerate
  '498011141',  -- diffusers
  '570384908',  -- peft
  '250510075',  -- trl
  '323591830',  -- huggingface_hub
  '898968194',  -- smolagents
  '547806116'   -- text-generation-inference
)
AND created_at >= toDateTime('{{START}}', 'UTC')
AND created_at < toDateTime('{{END}}', 'UTC')
AND event_type IN (
  'IssuesEvent',
  'IssueCommentEvent',
  'PullRequestEvent',
  'PullRequestReviewEvent',
  'PullRequestReviewCommentEvent'
)
ORDER BY created_at, repo_id
FORMAT JSONEachRow
