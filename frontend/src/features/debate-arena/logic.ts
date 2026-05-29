import type { DebateStreamEvent } from './types';

interface ParsedEventBuffer {
  events: DebateStreamEvent[];
  remainder: string;
}

export function parseDebateEventBuffer(buffer: string): ParsedEventBuffer {
  const normalized = buffer.replace(/\r\n/g, '\n');
  const blocks = normalized.split('\n\n');
  const remainder = blocks.pop() ?? '';
  const events = blocks
    .map(parseDebateEventBlock)
    .filter((event): event is DebateStreamEvent => event !== null);

  return { events, remainder };
}

function parseDebateEventBlock(block: string): DebateStreamEvent | null {
  let eventType = '';
  const dataLines: string[] = [];

  block.split('\n').forEach((line) => {
    if (line.startsWith('event:')) {
      eventType = line.slice('event:'.length).trim();
      return;
    }

    if (line.startsWith('data:')) {
      dataLines.push(line.slice('data:'.length).trimStart());
    }
  });

  if (!eventType || dataLines.length === 0) {
    return null;
  }

  try {
    const data = JSON.parse(dataLines.join('\n')) as Record<string, unknown>;
    return { ...data, type: eventType } as DebateStreamEvent;
  } catch {
    return null;
  }
}
