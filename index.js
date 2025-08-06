#!/usr/bin/env node

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ErrorCode,
  ListToolsRequestSchema,
  McpError,
} from "@modelcontextprotocol/sdk/types.js";
import axios from "axios";
import { subDays, parseISO } from "date-fns";

class GranolaMCPServer {
  constructor() {
    this.server = new Server(
      {
        name: "granola-mcp-server",
        version: "1.0.0",
      },
      {
        capabilities: {
          tools: {},
        },
      }
    );

    this.apiKey = process.env.GRANOLA_API_KEY;
    this.userId = process.env.GRANOLA_USER_ID;
    this.baseURL = process.env.GRANOLA_API_URL || "https://api.granola.ai";
    
    if (!this.apiKey) {
      console.error("GRANOLA_API_KEY environment variable is required");
      process.exit(1);
    }

    this.setupToolHandlers();
  }

  setupToolHandlers() {
    this.server.setRequestHandler(ListToolsRequestSchema, async () => {
      return {
        tools: [
          {
            name: "get_personal_notes",
            description: "Retrieve personal Granola notes from the past 7 days where you were a participant in the call",
            inputSchema: {
              type: "object",
              properties: {
                days: {
                  type: "number",
                  description: "Number of days to look back (default: 7)",
                  default: 7,
                },
                limit: {
                  type: "number",
                  description: "Maximum number of notes to retrieve (default: 50)",
                  default: 50,
                },
              },
            },
          },
          {
            name: "check_call_participation",
            description: "Check if you were a participant in a specific call/meeting",
            inputSchema: {
              type: "object",
              properties: {
                noteId: {
                  type: "string",
                  description: "The ID of the note/meeting to check",
                },
              },
              required: ["noteId"],
            },
          },
        ],
      };
    });

    this.server.setRequestHandler(CallToolRequestSchema, async (request) => {
      const { name, arguments: args } = request.params;

      try {
        switch (name) {
          case "get_personal_notes":
            return await this.getPersonalNotes(args);
          case "check_call_participation":
            return await this.checkCallParticipation(args);
          default:
            throw new McpError(
              ErrorCode.MethodNotFound,
              `Unknown tool: ${name}`
            );
        }
      } catch (error) {
        console.error(`Error in tool ${name}:`, error);
        throw new McpError(
          ErrorCode.InternalError,
          `Error executing tool ${name}: ${error.message}`
        );
      }
    });
  }

  async makeAPIRequest(endpoint, params = {}) {
    try {
      const response = await axios.get(`${this.baseURL}${endpoint}`, {
        headers: {
          Authorization: `Bearer ${this.apiKey}`,
          "Content-Type": "application/json",
        },
        params,
      });
      return response.data;
    } catch (error) {
      console.error(`API request failed: ${error.message}`);
      if (error.response) {
        console.error(`Response status: ${error.response.status}`);
        console.error(`Response data:`, error.response.data);
      }
      throw error;
    }
  }

  async getPersonalNotes(args) {
    const { days = 7, limit = 50 } = args;
    const cutoffDate = subDays(new Date(), days);

    try {
      // Fetch all notes from the specified time period
      const allNotes = await this.makeAPIRequest("/notes", {
        limit: limit * 2, // Fetch more to account for filtering
        since: cutoffDate.toISOString(),
        sort: "created_desc",
      });

      // Filter notes to only include ones where the user was a participant
      const personalNotes = [];
      
      for (const note of allNotes.notes || allNotes || []) {
        try {
          const isParticipant = await this.wasUserParticipant(note);
          
          if (isParticipant) {
            personalNotes.push({
              id: note.id,
              title: note.title || note.meeting_title || "Untitled Meeting",
              date: note.created_at || note.date,
              content: note.content || note.summary,
              participants: note.participants || note.attendees || [],
              duration: note.duration,
              meeting_url: note.meeting_url,
              shared_with: note.shared_with || [],
              is_personal: true,
              meeting_type: note.meeting_type || "unknown",
            });
          }
          
          // Stop if we've collected enough personal notes
          if (personalNotes.length >= limit) {
            break;
          }
        } catch (participantError) {
          console.error(`Error checking participation for note ${note.id}:`, participantError);
          // Continue with next note rather than failing completely
        }
      }

      return {
        content: [
          {
            type: "text",
            text: JSON.stringify({
              message: `Found ${personalNotes.length} personal notes from the past ${days} days`,
              notes: personalNotes,
              filtered_count: (allNotes.notes || allNotes || []).length - personalNotes.length,
              total_found: (allNotes.notes || allNotes || []).length,
            }, null, 2),
          },
        ],
      };
    } catch (error) {
      throw new Error(`Failed to retrieve personal notes: ${error.message}`);
    }
  }

  async wasUserParticipant(note) {
    try {
      // Strategy 1: Check if user ID is in participants list
      if (note.participants && Array.isArray(note.participants)) {
        const userInParticipants = note.participants.some(participant => {
          return participant.id === this.userId || 
                 participant.user_id === this.userId ||
                 participant.email === process.env.GRANOLA_USER_EMAIL;
        });
        
        if (userInParticipants) {
          return true;
        }
      }

      // Strategy 2: Check if user is the note creator/owner
      if (note.created_by === this.userId || note.owner_id === this.userId) {
        return true;
      }

      // Strategy 3: Check meeting metadata for participant information
      if (note.meeting_id) {
        try {
          const meetingDetails = await this.makeAPIRequest(`/meetings/${note.meeting_id}`);
          
          if (meetingDetails.participants) {
            return meetingDetails.participants.some(participant => {
              return participant.id === this.userId || 
                     participant.user_id === this.userId ||
                     participant.email === process.env.GRANOLA_USER_EMAIL;
            });
          }
        } catch (meetingError) {
          console.error(`Could not fetch meeting details for ${note.meeting_id}:`, meetingError);
        }
      }

      // Strategy 4: Check if note was shared WITH user vs created BY user
      // If note has shared_with array and user is only in that list (not creator), exclude it
      if (note.shared_with && Array.isArray(note.shared_with)) {
        const isSharedWithUser = note.shared_with.some(sharedUser => {
          return sharedUser.id === this.userId || 
                 sharedUser.user_id === this.userId ||
                 sharedUser.email === process.env.GRANOLA_USER_EMAIL;
        });
        
        // If user is only in shared_with list but not the creator, this is a shared note
        if (isSharedWithUser && note.created_by !== this.userId && note.owner_id !== this.userId) {
          return false;
        }
      }

      // Strategy 5: Check note permissions and ownership
      if (note.permissions) {
        return note.permissions.owner === this.userId || 
               note.permissions.created_by === this.userId;
      }

      // Default: If we can't determine participation clearly, exclude for safety
      // This ensures we only include notes we're confident the user participated in
      console.warn(`Could not determine participation for note ${note.id}, excluding for safety`);
      return false;

    } catch (error) {
      console.error(`Error checking user participation for note ${note.id}:`, error);
      return false;
    }
  }

  async checkCallParticipation(args) {
    const { noteId } = args;

    try {
      // Get detailed note information
      const note = await this.makeAPIRequest(`/notes/${noteId}`);
      const isParticipant = await this.wasUserParticipant(note);

      return {
        content: [
          {
            type: "text",
            text: JSON.stringify({
              note_id: noteId,
              is_participant: isParticipant,
              note_title: note.title || note.meeting_title || "Untitled Meeting",
              created_by: note.created_by,
              owner_id: note.owner_id,
              participants: note.participants || [],
              shared_with: note.shared_with || [],
              meeting_type: note.meeting_type,
              participation_details: {
                user_id: this.userId,
                user_email: process.env.GRANOLA_USER_EMAIL,
                check_methods: [
                  "participants_list",
                  "note_ownership", 
                  "meeting_metadata",
                  "sharing_status"
                ]
              }
            }, null, 2),
          },
        ],
      };
    } catch (error) {
      throw new Error(`Failed to check call participation: ${error.message}`);
    }
  }

  async run() {
    const transport = new StdioServerTransport();
    await this.server.connect(transport);
    console.error("Granola MCP Server running on stdio");
  }
}

const server = new GranolaMCPServer();
server.run().catch(console.error);