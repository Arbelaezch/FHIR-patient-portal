import "./globals.css";

export const metadata = {
  title: "FHIR Patient Portal",
  description: "Your personal health dashboard",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}