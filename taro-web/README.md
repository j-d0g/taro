# taro-web

Frontend for Taro.ai. Not yet implemented.

## Plan

- Chat UI that talks to `taro-api` at `POST /chat`
- Show which tools the agent used per response
- Multi-turn conversations (pass `thread_id` back)

## Getting Started

TBD — likely Next.js or a simple HTML/JS page.

For now, use LangGraph Studio or curl to interact with the agent:

```bash
cd ../taro-api && make studio
```
