import path from 'node:path';
export const root=path.resolve(import.meta.dirname,'..');
export const providerHome=path.join(root,'.runtime/provider');
export const codexBinary=path.join(root,'node_modules/.bin/codex');
