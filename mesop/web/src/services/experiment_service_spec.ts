import {ExperimentService} from 'mesop/mesop/web/src/services/experiment_service';

describe('ExperimentService', () => {
  afterEach(() => {
    (window as any).__MESOP_EXPERIMENTS__ = undefined;
  });

  it('uses default settings when __MESOP_EXPERIMENTS__ is not set', () => {
    const service = new ExperimentService();
    expect(service.websocketsEnabled).toBe(false);
  });

  it('reads websocketsEnabled=true from window settings', () => {
    (window as any).__MESOP_EXPERIMENTS__ = {
      websocketsEnabled: true,
      webComponentsCacheKey: null,
    };
    const service = new ExperimentService();
    expect(service.websocketsEnabled).toBe(true);
  });

  it('reads webComponentsCacheKey from window settings', () => {
    (window as any).__MESOP_EXPERIMENTS__ = {
      websocketsEnabled: false,
      webComponentsCacheKey: 'abc123',
    };
    const service = new ExperimentService();
    expect(service.webComponentsCacheKey).toBe('abc123');
  });

  it('returns null webComponentsCacheKey when explicitly set to null', () => {
    (window as any).__MESOP_EXPERIMENTS__ = {
      websocketsEnabled: false,
      webComponentsCacheKey: null,
    };
    const service = new ExperimentService();
    expect(service.webComponentsCacheKey).toBeNull();
  });
});
