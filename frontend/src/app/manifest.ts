import type { MetadataRoute } from "next";

export default function manifest(): MetadataRoute.Manifest {
  return {
    name: "Bámi-Sọ̀rọ̀ — Yoruba Speech-to-Text & Translation",
    short_name: "Bámi-Sọ̀rọ̀",
    description:
      "Professional Yoruba speech recognition and translation powered by AI. Transcribe, translate, and preserve the beauty of Èdè Yorùbá.",
    id: "/",
    start_url: "/",
    scope: "/",
    display: "standalone",
    orientation: "portrait",
    background_color: "#09090b",
    theme_color: "#09090b",
    lang: "en",
    categories: ["productivity", "utilities"],
    icons: [
      { src: "/icons/icon-192.png", sizes: "192x192", type: "image/png", purpose: "any" },
      { src: "/icons/icon-512.png", sizes: "512x512", type: "image/png", purpose: "any" },
      {
        src: "/icons/icon-maskable-512.png",
        sizes: "512x512",
        type: "image/png",
        purpose: "maskable",
      },
    ],
    shortcuts: [
      {
        name: "Speech-to-Text",
        short_name: "Transcribe",
        description: "Record or upload audio and transcribe Yoruba speech",
        url: "/dashboard",
        icons: [
          { src: "/icons/icon-192.png", sizes: "192x192", type: "image/png", purpose: "any" },
        ],
      },
      {
        name: "Translate",
        short_name: "Translate",
        description: "Translate English, Yoruba, or mixed text",
        url: "/dashboard/translate",
        icons: [
          { src: "/icons/icon-192.png", sizes: "192x192", type: "image/png", purpose: "any" },
        ],
      },
    ],
  };
}