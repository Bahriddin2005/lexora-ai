import type { CapacitorConfig } from "@capacitor/cli";

const appUrl = process.env.LEXORA_APP_URL ?? "https://lexora-ai.onrender.com";

const config: CapacitorConfig = {
  appId: "uz.lexora.app",
  appName: "Lexora AI",
  webDir: "mobile-shell",
  server: {
    url: appUrl,
    cleartext: appUrl.startsWith("http://"),
    androidScheme: "https",
  },
  android: {
    backgroundColor: "#4f46e5",
    allowMixedContent: false,
  },
};

export default config;
