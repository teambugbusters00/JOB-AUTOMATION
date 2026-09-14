import type { CapacitorConfig } from '@capacitor/cli';

const serverUrl = process.env.CAPACITOR_SERVER_URL || 'https://job-automation-8nm3.onrender.com';

const config: CapacitorConfig = {
  appId: 'com.teambugbusters.jobautomation',
  appName: 'JOB-AUTOMATION',
  webDir: 'web',
  server: {
    url: serverUrl,
    cleartext: false,
    androidScheme: 'https'
  },
  android: {
    allowMixedContent: false
  }
};

export default config;
