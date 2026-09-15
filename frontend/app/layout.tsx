import type { Metadata } from "next";
import "./globals.css";
import { Toaster } from "sonner";

export const metadata: Metadata = {
  title: "JOB-AUTOMATION | AI Career OS",
  description: "AI-powered job discovery, resume intelligence and application preparation.",
};

export default function RootLayout({children}:{children:React.ReactNode}) {
  return <html lang="en"><body>{children}<Toaster theme="dark" position="top-right"/></body></html>;
}
