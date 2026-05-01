import {Injectable} from '@angular/core';

interface ExperimentSettings {
  readonly websocketsEnabled: boolean;
  readonly websocketsReloadOnDisconnect: boolean;
  readonly webComponentsCacheKey: string | null;
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
      websocketsReloadOnDisconnect:
        windowSettings?.['websocketsReloadOnDisconnect'] ?? false,
      webComponentsCacheKey: windowSettings?.['webComponentsCacheKey'] ?? null,
    };
  }

  get websocketsEnabled(): boolean {
    return this.settings.websocketsEnabled;
  }
  get websocketsReloadOnDisconnect(): boolean {
    return this.settings.websocketsReloadOnDisconnect;
  }
  get webComponentsCacheKey(): string | null {
    return this.settings.webComponentsCacheKey;
  }
}
