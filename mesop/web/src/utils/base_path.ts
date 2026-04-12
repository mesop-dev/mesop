export function prefixBasePath(path: string): string {
  const base = (window as any)['__MESOP_BASE_URL_PATH__'] as string | undefined;
  if (!base) {
    return path;
  }
  if (!path.startsWith('/')) {
    path = `/${path}`;
  }
  if (base.endsWith('/')) {
    return base + path.substring(1);
  }
  return base + path;
}
