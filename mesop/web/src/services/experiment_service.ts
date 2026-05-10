import {Injectable} from '@angular/core';

interface ExperimentSettings {
  readonly websocketsEnabled: boolean;
  readonly webComponentsCacheKey: string | null;
  readonly websocketsProbeOnDisconnect: boolean;
}

@Injectable({
  providedIn: 'root',
})
export class ExperimentService {
  private readonly settings: ExperimentSettings;

  constructor() {
    const windowSettings = (window as any)['__MESOP_EXPERIMENTS__'];
    this.settings = {
      websocketsEnabled: windowSettings?.['websocketsEnabled'] ?? false,
      webComponentsCacheKey: windowSettings?.['webComponentsCacheKey'] ?? null,
      websocketsProbeOnDisconnect:
        windowSettings?.['websocketsProbeOnDisconnect'] ?? false,
    };
  }

  get websocketsEnabled(): boolean {
    return this.settings.websocketsEnabled;
  }
  get websocketsProbeOnDisconnect(): boolean {
    return this.settings.websocketsProbeOnDisconnect;
  }
  get webComponentsCacheKey(): string | null {
    return this.settings.webComponentsCacheKey;
  }
}
