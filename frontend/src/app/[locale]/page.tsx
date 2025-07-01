import { getCurrentLocale } from "@/utils/getCurrentLocale"
import { getDictionary, createTranslator } from "@/utils/translation"
import React from "react"


import { Metadata } from "next";
export const metadata: Metadata = {
  title: {
    default: "EnterViu",
    template: "%s | EnterViu"
  },
  description: "EnterViu - Professional Career Platform. Build your profile, discover job opportunities, and connect with employers through our intelligent job matching system.",
  keywords: [
    "EnterViu", 
    "Job Search", 
    "Career", 
    "Profile Building", 
    "Employment", 
    "Job Matching", 
    "Professional", 
    "Resume", 
    "Career Development", 
    "Job Board", 
    "Recruitment", 
    "Next.js", 
    "React", 
    "TypeScript", 
    "i18n", 
    "Internationalization", 
    "Dark Mode",
    "Career Platform",
    "Job Portal",
    "Professional Network"
  ],
  authors: [
    { name: "EnterViu Team", url: "https://enterviu.com" },
    { name: "Career Development Team" }
  ],
  creator: "EnterViu - Professional Career Platform",
  publisher: "EnterViu Organization",
  applicationName: "EnterViu Platform",
  generator: "Next.js",
  referrer: "origin-when-cross-origin",
  category: "Education",
  classification: "Educational Platform",  metadataBase: new URL("https://enterviu.com"),
  alternates: {
    canonical: "/",
    languages: {
      "vi-VN": "/vi",
      "en-US": "/en",
    },
  },
  icons: {
    icon: [
      { url: "/assets/logo/logo_web.jpg", sizes: "32x32", type: "image/png" },
      { url: "/assets/logo/logo_web.jpg", sizes: "16x16", type: "image/png" },
    ],
    apple: [
      { url: "/assets/logo/logo_web.jpg", sizes: "180x180", type: "image/png" },
    ],
    shortcut: "/assets/logo/logo_web.jpg",
  },
  manifest: "/manifest.json",
  openGraph: {
    type: "website",
    locale: "vi_VN",
    alternateLocale: ["en_US"],
    url: "https://enterviu.com",
    title: "EnterViu - Professional Career Platform",
    description: "Join EnterViu community to build your professional profile, discover job opportunities, and connect with top employers through intelligent matching.",
    siteName: "EnterViu Platform",
    images: [
      {
        url: "/assets/logo/logo_web.jpg",
        width: 1200,
        height: 630,
        alt: "EnterViu Logo - Professional Career Platform",
      },
    ],
    countryName: "Vietnam",
  },
  twitter: {
    card: "summary_large_image",
    site: "@enterviu_official",
    creator: "@enterviu_official",
    title: "EnterViu - Professional Career Platform",
    description: "Join EnterViu community to build your professional profile, discover job opportunities, and connect with top employers through intelligent matching.",
    images: ["/assets/logo/logo_web.jpg"],
  },
  robots: {
    index: true,
    follow: true,
    nocache: false,
    googleBot: {
      index: true,
      follow: true,
      noimageindex: false,
      "max-video-preview": -1,
      "max-image-preview": "large",
      "max-snippet": -1,
    },
  },
  verification: {
    google: "your-google-site-verification-code",
    yandex: "your-yandex-verification-code",
    yahoo: "your-yahoo-verification-code",
  },  other: {
    "mobile-web-app-capable": "yes",
    "apple-mobile-web-app-capable": "yes",
    "apple-mobile-web-app-status-bar-style": "default",
    "apple-mobile-web-app-title": "EnterViu",
    "application-name": "EnterViu Platform",
    "msapplication-TileColor": "#3b82f6",
    "msapplication-TileImage": "/assets/logo/logo_web.jpg",
    "theme-color": "#3b82f6",
  },
};
async function Home() {
  const locale = await getCurrentLocale();
  const dictionary = await getDictionary(locale);
  const t = createTranslator(dictionary);


  // Placeholder features data
  const featuresData: { title: string }[] = []; // Replace with your static or fetched data

  return (
    <>
      <div>
        <h1>{t('home.title', { defaultValue: 'Welcome to EnterViu' })}</h1>
        <p>
          {t('home.description')},
        </p>
        {/* Example static sections */}
        <section>
          <h2>Features</h2>
          <ul>
            {featuresData.map((feature, idx) => (
              <li key={idx}>{feature.title}</li>
            ))}
          </ul>
        </section>
        <section>
        </section>
      </div>
    </>
  );
}

export default Home;
