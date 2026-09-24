import { Hero } from "@/components/wevnsec/Hero";
import { TrustBar } from "@/components/wevnsec/TrustBar";
import { Marquee } from "@/components/wevnsec/Marquee";
import { HowItWorks } from "@/components/wevnsec/HowItWorks";
import { WhatWeCheck } from "@/components/wevnsec/WhatWeCheck";
import { Verification } from "@/components/wevnsec/Verification";
import { DocsPreview } from "@/components/wevnsec/DocsPreview";
import { Pricing } from "@/components/wevnsec/Pricing";
import { Faq } from "@/components/wevnsec/Faq";
import { FinalCta } from "@/components/wevnsec/FinalCta";

export default function Landing() {
    return (
        <main>
            <Hero />
            <TrustBar />
            <Marquee />
            <HowItWorks />
            <WhatWeCheck />
            <Verification />
            <DocsPreview />
            <Pricing />
            <Faq />
            <FinalCta />
        </main>
    );
}
