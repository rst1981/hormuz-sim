import type { TurnReport, RunResult, MCResult } from '../types';

export class SimWebSocket {
  private ws: WebSocket | null = null;

  private get wsBase(): string {
    const apiUrl = import.meta.env.VITE_API_URL;
    if (apiUrl) {
      // Convert http(s) API URL to ws(s) URL, strip /api suffix
      const base = apiUrl.replace(/\/api\/?$/, '').replace(/^http/, 'ws');
      return base;
    }
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    return `${protocol}//${window.location.host}`;
  }

  connectMC(
    jobId: string,
    onRunComplete: (data: RunResult) => void,
    onProgress: (completed: number, total: number) => void,
    onJobComplete: (data: MCResult) => void,
  ) {
    this.ws = new WebSocket(`${this.wsBase}/ws/mc/${jobId}`);
    this.ws.onmessage = (event) => {
      const msg = JSON.parse(event.data);
      if (msg.type === 'run_complete') onRunComplete(msg.data);
      else if (msg.type === 'progress') onProgress(msg.completed, msg.total);
      else if (msg.type === 'job_complete') onJobComplete(msg.data);
    };
    this.ws.onerror = (e) => console.error('WS error:', e);
  }

  connectLiveSim(
    simId: string,
    onTurn: (data: TurnReport) => void,
    onTerminated: (outcome: string, finalState: unknown) => void,
  ) {
    this.ws = new WebSocket(`${this.wsBase}/ws/sim/${simId}/live`);
    this.ws.onmessage = (event) => {
      const msg = JSON.parse(event.data);
      if (msg.type === 'turn') onTurn(msg.data);
      else if (msg.type === 'terminated') onTerminated(msg.outcome, msg.final_state);
    };
  }

  send(msg: Record<string, unknown>) {
    this.ws?.send(JSON.stringify(msg));
  }

  disconnect() {
    this.ws?.close();
    this.ws = null;
  }
}

export const simWS = new SimWebSocket();
