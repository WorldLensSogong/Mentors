export interface DebatePersona {
  id: string;
  name: string;
  stance: string;
  style: string;
  is_public: boolean;
}

export interface DebateStartRequest {
  topic: string;
  persona_a_id: string;
  persona_b_id: string;
}

export interface DebateStartResponse {
  debate_session_id: number;
  topic: string;
  status: string;
  stream_url: string;
}

export interface DebateEligibility {
  allowed: boolean;
  tier: string;
  reason: string | null;
}

export interface DebateDocument {
  id: string;
  title: string;
  source: string;
  url: string;
  published_at: string;
  metadata?: Record<string, unknown>;
}

export type DebateTurnType = 'opinion' | 'rebuttal' | 'counter';

export interface DebateSpeaker {
  id: string;
  name: string;
}

export interface DebateContextEvent {
  type: 'context';
  debate_session_id: number;
  documents: DebateDocument[];
}

export interface DebateTurnStartEvent {
  type: 'turn_start';
  turn_index: number;
  turn_type: DebateTurnType;
  speaker: DebateSpeaker;
}

export interface DebateDeltaEvent {
  type: 'delta';
  turn_index: number;
  speaker: DebateSpeaker;
  delta: string;
}

export interface DebateTurnDoneEvent {
  type: 'turn_done';
  turn_index: number;
}

export interface DebateDoneEvent {
  type: 'done';
  debate_session_id: number;
  replay?: boolean;
}

export interface DebateErrorEvent {
  type: 'error';
  debate_session_id?: number;
  code?: string;
  message: string;
}

export type DebateStreamEvent =
  | DebateContextEvent
  | DebateTurnStartEvent
  | DebateDeltaEvent
  | DebateTurnDoneEvent
  | DebateDoneEvent
  | DebateErrorEvent;

export interface DebateTurnMessage {
  turnIndex: number;
  turnType: DebateTurnType;
  speaker: DebateSpeaker;
  content: string;
  isDone: boolean;
}

export interface DebateSessionSummary {
  id: number;
  topic: string;
  status: string;
  persona_a_id: string;
  persona_a_name: string;
  persona_b_id: string;
  persona_b_name: string;
  created_at: string;
  completed_at: string | null;
}

export interface DebateSessionListResponse {
  sessions: DebateSessionSummary[];
}

export interface DebateMessageDetail {
  turn_index: number;
  speaker_id: string;
  speaker_name: string;
  turn_type: string;
  content: string;
}

export interface DebateSessionDetail {
  id: number;
  topic: string;
  status: string;
  persona_a_id: string;
  persona_a_name: string;
  persona_b_id: string;
  persona_b_name: string;
  created_at: string;
  completed_at: string | null;
  messages: DebateMessageDetail[];
}
