import {Injectable} from '@angular/core';

interface ExperimentSettings {
  readonly websocketsEnabled: boolean;
  readonly webComponentsCacheKey: string | null;
}

@Injectable({
  providedIn: 'root',
})
export class ExperimentService {
  private readonly settings: ExperimentSettings;

  constructor() {
    const windowSettings = (window as any)['__MESOP_EXPERIMENTS__'];
    this.settings = windowSettings ?? {
      websocketsEnabled: false,
    };
  }

  get websocketsEnabled(): boolean {
    return this.settings.websocketsEnabled;
  }
  get webComponentsCacheKey(): string | null {
    return this.settings.webComponentsCacheKey;
  }
}
