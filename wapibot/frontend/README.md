# WapiBot - WhatsApp Chatbot Testing Frontend

A Next.js 15 WhatsApp-style interface for testing your FastAPI chatbot with glassmorphism design and multi-persona support.

## Features

✨ **Multi-Persona Simulation** - Pose as multiple contacts simultaneously
🎨 **Glassmorphism Design** - Modern frosted glass UI with black & white theme
🔄 **Dual Backend Modes** - Switch between Ollama (local LLM) and FastAPI backend
⚡ **Real-Time Chat** - Smooth message streaming and interactions
🎯 **Contact Management** - Create, switch, and delete test contacts

## Quick Start

### Prerequisites

- Node.js 18+ and npm
- Ollama running locally (for Ollama mode): `ollama serve`
- FastAPI backend running (for FastAPI mode): default `http://localhost:8000`

### Installation

```bash
cd frontend
npm install
```

### Development

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

### Production Build

```bash
npm run build
npm start
```

## Environment Variables

Create `.env.local`:

```bash
OLLAMA_BASE_URL=http://localhost:11434/v1
NEXT_PUBLIC_FASTAPI_URL=http://localhost:8000
NEXT_PUBLIC_APP_NAME=WapiBot Testing Interface
```

## Architecture

### Tech Stack

- **Framework**: Next.js 15 (App Router)
- **UI**: React 18.3 + Tailwind CSS 3.4
- **State**: Zustand 4.5 with localStorage persistence
- **AI**: Vercel AI SDK + Ollama
- **Icons**: Lucide React

### Project Structure

```
app/
├── layout.tsx              # Root layout with animated background
├── page.tsx                # Main orchestrator (sidebar + chat)
├── globals.css             # Glassmorphism styles
└── api/
    └── ollama/models       # Fetch available Ollama models

components/
├── layout/
│   ├── Header.tsx          # Mode switcher, model selector
│   └── Sidebar.tsx         # Contact list, new contact form
├── chat/
│   ├── ChatInterface.tsx   # Main chat orchestrator
│   ├── MessageBubble.tsx   # Message display component
│   └── TypingIndicator.tsx # "Bot typing..." animation
└── ui/
    ├── Button.tsx          # Glassmorphic button
    ├── GlassCard.tsx       # Glass surface component
    └── Input.tsx           # Glass input field

hooks/
├── useConversations.ts     # Zustand store (conversations, state management)
└── useOllamaModels.ts     # Fetch available Ollama models

lib/
├── types.ts                # TypeScript interfaces
├── utils.ts                # Utility functions
└── constants.ts            # App constants
```

## Usage

### Creating a Test Contact

1. Click the **+** button in the header
2. Enter a **10-digit phone number** (Indian format, starts with 6-9)
3. Enter a **display name**
4. Click **Create**

### Switching Backends

**Ollama Mode:**
- Uses local LLM running on `localhost:11434`
- Select different models from the dropdown
- Messages stream in real-time

**FastAPI Mode:**
- Connects to your backend on `localhost:8000`
- POST to `/webhook/chat` endpoint
- Displays bot responses with buttons, media, etc.

### Testing Multiple Contacts

- Create 3+ contacts with different phone numbers
- Switch between them via the sidebar
- Each contact has isolated message history
- Data persists in browser localStorage

## State Management

### Zustand Store (`useConversationStore`)

```typescript
{
  conversations: Conversation[]     // All chat threads
  activeConversationId: string      // Currently viewing
  backendMode: 'ollama' | 'fastapi' // Which mode active
  selectedOllamaModel: string       // e.g., 'gemma3:4b'
  availableOllamaModels: string[]   // Dropdown options
}
```

All state auto-persists to localStorage.

## API Integration

### Ollama API Route

```
POST /api/ollama/models
```

Fetches available Ollama models running locally.

**Response:**
```json
{
  "models": [
    {"name": "gemma3:4b", "id": "...", "size": "3.3 GB"},
    {"name": "qwen3:8b", "id": "...", "size": "5.2 GB"}
  ]
}
```

### FastAPI Integration (Future)

Will POST to your backend:

```bash
POST http://localhost:8000/webhook/chat
{
  "phone_number": "9876543210",
  "message_body": "Hello",
  "conversation_id": "unique-id"
}
```

Expected response format:

```json
{
  "message": "Hi there!",
  "buttons": [
    {"id": "btn_1", "label": "Book Service"},
    {"id": "btn_2", "label": "Cancel"}
  ],
  "media_url": "https://example.com/qr.png"
}
```

## Glassmorphism Design System

### Color Palette

```css
Background: Linear gradient from #0a0a0a to #1a1a1a
Text: #ffffff (primary), #999999 (secondary)
Glass: rgba(255, 255, 255, 0.05)
Border: rgba(255, 255, 255, 0.1)
```

### Utilities

```css
.glass-card          /* Main glass surface */
.glass-button        /* Interactive button */
.glass-input         /* Input field */
.message-bubble-user /* User message */
.message-bubble-bot  /* Bot message */
.text-shadow-glow    /* Glowing text */
```

### Animations

```css
animate-fade-in      /* Opacity fade */
animate-slide-up     /* Upward slide */
animate-pulse-glow   /* Glowing pulse */
```

## Development Tips

### Adding New Features

1. **New Component**: Create in `components/` with TypeScript
2. **New State**: Add actions to `hooks/useConversations.ts`
3. **New API Route**: Create in `app/api/`
4. **Styling**: Use Tailwind classes + custom glass utilities

### Type Safety

Always define types in `lib/types.ts`:

```typescript
export interface MyType {
  id: string;
  name: string;
  // ...
}
```

### Testing Locally

1. Start Ollama: `ollama serve`
2. Start frontend: `npm run dev`
3. Create contact with phone like `9876543210`
4. Send message to test Ollama integration

## Troubleshooting

### Ollama Not Available

- Ensure Ollama is running: `ollama serve`
- Check `http://localhost:11434/api/tags` returns models
- Models might be slow first time (loading into RAM)

### FastAPI Connection Error

- Ensure backend is running on port 8000
- Check `NEXT_PUBLIC_FASTAPI_URL` env var
- Verify `/webhook/chat` endpoint exists

### Models Not Loading

- Run `ollama list` to see available models
- Make sure models are pulled: `ollama pull gemma3:4b`
- Check browser console for errors

## Next Steps

1. **Connect to FastAPI backend** - Implement `/webhook/chat` integration
2. **Add message types** - Support buttons, media, templates
3. **Implement payment flow** - UPI QR code display
4. **Add booking features** - Service selection, date picking
5. **Deploy to cloud** - Docker setup for AWS/Digital Ocean

## License

MIT

## Support

For issues or questions about the frontend, check:
- Browser console for errors
- Network tab in DevTools
- Ollama/FastAPI server logs
