/** The BrandGuard mark. The left half takes the surrounding text colour, so it stays visible on dark and light
 *  surfaces; the right half is the logo's fixed grey. Decorative: the wordmark or a link label names it. */
export function BrandMark({ className = "brand-mark" }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 561 731" aria-hidden="true" focusable="false">
      <path fill="currentColor" d="M280 0 0 163v372l280 196V522L141 421V287l139 93z" />
      <path fill="#8f9290" d="m505 136 56 27v374L280 731V522l155-101V313L280 433v-53z" />
    </svg>
  );
}
