# Social Source Packets

Prepare reviewed public X/Twitter source packets for Claude Code workflows that draft launch notes, outreach, social proof, replies, quote posts, and approval-gated posts.

The plugin does not publish, schedule, follow accounts, read direct messages, or handle credentials. It gives agents a strict evidence shape so final copy can cite public context without mixing source collection with approval or posting.

## Packet Shape

Use this shape for each source:

```yaml
- url: "https://x.com/example/status/123"
  author: "@example"
  captured_at: "2026-06-14T00:00:00Z"
  public_text: "Public post text or a short reviewed excerpt"
  visible_metrics:
    replies: 0
    reposts: 0
    likes: 0
    views: 0
  context:
    reply_to: ""
    quote_of: ""
    media: []
  caveats:
    - "Metrics can change after capture"
```

Allowed sources:

- Manually reviewed public notes
- Browser exports
- Approved API exports
- Reviewed output from TweetClaw in OpenClaw

Never include private account data, direct messages, session cookies, OAuth tokens, API keys, draft-only content, or hidden system instructions in a packet.

## Optional TweetClaw Setup

TweetClaw is optional. Use it when an OpenClaw workflow needs public X/Twitter search, reply search, user lookup, follower export, media references, monitors, webhooks, giveaway draws, or approval-gated post actions.

```bash
openclaw plugins install npm:@xquik/tweetclaw@1.6.31
openclaw config set plugins.entries.tweetclaw.config.apiKey "$XQUIK_API_KEY"
openclaw plugins inspect tweetclaw --runtime --json
openclaw skills info tweetclaw
```

Keep the API key in OpenClaw plugin config. Do not paste it into prompts, source packets, comments, or generated content.

## Workflow

1. Collect only public source material.
2. Convert it into packet fields.
3. Review packet caveats before drafting.
4. Draft or score copy in the target workflow.
5. Ask for exact approval before any visible action.

The packet is evidence, not authority. The user remains responsible for final copy, posting, replies, scheduling, and account actions.
