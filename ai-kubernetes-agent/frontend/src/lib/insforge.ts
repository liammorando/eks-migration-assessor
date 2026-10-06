import { createClient } from '@insforge/sdk';

const baseUrl = process.env.NEXT_PUBLIC_INSFORGE_BASE_URL || 'https://ifn44snm.us-east.insforge.app';
const anonKey = process.env.NEXT_PUBLIC_INSFORGE_ANON_KEY || 'your-anon-key';

export const insforge = createClient({
  baseUrl,
  anonKey,
});

export default insforge;