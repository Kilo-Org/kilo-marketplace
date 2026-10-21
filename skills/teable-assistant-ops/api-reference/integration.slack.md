# Slack Integration

Send messages and notifications to Slack from automation scripts.

## Setup
1. Check status: `teable integration list`
2. Not connected / invalid → call the `connect_integration` tool
3. Connected → fetch tokens: `teable integration get-token`

## Two Types of Tokens

Slack integration provides TWO tokens for different purposes:

```javascript
// BOT token (xoxb-...) - for sending messages, posting to channels
const botToken = input.integrations["<id>"].authConfig.accessToken;

// USER token (xoxp-...) - for listing channels, reading user info
const userToken = input.integrations["<id>"].authConfig.authedUser.access_token;
```

**When to use which:**
- Send messages → BOT token (has chat:write scope)
- List channels → USER token (has channels:read scope)
- Get user info → USER token (has users:read scope)

## Send Message
```javascript
const response = await fetch('https://slack.com/api/chat.postMessage', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${slackToken}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    channel: '#general', // or channel ID like C1234567890
    text: 'Hello from Teable!'
  })
});
const result = await response.json();
if (!result.ok) throw new Error(result.error);
```

## Rich Message with Blocks
```javascript
await fetch('https://slack.com/api/chat.postMessage', {
  method: 'POST',
  headers: { 'Authorization': `Bearer ${slackToken}`, 'Content-Type': 'application/json' },
  body: JSON.stringify({
    channel: '#notifications',
    text: 'New record created', // fallback
    blocks: [
      { type: 'header', text: { type: 'plain_text', text: '📋 New Record' } },
      { type: 'section', fields: [
        { type: 'mrkdwn', text: `*Name:*\n${record.fields.Name}` },
        { type: 'mrkdwn', text: `*Status:*\n${record.fields.Status}` }
      ]},
      { type: 'actions', elements: [
        { type: 'button', text: { type: 'plain_text', text: 'View' }, url: recordUrl }
      ]}
    ]
  })
});
```

## List Channels (user token)
```javascript
const res = await fetch('https://slack.com/api/conversations.list?types=public_channel,private_channel', {
  headers: { 'Authorization': `Bearer ${userToken}` }
});
const { channels } = await res.json();
```

## Common Errors
- `channel_not_found`: Invalid channel ID
- `not_in_channel`: Bot not added to channel  
- `invalid_auth`: Token expired, user needs to reconnect

## Use Cases
- Record notifications
- Daily reports (scheduled trigger)
- Approval workflows with buttons
- Status change alerts

Block Kit reference: https://api.slack.com/block-kit
