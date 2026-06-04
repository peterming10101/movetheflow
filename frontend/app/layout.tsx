import "./globals.css";

export const metadata = {
  title: "Movetheflow Diagnostics",
  description: "Phase 1 market-data diagnostics",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
