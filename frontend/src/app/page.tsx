import Link from "next/link";
import Image from "next/image";
import { ThemeToggle } from "@/components/ThemeToggle";
import { Mic, Languages, Sparkles, AudioWaveform, ArrowRight, Play, FileText, ArrowDownToLine, ShieldCheck } from "lucide-react";

const features = [
  {
    icon: Mic,
    title: "Accurate Yorùbá speech-to-text",
    body: "Local Yorùbá ASR with a four-engine cascade — Whisper, Faster-Whisper, speechbrain and NLLB — tuned for clear, reliable transcription.",
  },
  {
    icon: Languages,
    title: "Translate in seconds",
    body: "Go from Yorùbá to English — or back — on demand. Translate speech while you speak, or paste text for instant results.",
  },
  {
    icon: Sparkles,
    title: "Code-switching, unified",
    body: "Speak naturally mixing Yorùbá and English. We detect the mix and produce one clean, consistent output.",
  },
  {
    icon: ShieldCheck,
    title: "Tone-perfect output",
    body: "Diacritics and Èdè Yorùbá spellings are restored and preserved — text that reads as beautifully as it sounds.",
  },
];

const steps = [
  {
    icon: Mic,
    step: "01",
    title: "Speak or upload",
    body: "Tap record on your phone, or upload any audio file you already have.",
  },
  {
    icon: FileText,
    step: "02",
    title: "We transcribe & translate",
    body: "Streaming AI returns polished text live — in Yorùbá or English.",
  },
  {
    icon: ArrowDownToLine,
    step: "03",
    title: "Copy, export, keep",
    body: "Save transcripts to history, download as .txt, .srt or .html, or replay your audio.",
  },
];

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-background text-foreground">
      {/* ─── Nav ─────────────────────────────────────────── */}
      <header className="sticky top-0 z-40 border-b border-border bg-background backdrop-blur-lg safe-top">
        <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-4 md:px-6">
          <Link href="/" className="flex items-center gap-2.5">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-blue-500 to-indigo-600 text-white shadow-lg shadow-blue-500/20">
              <AudioWaveform className="h-5 w-5" />
            </div>
            <div className="leading-tight">
              <span className="text-sm font-bold gradient-text">Bámi-Sọ̀rọ̀</span>
              <div className="text-[10px] font-medium uppercase tracking-wider text-muted">Yorùbá Speech · Text</div>
            </div>
          </Link>

          <nav className="hidden items-center gap-7 md:flex">
            <Link href="#features" className="text-sm font-medium text-secondary hover:text-foreground transition-colors">
              Features
            </Link>
            <Link href="#how" className="text-sm font-medium text-secondary hover:text-foreground transition-colors">
              How it works
            </Link>
            <Link href="#about" className="text-sm font-medium text-secondary hover:text-foreground transition-colors">
              About
            </Link>
          </nav>

          <div className="flex items-center gap-2">
            <ThemeToggle />
            <Link
              href="/auth"
              className="hidden rounded-lg px-3.5 py-2 text-sm font-medium text-secondary hover:text-foreground hover:bg-slate-100 dark:hover:bg-white/5 transition-colors sm:inline-flex"
            >
              Sign in
            </Link>
            <Link
              href="/auth"
              className="inline-flex items-center gap-1.5 rounded-lg bg-blue-600 px-3.5 py-2 text-sm font-medium text-white hover:bg-blue-700 transition-colors shadow-sm"
            >
              Get started
              <ArrowRight className="h-4 w-4" />
            </Link>
          </div>
        </div>
      </header>

      {/* ─── Hero ────────────────────────────────────────── */}
      <section className="relative overflow-hidden">
        <div aria-hidden className="pointer-events-none absolute -top-40 right-0 h-[520px] w-[520px] rounded-full bg-blue-500/10 blur-3xl" />
        <div aria-hidden className="pointer-events-none absolute top-40 -left-40 h-[440px] w-[440px] rounded-full bg-indigo-500/10 blur-3xl" />

        <div className="relative mx-auto grid max-w-6xl items-center gap-12 px-4 py-16 md:px-6 md:py-24 lg:grid-cols-[1.05fr_0.95fr]">
          <div>
            <div className="mb-5 inline-flex items-center gap-2 rounded-full border border-border bg-card px-3 py-1.5 text-xs font-medium text-secondary">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse-dot" />
              AI-powered Yorùbá speech-to-text & translation
            </div>

            <h1 className="text-4xl font-extrabold leading-[1.08] tracking-tight md:text-6xl">
              Your Yorùbá voice,
              <br />
              <span className="gradient-text">understood perfectly.</span>
            </h1>

            <p className="mt-6 max-w-xl text-base leading-relaxed text-secondary md:text-lg">
              Bámi-Sọ̀rọ̀ turns spoken Yorùbá — even mixed with English — into polished,
              tone-perfect text, and translates it instantly. Built for journalists,
              broadcasters, and anyone who doesn&apos;t want a dialect lost to typing.
            </p>

            <div className="mt-8 flex flex-wrap items-center gap-3">
              <Link
                href="/auth"
                className="inline-flex items-center gap-2 rounded-xl bg-blue-600 px-6 py-3 text-sm font-semibold text-white shadow-lg shadow-blue-600/25 hover:bg-blue-700 transition-colors"
              >
                <Mic className="h-4 w-4" />
                Start transcribing free
              </Link>
              <Link
                href="#features"
                className="inline-flex items-center gap-2 rounded-xl border border-border bg-card px-6 py-3 text-sm font-semibold text-foreground hover:border-slate-300 dark:hover:border-white/20 hover:bg-slate-50 dark:hover:bg-white/5 transition-colors"
              >
                <Play className="h-4 w-4" />
                See how it works
              </Link>
            </div>

            <dl className="mt-10 grid max-w-md grid-cols-3 divide-x divide-border border border-border rounded-xl bg-card">
              {[
                { k: "Yorùbá", v: "native-speech model" },
                { k: "2", v: "languages, one output" },
                { k: "4", v: "ASR engine cascade" },
              ].map((s) => (
                <div key={s.v} className="px-4 py-3">
                  <dt className="text-lg font-bold text-foreground">{s.k}</dt>
                  <dd className="text-[11px] leading-tight text-muted">{s.v}</dd>
                </div>
              ))}
            </dl>
          </div>

          {/* Hero photo */}
          <div className="relative">
            <div className="relative overflow-hidden rounded-3xl border border-border shadow-2xl shadow-blue-900/10">
              <div className="aspect-[4/3] md:aspect-[5/6]">
                <Image
                  src="/hero-voiceover.jpg"
                  alt="A Nigerian voice-over artist recording Yorùbá speech in a professional studio"
                  fill
                  priority
                  sizes="(max-width: 1024px) 100vw, 560px"
                  className="object-cover"
                />
              </div>
              <div aria-hidden className="absolute inset-0 bg-gradient-to-t from-black/60 via-black/10 to-transparent" />

              <div className="absolute bottom-4 left-4 right-4 flex items-center justify-between gap-3">
                <div className="flex items-center gap-2.5 rounded-xl bg-black/55 px-3.5 py-2.5 backdrop-blur-md">
                  <span className="flex h-6 w-6 items-center justify-center rounded-md bg-emerald-500/90">
                    <AudioWaveform className="h-3.5 w-3.5 text-white" />
                  </span>
                  <div className="leading-tight">
                    <p className="text-xs font-semibold text-white">Transcribing live</p>
                    <p className="text-[10px] text-slate-300">Yorùbá · auto-detected</p>
                  </div>
                </div>
                <div className="flex items-center gap-1.5 rounded-xl bg-black/55 px-3 py-2.5 backdrop-blur-md">
                  <Sparkles className="h-3.5 w-3.5 text-amber-300" />
                  <span className="text-xs font-semibold text-white">Tone-perfect</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ─── Features ────────────────────────────────────── */}
      <section id="features" className="relative border-t border-border bg-slate-50 dark:bg-white/[0.03]">
        <div className="mx-auto max-w-6xl px-4 py-20 md:px-6">
          <div className="mb-12 max-w-2xl">
            <p className="mb-2 text-xs font-semibold uppercase tracking-widest text-blue-600 dark:text-blue-400">
              Why Bámi-Sọ̀rọ̀
            </p>
            <h2 className="text-3xl font-extrabold tracking-tight md:text-4xl">
              Everything you need to go from voice to text
            </h2>
          </div>

          <div className="grid gap-6 md:grid-cols-2">
            {features.map(({ icon: Icon, title, body }) => (
              <div key={title} className="rounded-2xl border border-border bg-card p-6 transition-all hover:border-slate-300 dark:hover:border-white/20 hover:shadow-md">
                <div className="mb-4 flex h-11 w-11 items-center justify-center rounded-xl bg-blue-600/10 text-blue-600 dark:text-blue-400">
                  <Icon className="h-5 w-5" />
                </div>
                <h3 className="mb-1.5 text-base font-semibold text-foreground">{title}</h3>
                <p className="text-sm leading-relaxed text-secondary">{body}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ─── How it works ────────────────────────────────── */}
      <section id="how" className="border-t border-border">
        <div className="mx-auto max-w-6xl px-4 py-20 md:px-6">
          <div className="mb-12 max-w-2xl">
            <p className="mb-2 text-xs font-semibold uppercase tracking-widest text-blue-600 dark:text-blue-400">
              How it works
            </p>
            <h2 className="text-3xl font-extrabold tracking-tight md:text-4xl">Three steps. That&apos;s it.</h2>
          </div>

          <div className="grid gap-6 md:grid-cols-3">
            {steps.map(({ icon: Icon, step, title, body }) => (
              <div key={step} className="relative rounded-2xl border border-border bg-card p-6">
                <div className="mb-10 flex items-center justify-between">
                  <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-gradient-to-br from-blue-500 to-indigo-600 text-white shadow-lg shadow-blue-500/20">
                    <Icon className="h-5 w-5" />
                  </div>
                  <span className="text-4xl font-extrabold text-slate-200 dark:text-white/5">{step}</span>
                </div>
                <h3 className="mb-1.5 text-base font-semibold text-foreground">{title}</h3>
                <p className="text-sm leading-relaxed text-secondary">{body}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ─── CTA ─────────────────────────────────────────── */}
      <section id="about" className="border-t border-border bg-gradient-to-br from-blue-600 to-indigo-700">
        <div className="mx-auto max-w-6xl px-4 py-20 text-center md:px-6">
          <h2 className="mx-auto max-w-2xl text-3xl font-extrabold tracking-tight text-white md:text-4xl">
            Don&apos;t let a living language wait on a keyboard.
          </h2>
          <p className="mx-auto mt-4 max-w-xl text-blue-100">
            Create a free account and transcribe your first Yorùbá recording in under a minute.
          </p>
          <Link
            href="/auth"
            className="mt-8 inline-flex items-center gap-2 rounded-xl bg-white px-7 py-3.5 text-sm font-semibold text-blue-700 shadow-lg hover:bg-blue-50 transition-colors"
          >
            Get started free
            <ArrowRight className="h-4 w-4" />
          </Link>
        </div>
      </section>

      {/* ─── Footer ──────────────────────────────────────── */}
      <footer className="border-t border-border bg-background safe-bottom">
        <div className="mx-auto flex max-w-6xl flex-col items-center justify-between gap-4 px-4 py-8 md:flex-row md:px-6">
          <div className="flex items-center gap-2">
            <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-gradient-to-br from-blue-500 to-indigo-600 text-white">
              <AudioWaveform className="h-4 w-4" />
            </div>
            <span className="text-sm font-semibold gradient-text">Bámi-Sọ̀rọ̀</span>
          </div>
          <p className="text-xs text-muted">
            © {new Date().getFullYear()} Ṣẹ̀kẹ̀rẹ̀ Communications. Preserving the beauty of Èdè Yorùbá.
          </p>
          <p className="text-[10px] text-slate-400 dark:text-slate-600">
            Photography: Emmanuel Ikwuegbu · Unsplash
          </p>
        </div>
      </footer>
    </div>
  );
}