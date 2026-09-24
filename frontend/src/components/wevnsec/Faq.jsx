import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion";
import { Reveal, SectionHeading } from "./Reveal";
import { FAQS } from "./data";

export const Faq = () => (
    <section data-testid="faq-section" className="py-24 sm:py-32 border-t border-border bg-card/30">
        <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
            <SectionHeading
                align="center"
                eyebrow="// faq"
                title="Questions engineers actually ask"
            />
            <Reveal delay={0.15}>
                <Accordion type="single" collapsible className="mt-12">
                    {FAQS.map((f, i) => (
                        <AccordionItem
                            key={f.q}
                            value={`item-${i}`}
                            data-testid={`faq-item-${i}`}
                            className="border-border"
                        >
                            <AccordionTrigger className="text-left text-[15px] font-medium text-foreground hover:text-brand hover:no-underline py-5">
                                {f.q}
                            </AccordionTrigger>
                            <AccordionContent className="text-sm leading-relaxed text-muted-foreground">
                                {f.a}
                            </AccordionContent>
                        </AccordionItem>
                    ))}
                </Accordion>
            </Reveal>
        </div>
    </section>
);
