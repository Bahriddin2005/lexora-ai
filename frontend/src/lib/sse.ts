export type SseEvent = { delta?: string; done?: boolean; cached?: boolean; error?: string; message?: string };

/** Incremental parser for `data: {...}\n\n` Server-Sent Events. */
export class SseParser {
  private buffer = "";

  push(chunk: string): SseEvent[] {
    this.buffer += chunk;
    const events: SseEvent[] = [];
    let index: number;
    while ((index = this.buffer.indexOf("\n\n")) !== -1) {
      const block = this.buffer.slice(0, index);
      this.buffer = this.buffer.slice(index + 2);
      const data = block
        .split("\n")
        .filter((line) => line.startsWith("data:"))
        .map((line) => line.slice(5).trimStart())
        .join("\n");
      if (!data) continue;
      try {
        events.push(JSON.parse(data) as SseEvent);
      } catch {
        // ignore malformed events
      }
    }
    return events;
  }
}

export async function readSse(res: Response, onEvent: (event: SseEvent) => void): Promise<void> {
  if (!res.body) return;
  const reader = res.body.pipeThrough(new TextDecoderStream()).getReader();
  const parser = new SseParser();
  for (;;) {
    const { value, done } = await reader.read();
    if (done) break;
    for (const event of parser.push(value)) onEvent(event);
  }
}
