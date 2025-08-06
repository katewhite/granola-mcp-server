# Granola MCP Server

A Model Context Protocol (MCP) server for Granola AI integration that retrieves your personal notes while filtering out shared notes where you weren't a participant.

## Features

- ✅ **Participant Filtering**: Only retrieves notes from calls where you were an actual participant
- ✅ **Excludes Shared Notes**: Filters out public notes that were just shared with you
- ✅ **Time-based Retrieval**: Get notes from the past N days (default: 7 days)
- ✅ **Multiple Verification Methods**: Uses multiple strategies to verify call participation
- ✅ **Detailed Participation Check**: Individual note participation verification

## Installation

1. Clone this repository:
```bash
git clone <repository-url>
cd granola-mcp-server
```

2. Install dependencies:
```bash
npm install
```

3. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your Granola credentials
```

## Configuration

Create a `.env` file with the following variables:

```env
# Required
GRANOLA_API_KEY=your_granola_api_key_here
GRANOLA_USER_ID=your_user_id_here

# Optional
GRANOLA_USER_EMAIL=your_email@example.com
GRANOLA_API_URL=https://api.granola.ai
```

### Getting Your Granola Credentials

1. **API Key**: Available in your Granola account settings under "API Access"
2. **User ID**: Found in your profile or account settings
3. **Email**: Your registered Granola account email

## Usage

### Running the Server

```bash
npm start
```

### Available Tools

#### `get_personal_notes`
Retrieves your personal notes from calls where you were a participant.

**Parameters:**
- `days` (optional): Number of days to look back (default: 7)
- `limit` (optional): Maximum number of notes to retrieve (default: 50)

**Example:**
```json
{
  "name": "get_personal_notes",
  "arguments": {
    "days": 14,
    "limit": 25
  }
}
```

#### `check_call_participation`
Checks if you were a participant in a specific call/meeting.

**Parameters:**
- `noteId` (required): The ID of the note/meeting to check

**Example:**
```json
{
  "name": "check_call_participation", 
  "arguments": {
    "noteId": "note_123456"
  }
}
```

## Participant Filtering Logic

The server uses multiple strategies to determine if you were a participant in a call:

1. **Participants List Check**: Verifies if your user ID/email is in the meeting participants
2. **Note Ownership**: Checks if you created or own the note
3. **Meeting Metadata**: Fetches detailed meeting information for participant verification
4. **Sharing Status**: Distinguishes between notes you created vs. notes shared with you
5. **Permissions Check**: Verifies note-level permissions and ownership

### Why This Filtering Matters

- **Personal Notes Only**: Excludes notes from meetings you didn't attend
- **No Shared Content**: Filters out notes that were just shared with you for reference
- **Privacy Focused**: Ensures you only see notes from your actual meetings
- **Accurate Context**: Provides AI assistants with relevant, personal meeting data

## Integration with MCP Clients

### Claude Desktop

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "granola": {
      "command": "node",
      "args": ["/path/to/granola-mcp-server/index.js"],
      "env": {
        "GRANOLA_API_KEY": "your_api_key",
        "GRANOLA_USER_ID": "your_user_id"
      }
    }
  }
}
```

### Other MCP Clients

This server implements the standard MCP protocol and works with any compatible client.

## Error Handling

- **Missing Credentials**: Server exits if required environment variables are missing
- **API Failures**: Individual note failures don't stop the entire retrieval process
- **Participation Uncertainty**: Notes are excluded if participation cannot be confirmed

## Development

```bash
# Run in development mode with auto-reload
npm run dev
```

## Troubleshooting

### Common Issues

1. **No Notes Returned**: 
   - Verify your API credentials are correct
   - Check that you have notes in the specified time period
   - Ensure you were actually a participant in recent calls

2. **API Authentication Errors**:
   - Confirm your `GRANOLA_API_KEY` is valid and has proper permissions
   - Check that the API URL is correct

3. **Participant Detection Issues**:
   - Verify your `GRANOLA_USER_ID` and `GRANOLA_USER_EMAIL` are correct
   - Check that Granola properly recorded your participation in meetings

### Debug Information

The server logs detailed information about:
- API requests and responses
- Participant checking logic
- Note filtering decisions
- Error conditions

Check the console output for debugging information.

## License

MIT