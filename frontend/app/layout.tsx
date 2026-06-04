import "./globals.css";

export const metadata = {
  title: "Movetheflow Platform",
  description: "Live BTCUSDT orderflow workspace",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
